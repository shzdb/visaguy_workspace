---
id: TASK-027
feature: FEAT-001
title: Operations set the tracking status from the Process File
status: blocked
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-010
created: 2026-09-14
updated: 2026-09-14
---

# TASK-027: Operations set the tracking status from the Process File

## Blocker

**Exact role names.** The owner named "operation team lead" and
"operation consultant". On `visaguy` (2026-09-14):

| Role | Users |
|---|---|
| `Operations Team Lead` | 19 (already has write on `PF Process File`) |
| `Operation Team Lead` | 0 |
| `Operations Associate` | 57 (already has write on `PF Process File`) |
| `Operation Consultant` / `Operations Consultant` | does not exist |

Confirm the two roles (likely `Operations Team Lead` and
`Operations Associate`), or create a consultant role.

## Objective

Let operations change a case's tracking status on its `PF Process File`
(ADR-010 "Amendment (2026-09-14)").

## Required behaviour

1. `custom_fields.json`, `PF Process File-custom_client_status`:
   `read_only: 0`, `permlevel: 1`,
   `fetch_from: custom_visa_tracking_application.current_status`,
   `fetch_if_empty: 1`; keep `depends_on`.
2. Permlevel-1 read for current PF readers and write for the two confirmed
   roles only (Custom DocPerm fixture, filtered to these rows — never a
   bare fixture sweep, risk 25).
3. Desk client script: `set_query` on the field → active statuses, in
   `sort_order`.
4. `PF Process File` `validate`: when the field changed and is set, reject an
   inactive/unknown status with a visible message.
5. `sync_process_file_client_status`: log with `visible_to_client=False`
   and `changed_by = session user`. No reason field.
6. Allowed on dependant Process Files.
7. Unchanged: the next genuine `workflow_state` / `custom_form_submitted`
   change recomputes and overwrites (ADR-010).

## Validation

- A confirmed role changes the status → application updated, exactly one
  log row, `visible_to_client = 0`, absent from the public timeline.
- Another role cannot change it (permlevel).
- Inactive status rejected before save.
- `fetch_if_empty` fills an empty field on save and never overwrites a set
  one; an unrelated save keeps the manual value.
- The next workflow change recomputes it.
- Check the field exists on the target site before migrate (risk 25).
