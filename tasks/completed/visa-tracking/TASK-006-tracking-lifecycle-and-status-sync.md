---
id: TASK-006
feature: FEAT-001
title: Lead, Customer, and Process File tracking lifecycle and status synchronisation
status: completed
repository: the_visaguy
owners: []
depends_on:
  - TASK-005
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Lead, Customer, and Process File tracking lifecycle and status synchronisation

## Objective

Create and maintain a `Visa Tracking Application` across the case lifecycle, from Lead through Process File, keeping exactly one canonical status and one immutable log.

## Required behaviour

- Link a verified `Passport Extraction` to `Lead` and `Customer` and create the tracking application while the case is still a Lead.
- Set the initial status from `Visa Tracker Settings`, not from a hardcoded label.
- When a `PF Process File` is created or linked, populate its tracking Link and apply the configured created-status.
- Let operations update Client Status on `PF Process File` as the normal daily input.
- Allow exceptional direct corrections from `Visa Tracking Application`, synchronising the linked Process File without recursion.
- Create exactly one log entry per effective status change; saving the same status again must not duplicate a log row.
- Only a verified extraction may be linked as the preferred `Lead`/`Customer` passport.
- Provide a reconciliation path for missed FileFlo events and mismatched statuses.

## Constraints

All status writes must route through a single service to prevent recursion and duplicate logs.

## Validation

Status changes from both directions converge; repeated saves produce no duplicate log rows; reconciliation repairs a deliberately skipped event.

## Definition of done

Two-way status synchronisation is correct, non-recursive, and audited.

## Implementation evidence

`tvgglobal/the_visaguy`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `9222302` | 2026-07-21 | feat: add visa tracking lifecycle sync |
| `4593a84` | 2026-07-22 | fix(visa-tracking): repair test isolation, friendly status uniqueness, stale skips |
| `ccbd632` | 2026-07-22 | fix(visa-tracking): repair settings loader Single guard and enqueue job-id race |
| `910914e` | 2026-07-22 | fix(visa-tracking): brace autoname formats and repair timeline NameError |
| `8254f93` | 2026-08-06 | feat: auto verify extraction |

Modules: `visa_tracking/services/lifecycle_service.py`, `services/status_service.py`, `services/reconciliation_service.py`, `services/audit_service.py`, `handlers/lead_handlers.py`, `handlers/process_file_handlers.py`, `handlers/passport_extraction_handlers.py`, `utils/provenance.py` (120 lines).

`doc_events` wiring added in `the_visaguy/hooks.py`:

- `PF Process File.on_update` → `visa_tracking.handlers.process_file_handlers.on_update` (appended alongside the existing WhatsApp handler, which was converted from a string to a list)
- `Customer.on_update` and `Customer.after_insert` → `visa_tracking.handlers.lead_handlers.on_customer_save`
- `Passport Extraction.on_update` → `visa_tracking.handlers.passport_extraction_handlers.on_update`

Tests: `test_lifecycle_service.py`, `test_status_service.py`, `test_reconciliation_service.py`, `test_audit_service.py`.

## Deviations from plan

`8254f93` ("auto verify extraction") introduces automatic verification of extractions. The feature document excluded "automatic use of unverified extraction data" and required that only a *verified* extraction be linked. Auto-verification satisfies that rule only if the promotion criteria are strict. **This must be reviewed during TASK-010** and the criteria recorded in ADR-005.
