# 09d — TASK-005 Corrective: DocType Placement (Defect A) and Fixture Keys (Defect B)

Date: 2026-07-22. Executor phase per `prompts/09d-task-005-corrective.txt`.
Repository: `the_visaguy`, worktree `/home/shahzad/visa-tracker-worktrees/the_visaguy`, branch `feat/visa-tracker`.
Site: `visa-tracker-test.localhost` (dedicated) only. `visaguy`, original checkouts, `processflo` untouched. No push.

## 1. Root cause restatement (from `11-task-010-evidence.md` §4.6, re-verified)

- **Defect A**: the five tracking DocType folders sat at `the_visaguy/the_visaguy/doctype/` (package top level) while `modules.txt` lists module `The Visa Guy` → folder `the_visaguy/the_visaguy/the_visa_guy/` with no `doctype/` subfolder. Frappe `sync_for` only scans module folders, so zero `Visa Track%` DocTypes synced. Verified pre-fix: all five JSONs declare `"module": "The Visa Guy"`.
- **Defect B**: all 6 records in `the_visaguy/fixtures/visa_tracking_status.json` lacked `name`/`modified`; `frappe/modules/import_file.py` reads `doc["name"]` unconditionally → `KeyError: 'name'` abort.

## 2. Changes (worktree HEAD before: `d20cc6d`, clean — verified)

### Commit `9f2393e60ef17ac1f8bf0e2569573382c8e046a8` (Defect A + B)

