# Phase 3 — Integration (2026-09-28)

Done by the orchestrator directly (the owner chose this over an unsupervised executor). Test site only; nothing run on `visaguy`.

## Merges (bench installed checkouts, branch `feat/visa-tracker`, not pushed)

| Repo | Merge | SHA |
|---|---|---|
| the_visaguy | sl/task-036 | `6f1db0d` |
| the_visaguy | sl/task-031 | `e775273` (auto-merge in `visa_tracking/jobs.py`, both functions kept) |
| the_visaguy | sl/task-034 | `5790c7f` |
| the_visaguy | sl/task-032 | `021f636` (HEAD) |
| passport_extractor | sl/task-033 | `fa97752` |
| passport_extractor | fix commit | `84da2fe` (HEAD) |

Gates: `py_compile` on all changed Python, JSON validation of all changed JSON, no conflict markers.

## Fix during integration

`84da2fe fix(TASK-033)`: the new review-action tests patched `frappe.local.flags` with `mock.patch.object(..., create=True)`. On a werkzeug `Local` the attribute is not in `__dict__`, so mock deleted it on exit, and `bench run-tests` crashed after the suite ("RuntimeError: object is not bound", exit 1, all tests OK). The test now saves and restores the flags by hand.

## Results (visa-tracker-test.localhost)

| Check | Result |
|---|---|
| the_visaguy pure tier | Ran 477, FAILED (errors=2, skipped=20): only the 2 known TestProcessFileHandler site-context errors |
| Backup | `20260928_080800-visa-tracker-test_localhost-database.sql.gz` |
| Migrate | rc 0. Patch `set_passport_field_id` executed: FF Field ID `passport` created; 0 template and 0 collection rows (no FileFlo data on the test site). Pre-existing notice: fixture `custom_field.json` skipped because DocType GoCardless Mandate is missing. |
| the_visaguy on-site (`--skip-test-records`) | Ran 578, OK (was 418 on 2026-09-14) |
| passport_extractor on-site | Plain run aborts in Frappe's test-record bootstrap (`DocType Company Print Options not found`, environmental, as in earlier phases). With `--skip-test-records`: Ran 98, OK, rc 0 after `84da2fe` |
| Patch second run | updates 0 |

## Static on-site checks

- PF Process File order: `custom_form_submitted`, `custom_visa_tracking_section`, `custom_visa_tracking_application`, `custom_client_status`, `custom_tracking_empty_note`, `custom_tracking_column_break`, `custom_tracking_updated_on`, `custom_tracking_enabled`, `custom_section_break_mw0ux`. field_order Property Setter present; after_migrate hook idempotent.
- Custom DocPerm: Application / Status / Status Log 19 rows each (Ops read; Ops create on Application; System Manager full). Passport Extraction 5 rows (Ops read+write level 0; standard rows kept). Settings 3 rows incl. System Manager.
- Visa Tracking Application: title_field `applicant_display_name`, show in link, sections Applicant / Current Status / Timeline / References / Secure Lookup, link to Status Log, list/filter/search per TASK-032.
- Workspace "Visa Tracking" with 4 shortcuts. Hidden Property Setters on Lead, CRM Lead, Customer. Applicant row link in list view. Client Scripts `PF Process File-visa-tracking-actions` and `-client` enabled. Passport Extraction list/search flags present.

## Not verified here

- End-to-end flow with real passport files (owner tests on `visaguy`).
- Desk UI in a browser (buttons, dialogs, previews).
- `visaguy` migrate and patch counts (owner).
