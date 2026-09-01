---
id: TASK-013
feature: FEAT-001
title: Consolidate the duplicated FileFlo upload logic
status: blocked
repository: visaguy_crm
owners: []
depends_on:
  - ADR-003
  - ADR-006
blocked_by: owner decision on approach; deliberately deferred 2026-07-23
created: 2026-07-23
updated: 2026-07-23
---

# TASK-013: Consolidate the duplicated FileFlo upload logic

## Blocker

Deferred by owner decision during the 2026-07-23 session in favour of the
lower-risk patch that unblocked testing. Refactoring a live CRM path needs an
explicit go-ahead and an agreed approach. Recorded as risk 21.

## Problem

`visaguy_crm.data_collecting_form.add_form_data` is a **fork** of
`fileflo.data_collection.add_form_data`. The live data-collection form calls the
CRM copy; the fileflo original is not on the request path at all.

The fork has already drifted, and the drift caused two production-visible
defects that had to be fixed **twice, independently**:

- `field_id` dropped for multi-upload fields — fixed in `fileflo` (`c7244a4`)
  and again in `visaguy_crm` (`b573e2c`);
- the FileFlo post-persistence extension event was never dispatched by the CRM
  copy at all.

`fileflo` had additionally refactored its child-table save into
`save_table_data()` while the fork retained the older inline form — the two
implementations are visibly diverging, not merely duplicated.

Until consolidated, **any change to one must be evaluated against the other.**
This is the single most likely source of a future silent regression in this
feature.

## Options

1. **Delegate.** Make the CRM endpoint call fileflo's implementation, passing
   its extras through. Removes the duplication permanently. Highest risk: the
   fork carries genuine CRM-specific behaviour — `custom_customer`,
   `custom_applicant_name`, `form_submitted` handling, upload-capacity
   re-creation, and its own `existing_count` numbering across submissions.
2. **Extract a shared core** in `fileflo` covering row creation and event
   dispatch, with both endpoints as thin callers. Lower risk than (1), keeps CRM
   concerns where they belong, still removes the drift surface.
3. **Keep both, add a contract test** asserting `field_id` survives and the
   extension event fires in *both* implementations. Cheapest; does not remove the
   drift, only detects it.

Option 2 is the suggested default. Option 3 is a reasonable interim step and is
worth doing regardless of which is ultimately chosen.

## Constraints

- Dependency direction is fixed by ADR-003: `visaguy_crm` may depend on
  `fileflo`, never the reverse.
- The live form must keep working throughout; this path is how every data
  collection form on the bench is submitted, not only visa tracking.
- Any refactor needs the multi-upload `field_id` round-trip test present on both
  sides *before* the change, so the refactor is guarded rather than trusted.

## Validation

- `fileflo` suite (baseline 8) and any `visaguy_crm` suite green.
- A real form submission on the bench still produces an
  `FF File Collection File` row carrying `field_id`, and still dispatches the
  extension event.
- Both single-upload (`multiple = 0`) and multi-upload (`multiple = 1`) fields
  covered — the original defect affected only the latter, and the suite's
  blindness to it is what let it ship.
