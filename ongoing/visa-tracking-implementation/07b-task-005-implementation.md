# TASK-005 Implementation Evidence

> Generated: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-005 — Tracking data model and settings
> Repository: `the_visaguy`
> Worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`
> Branch: `feat/visa-tracker`
> Commit: `f7ad8c0518a6442cbb33136b84dba524f2909ecd`
> Commit message: `feat: add visa tracking data model and settings`

## Summary

Implemented the complete TASK-005 static package for the visa tracking domain in the `the_visaguy` feature worktree:

- Four new DocTypes: `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`.
- Controllers with validation per `01-architecture-and-data-model.md`.
- Initial `Visa Tracking Status` fixture records (six statuses).
- Role and Custom DocPerm fixtures for `Visa Tracker Manager`, `Visa Tracker Operator`, and `System Manager`; no Guest access.
- Custom field fixtures for `Lead`, `Customer`, `CRM Lead`, and `PF Process File`.
- Client script fixture for `PF Process File` to toggle `custom_client_status`.
- Module subpackage `the_visaguy/visa_tracking/` with constants, cached settings loader, HMAC lookup-hash seam, and status-log service seam.
- Synthetic tests for validation, permissions, and service seams.

No migration or test was run on site `visaguy`. `processflo` was not modified. No push was performed.

## Changed files

| Path | Purpose |
|------|---------|
| `the_visaguy/hooks.py` | Register new fixtures: `Custom Field`, `Property Setter`, `Client Script`, `Role`, `Custom DocPerm`, `Visa Tracking Status`. |
| `the_visaguy/doctype/visa_tracker_settings/__init__.py` | Module marker. |
| `the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.json` | Single DocType schema. |
| `the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.py` | Controller validation. |
| `the_visaguy/doctype/visa_tracker_settings/test_visa_tracker_settings.py` | Synthetic validation tests. |
| `the_visaguy/doctype/visa_tracking_status/__init__.py` | Module marker. |
| `the_visaguy/doctype/visa_tracking_status/visa_tracking_status.json` | Status master-data schema. |
| `the_visaguy/doctype/visa_tracking_status/visa_tracking_status.py` | Controller + helper functions. |
| `the_visaguy/doctype/visa_tracking_status/test_visa_tracking_status.py` | Synthetic status/normalization tests. |
| `the_visaguy/doctype/visa_tracking_application/__init__.py` | Module marker. |
| `the_visaguy/doctype/visa_tracking_application/visa_tracking_application.json` | Case record schema. |
| `the_visaguy/doctype/visa_tracking_application/visa_tracking_application.py` | Controller validation. |
| `the_visaguy/doctype/visa_tracking_application/test_visa_tracking_application.py` | Synthetic tracking-enable tests. |
| `the_visaguy/doctype/visa_tracking_status_log/__init__.py` | Module marker. |
| `the_visaguy/doctype/visa_tracking_status_log/visa_tracking_status_log.json` | Audit log schema. |
| `the_visaguy/doctype/visa_tracking_status_log/visa_tracking_status_log.py` | Controller validation. |
| `the_visaguy/doctype/visa_tracking_status_log/test_visa_tracking_status_log.py` | Synthetic service/log tests. |
| `the_visaguy/fixtures/visa_tracking_status.json` | Six initial status records. |
| `the_visaguy/fixtures/custom_fields.json` | Custom fields on `Lead`, `Customer`, `CRM Lead`, `PF Process File`. |
| `the_visaguy/fixtures/property_setters.json` | Empty placeholder. |
| `the_visaguy/fixtures/client_scripts.json` | `PF Process File` client script. |
| `the_visaguy/fixtures/roles.json` | `Visa Tracker Manager`, `Visa Tracker Operator`. |
| `the_visaguy/fixtures/custom_docperm.json` | Explicit permissions by role/DocType. |
| `the_visaguy/visa_tracking/__init__.py` | Module marker. |
| `the_visaguy/visa_tracking/utils/__init__.py` | Module marker. |
| `the_visaguy/visa_tracking/utils/constants.py` | Bounds and stable status codes. |
| `the_visaguy/visa_tracking/utils/settings.py` | Cached loader and predicate helpers. |
| `the_visaguy/visa_tracking/services/__init__.py` | Module marker. |
| `the_visaguy/visa_tracking/services/lookup_service.py` | HMAC lookup-hash seam. |
| `the_visaguy/visa_tracking/services/status_service.py` | Status-log seam and public timeline helper. |
| `the_visaguy/visa_tracking/tests/__init__.py` | Module marker. |
| `the_visaguy/visa_tracking/tests/test_lookup_service.py` | HMAC seam tests. |
| `the_visaguy/visa_tracking/tests/test_settings.py` | Settings loader/predicate tests. |

## Static gates

| Gate | Result |
|------|--------|
| DocType JSON valid JSON | Pass — all four schemas parse. |
| Fixture JSON valid JSON | Pass — all fixture files parse. |
| Schema field assertions | Pass — every required field from TASK-005 is present. |
| `Visa Tracker Settings` is Single | Pass. |
| Fixture duplicate checks | Pass — no duplicate names/codes/sequences/roles. |
| Python compile (`py_compile`) | Pass — all controllers, services, tests, and `hooks.py` compile. |
| Hook fixture registration | Pass — all fixture files registered in `hooks.py`. |
| No Guest permissions | Pass — no Guest role in DocType schemas or `custom_docperm.json`. |
| No forbidden imports | Pass — no imports from `fileflo`, `processflo`, or `passport_extractor` internals. |
| No secret values committed | Pass — HMAC key name only; no value in source. |
| No PII / passport samples | Pass — synthetic test data only. |
| No `processflo` edits | Pass — `processflo` worktree still dirty only with pre-existing unrelated file. |
| `git diff --check` | Pass — no whitespace errors. |
| `git status --short` after commit | Clean. |

## Runtime gates

Deferred to TASK-010 / dedicated test site:

- `bench --site <test-site> migrate` with new DocTypes and fixtures.
- Initial `Visa Tracking Status` records exist and are active after migrate.
- Custom fields appear on `Lead`, `Customer`, `CRM Lead`, and `PF Process File`.
- Synthetic tests pass in a Frappe test runner.
- No migration or test run on site `visaguy`.

## Notes

- The HMAC key is referenced only by configuration key name (`visa_tracker_lookup_hmac_key`) in `constants.py` and `settings.py`; the value is read from `frappe.conf` at runtime.
- CRM Lead custom fields are included because TASK-001 source evidence confirmed both ERPNext `Lead` and Frappe `CRM Lead` are wired into the deployed flow.
- `PF Process File` custom fields are shipped as `the_visaguy` fixtures per ADR-003; no source change was made in `processflo`.
