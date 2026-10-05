# TASK-039 Parts A and B (server side) - log

## Summary
Part A done. Part B items 2, 3, 4, 5 done. Part B item 1 (DocType fields) and Part C belong to the other agent.
Branch `sl/task-039` (base b372f73), pushed to remote `bench`.

## Commits
- e6632e6 feat(TASK-039): drop the Lead passport link, set passport number and DOB on the application (no attribution trailer; verified)

## Files changed (the_visaguy/the_visaguy/)
- visa_tracking/services/lifecycle_service.py
- visa_tracking/handlers/lead_handlers.py
- visa_tracking/handlers/passport_extraction_handlers.py
- fixtures/custom_fields.json (two Lead/CRM Lead fields removed; two tracking link fields re-anchored on `status`)
- fixtures/custom_docperm.json (4 new permlevel 1 read rows)
- the_visa_guy/doctype/visa_tracker_settings/visa_tracker_settings.json (description only)
- patches/v1_0/remove_lead_passport_extraction_field.py (new)
- patches/v1_0/backfill_application_passport_number_and_dob.py (new)
- patches.txt (two lines appended to [post_model_sync])
- visa_tracking/tests/test_lifecycle_service.py, visa_tracking/tests/test_task_039_lead_link_removal.py (new)

## Design notes and deviations
- Removed `link_verified_extraction_to_lead`, `_link_lead_extraction` and the call in `handle_verified_extraction`.
- New `_link_customer_extraction`: gated by `auto_link_verified_passport`; looks up the Customer with `lead_name == lead` and calls the existing `link_verified_extraction_to_customer`. Runs on create and on reuse. No Customer yet is a no-op. CRM Lead names never match `Customer.lead_name`, so CRM Leads get the Customer link only through a later path (none exists today); same as before, since the old handler only read `Lead`.
- `lead_handlers.sync_customer_tracking_links` no longer reads the Lead field: the extraction comes from the Lead's newest application (`passport_extraction`), still only if Verified. This path is not gated by `auto_link_verified_passport`, as before.
- Create sets `app.passport_number` / `app.date_of_birth` from `pex.passport_number_normalized` / `pex.date_of_birth`. Reuse writes them via `db.set_value(update_modified=False)` only when they differ and the source is non-empty. Reuse does not change `app.passport_extraction` (existing behaviour), so "when passport_extraction changes" is implemented as "when the values differ".
- Custom DocPerm rows are named `<Role>-Visa Tracking Application-1`, copied from the existing `...-Passport Extraction-1` row format, read only. Existing permlevel 0 rows are untouched.
- Delete patch uses `frappe.delete_doc(..., ignore_missing=True, force=True)` after an exists check.
- Backfill patch is one joined UPDATE, skipped unless both columns exist, does not touch `modified`.
- Tests: `VERIFIED_PEX` gained `passport_number_normalized: X1234567`.
- test_ensure_service.py still mocks a Lead doc with `custom_passport_extraction`; harmless, not changed.

## Tests and pure tier
Added: test_lifecycle_service (TestCreateTrackingApplication: lead never written, customer link gated, reuse links customer and fills fields, unchanged fields not rewritten; TestLinkVerifiedExtraction: lead helpers removed; TestCustomerHandler: no applications noop); test_task_039_lead_link_removal (fixtures, delete patch, backfill patch). Updated existing create, handler and customer-handler tests.
Pure tier on bench worktree task-039-the_visaguy: `Ran 629 tests`, FAILED (errors=2, skipped=20): only the 2 known TestProcessFileHandler `AttributeError: site` errors (baseline 618).
py_compile and JSON validity: OK.

## On-site checks for the orchestrator
1. After the other agent's fields are merged: `bench migrate` on visa-tracker-test.localhost. Patch order matters little; the backfill is a no-op if the columns are not yet synced and runs again harmlessly only if re-queued (patches run once), so confirm migrate syncs the DocType BEFORE post_model_sync patches (it does) and that counts are filled.
2. Lead and CRM Lead no longer have `custom_passport_extraction`; the tracking link field still shows after `status`.
3. Smoke chain: verify an extraction for a Lead that has a Customer; Customer gets `custom_passport_extraction`; application has `passport_number` and `date_of_birth`; Lead is not saved (modified unchanged).
4. Operations Associate sees the two fields; a Lead Role user does not.
5. Existing applications have the fields filled; `modified` unchanged.
6. Integration test `test_same_passport_gets_one_application_per_lead_applicant` now asserts the Lead has no extraction link; run the on-site suite.
7. Frappe does not always apply new Custom DocPerm rows when a fixture row has the same role and permlevel as nothing existing; confirm the four permlevel 1 rows exist in Role Permission Manager.

## Open questions
- CRM Lead: should the Customer link also work for CRM Lead sources? No Customer back-reference exists for CRM Lead today.