- Created `the_visaguy/the_visa_guy/doctype/__init__.py` (empty, matching `utility/doctype/__init__.py` convention).
- `git mv` of all five folders — `visa_tracker_audit_log`, `visa_tracker_settings`, `visa_tracking_application`, `visa_tracking_status`, `visa_tracking_status_log` — from `the_visaguy/doctype/` into `the_visaguy/the_visa_guy/doctype/`. Full contents preserved (`__init__.py`, controllers, `.json`, test files); old top-level `doctype/` removed; stale `__pycache__` under the moved tree deleted. 21 files, renames only.
- Reference sweep: repo-wide grep for `the_visaguy.doctype` (all file types, excluding `.git`/`__pycache__`) → **zero** matches before and after; imports reference `the_visaguy.visa_tracking.*` (unmoved). `hooks.py`/`patches.txt` carry no old-path references. Package importability verified: `the_visaguy.the_visa_guy.doctype.<name>.<name>` resolves to the new paths with worktree-first `PYTHONPATH`; all moved `.py` files pass `py_compile`.
- Fixture: added `"name"` (equal to `status_code`, matching DocType `autoname: field:status_code`) and `"modified": "2026-07-21 11:00:00.000000"` (same static timestamp format as the app's `roles.json`) to all 6 records. Diff contains **only** these two added keys per record; no business values changed.

### Commit `28e58c0420a21dff34f0b8a3763bacb43ec4f9d8` (Defect A sweep completion — found during verification)

Two test modules built **filesystem** paths to the old location (invisible to dotted-path greps):
- `the_visaguy/visa_tracking/tests/test_audit_service.py:154-160` → inserted `"the_visa_guy"` path segment.
- `the_visaguy/visa_tracking/tests/test_public_api.py:535` → `load_json("the_visa_guy", "doctype", ...)`.

These were the cause of 4 errors in the first post-fix suite run; fixed and re-verified.

## 3. Migration evidence (dedicated site, worktree-first PYTHONPATH)

`bench --site visa-tracker-test.localhost migrate` → **rc=0** (log `/tmp/vt_migrate_09d.log`). Read-only SQL after migration (**runtime-verified**):

- `tabDocType`: `Visa Tracker Audit Log`, `Visa Tracker Settings`, `Visa Tracking Application`, `Visa Tracking Status`, `Visa Tracking Status Log` — all module `The Visa Guy`. Tables exist for the four non-Single DocTypes (Settings is Single, no table — expected).
- `` `tabVisa Tracking Status` ``: exactly the 6 seed records, `name = status_code`, all `active=1`, sequences 10–60.
- `tabCustom Field`: 8 rows, no duplicates — `custom_passport_extraction` + `custom_visa_tracking_application` on `Lead`, `CRM Lead`, `Customer`; `custom_visa_tracking_application` + `custom_client_status` on `PF Process File`. The 8 pre-persisted fields converged idempotently.
- `tabCustom DocPerm`: 8 rows, no duplicates — `Visa Tracker Manager` + `Visa Tracker Operator` on each of the 4 perm-managed DocTypes. Converged idempotently.
- Zero `Guest` rows in `tabCustom DocPerm` for any `Visa Track%`/`Visa Tracker%`/`Passport Extraction%` parent.

## 4. Test results

| Suite | Result | Label |
|---|---|---|
| `run-tests --app the_visaguy` (plain) | Aborts before tests in Frappe's global test-record bootstrap: ERPNext `Company` test record → `create_default_warehouses` → `LinkValidationError: Could not find Warehouse Type: Transit` (standard ERPNext master data absent on the minimal dedicated site). Environmental, pre-existing, unrelated to the_visaguy code. Log `/tmp/vt_tests_the_visaguy_09d.log` | runtime-verified (execution) |
| `run-tests --app the_visaguy --skip-test-records` | **216 ran, 201 pass, 12 skipped, 3 errors** (rc=0; verbose log `/tmp/vt_tests_tvg_09d_v2.log`). The 4 previously site-bound tracking DocType test modules now execute from `the_visaguy.the_visa_guy.doctype.*`. Remaining 3 errors are pre-existing genuine defects surfaced for the first time (§5) | runtime-verified |
| `run-tests --app fileflo` (plain) | **6 ran, 6 pass, 0 errors — OK** (rc=0; `/tmp/vt_tests_fileflo_09d.log`) | runtime-verified |
| Pure standalone (`visa_tracking/tests`, no site) | **199 ran, 197 pass, 10 skipped, 2 errors** — back to the exact recorded baseline; the 2 errors are the pre-existing site-bound `TestLookupService`/`TestSettings` classes (`IncorrectSitePath: test_site`) | runtime-verified (execution) |

## 5. Further genuine defects surfaced (reported, NOT fixed per contract §4)

1. **`test_visa_tracking_status.py::test_unique_status_code_and_sequence`** expects `frappe.ValidationError` on duplicate `status_code`/`sequence` inserts, but `frappe.exceptions.DuplicateEntryError` (subclass of `NameError`, **not** `ValidationError`) is raised — duplicate code collides on the primary key (`autoname: field:status_code`) and duplicate sequence on the `unique: 1` column before any friendly validation. The controller has no explicit duplicate check. This test never executed anywhere before (site-bound under Defect A; not in the pure-tier path).
2. **Test isolation defect (TASK-004 code)**: `visa_tracking/tests/test_fileflo_inspection.py:364-368` — `TestProvenanceResolution.setUp` binds a `MagicMock` to `frappe.local.db` and `tearDown` does `del frappe.local.db`, destroying the **real** connection for the rest of the process. Every `FrappeTestCase` integration class except two self-skips (`skipTest("Deferred to TASK-010: no dedicated test site available")`, now a stale reason) before touching `frappe.local.db`; the unguarded `TestLookupService` and `TestSettings` then error at `FrappeTestCase.setUpClass` (`AttributeError: db`). Both modules **pass in isolation** on-site (`--app the_visaguy --module ...`: 8/8 OK and 2/2 OK), proving the classes and migrated schema are sound.

## 6. Notes for the TASK-010 resume

- 12 on-site skips are the integration classes self-skipping with the stale "no dedicated test site available" reason; a dedicated site now exists — re-enabling them is a follow-up decision, not made here.
- Plain `run-tests` (without `--skip-test-records`) needs the ERPNext test-record bootstrap (`Warehouse Type: Transit` etc.) or continued use of `--skip-test-records` (the_visaguy tests build their own synthetic fixtures).
- `run-tests --module ...` **without** `--app` pulls in ERPNext's `before_tests` hook, which crashes on this site (`country=None` in `install_fixtures.py`). Always scope with `--app`.

## 7. State

- Worktree clean at `28e58c0420a21dff34f0b8a3763bacb43ec4f9d8` (`9f2393e` → `28e58c0` on top of `d20cc6d`). No push, environment-default Git identity.
- No task files moved. Synthetic data only. `visaguy` not migrated or tested.

## 8. Verdicts

- Defect A: **fixed and runtime-verified** (DocTypes discovered, tables synced, test modules execute from the new path).
- Defect B: **fixed and runtime-verified** (fixture import no longer aborts; 6 records present, active, correctly named).
- Migrate: **rc=0**, idempotent convergence of pre-persisted custom fields/docperms confirmed.
- On-site suites: the_visaguy 216 ran / 201 pass / 12 skipped / 3 errors (all 3 pre-existing genuine defects, §5); fileflo 6/6 OK.
