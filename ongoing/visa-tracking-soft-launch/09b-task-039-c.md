# TASK-039 Part B item 1 and Part C (branch sl/task-039c)

## Summary
Added `passport_number` (Data) and `date_of_birth` (Date) to the Visa Tracking Application Applicant section (read_only, permlevel 1, fetch_from the extraction, not in list, filter or search). The timeline now fetches `name` and shows an "Open" link per row to the Status Log form.

## Commits
- 6718c89 feat(TASK-039): passport number and DOB fields and per-row status log link on the application (no trailer)

## Files changed
- the_visaguy/the_visa_guy/doctype/visa_tracking_application/visa_tracking_application.json (fields placed after `destination`, before `applicant_column_break`; field_order and modified updated)
- the_visaguy/the_visa_guy/doctype/visa_tracking_application/visa_tracking_application.js (fetch `name`, extra column with Open link via frappe.utils.get_form_link, escaped)
- the_visaguy/visa_tracking/tests/test_desk_layout_fixtures.py (new test for the two fields; form script assertions for name and link)

## Deviations
None. Field position (left column of Applicant section) was my choice; the contract only said Applicant section.

## Tests and pure tier
JSON valid; `node --check` on the JS passed. Pure tier on bench worktree task-039c-the_visaguy: "Ran 619 tests", FAILED (errors=2, skipped=20), the 2 known TestProcessFileHandler errors only (618 baseline + 1 new test).

## On-site checks
- Migrate test site; form shows both fields for Operations Associate, hidden for a Lead Role user (needs the Custom DocPerm rows from the other task).
- Fields populate from the linked extraction (fetch_from) on save.
- Each timeline row has an Open link that opens its Status Log.

## Open questions
- The fetch_from only fires on form change; server-side setting and backfill belong to the other agent's scope.
