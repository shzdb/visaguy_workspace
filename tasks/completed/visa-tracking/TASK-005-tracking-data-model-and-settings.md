---
id: TASK-005
feature: FEAT-001
title: Visa tracking data model, settings, custom fields, and fixtures
status: completed
repository: the_visaguy
owners: []
depends_on:
  - TASK-004
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Visa tracking data model, settings, custom fields, and fixtures

## Objective

Create the tracking data model in `the_visaguy`: a settings Single, a tracking application, a status record type, an immutable status log, and the read-only links on `Lead`, `Customer`, and `PF Process File`.

## Required behaviour

- `Visa Tracker Settings` (Single) controlling at least: Default Lead Status, Process File Created Status, and whether automatic Process File transition is enabled.
- `Visa Tracking Application` whose `current_status` is the canonical current public state.
- `Visa Tracking Status` as records — not hardcoded Select options — each with a stable code, order, default message, active flag, final flag, success flag, and `allow_on_process_file` flag.
- `Visa Tracking Status Log` as the canonical immutable client-visible timeline.
- Read-only tracking links on `Lead`, `Customer`, and `PF Process File`, plus a client-status Link field on `PF Process File`.
- Seed statuses: Application Received, Documents Under Review, Verification in Progress, Working on Your Application, Application Submitted, Update Shared with Client.

## Constraints

No business code may hardcode a status label as a lifecycle decision. `processflo` must not be edited; the `PF Process File` fields are added as custom fields from `the_visaguy`.

## Validation

`bench migrate` applies cleanly; fixtures export and re-import without diff churn; the seed statuses are present.

## Definition of done

The model migrates cleanly and all lifecycle-relevant statuses are configuration, not code.

## Implementation evidence

`tvgglobal/the_visaguy`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `f7ad8c0` | 2026-07-21 | feat: add visa tracking data model and settings |
| `9f2393e` | 2026-07-22 | fix: place visa tracking DocTypes under The Visa Guy module and fix status fixture keys |
| `28e58c0` | 2026-07-22 | fix: update test schema paths for moved visa tracking DocTypes |

DocTypes created under `the_visaguy/the_visa_guy/doctype/`:

- `visa_tracker_settings`
- `visa_tracking_application`
- `visa_tracking_status`
- `visa_tracking_status_log`
- `visa_tracker_audit_log`

Supporting module: `visa_tracking/utils/settings.py` (131 lines, cached settings loader).

`hooks.py` fixtures extended with `Custom Field`, `Property Setter`, `Client Script`, `Role`, `Custom DocPerm`, and `Visa Tracking Status`.

Tests: `visa_tracking/tests/test_settings.py`.

## Deviations from plan

`Visa Tracker Audit Log` is a fifth DocType not enumerated in the feature document's data-model list. It implements the feature's scope item 15 (audit logging) as a first-class record rather than as log lines. This is an addition, not a contradiction, and is recorded in ADR-005.
