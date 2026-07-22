# 09e — TASK-005/007 Corrective: Test Isolation, Status Uniqueness Validation, Stale-Skip Re-enablement

Date: 2026-07-22. Executor phase per `prompts/09e-task-005-007-corrective.txt`.
Repository: `the_visaguy`, worktree `/home/shahzad/visa-tracker-worktrees/the_visaguy`, branch `feat/visa-tracker`.
Site: `visa-tracker-test.localhost` (dedicated) only. `visaguy`, original checkouts, `processflo` untouched. No push.

## 1. Ground facts verified

- Worktree HEAD `28e58c0420a21dff34f0b8a3763bacb43ec4f9d8`, branch `feat/visa-tracker`, clean before edits (**runtime-verified**).
- One commit produced: **`4593a845f336763a4afdce2d155bb96471c6b198`**, environment-default Git identity, no `--author`, no push. Worktree clean after commit. 13 files changed, 138 insertions, 74 deletions.

## 2. Defect 1 — `frappe.local.db` teardown destroying the real connection (fixed)

- `the_visaguy/visa_tracking/tests/test_fileflo_inspection.py` `TestProvenanceResolution`: `setUp` now saves any existing `frappe.local.db` (`_had_real_db`/`_real_db`) before binding the `MagicMock`; `tearDown` restores the saved connection when one existed, and only `del`s the attribute in the no-site case (preserving standalone-tier hygiene).
- Sweep: repo-wide grep for `del frappe.local` and `frappe.local.db` writes across `the_visaguy/` (excluding `__pycache__`) — this was the **only** occurrence; no other file needed the fix (**source-wired**).
- Result: the 2 downstream `AttributeError: db` errors (`TestLookupService`, `TestSettings` at `FrappeTestCase.setUpClass`) are gone; all 5 methods in those classes now pass on-site (**runtime-verified**).

## 3. Defect 2 — friendly duplicate validation for `Visa Tracking Status` (fixed)

- Root cause (more precise than 09d's statement): the controller *did* have duplicate checks in `validate()`, but with `autoname: field:status_code` Frappe assigns `name = status_code` in `set_new_name` **before** `validate()` runs, so the `{"name": ("!=", self.name)}` filter excluded exactly the colliding row. The friendly check passed vacuously and the primary-key insert then raised raw `DuplicateEntryError` (a `NameError`, not `frappe.ValidationError`).
- Fix in `the_visaguy/the_visa_guy/doctype/visa_tracking_status/visa_tracking_status.py::_validate_status_code`: query by `status_code` only, and throw `frappe.ValidationError` when a row exists and (`self.is_new()` or it is a different document). Sequence check unchanged (name is never derived from `sequence`, so the existing self-exclusion is correct there). No schema change, no test-assertion change. Messages contain status codes/record names only — PII-free.
- Result: `test_unique_status_code_and_sequence` ... **ok** on-site (**runtime-verified**).

## 4. Defect 3 — stale "no dedicated test site available" skips (removed; key finding)

- **Key finding**: all 12 self-skipping integration classes are *placeholder scaffolding* — every test method body consists solely of `self.skipTest(...)`; no real integration assertions exist to "re-enable" (they are explicitly TASK-010 scope per their own comments). Converting them to empty bodies would have produced ~27 vacuous passes and fake security coverage; that was deliberately **not** done.
- What was done instead, in all 12 classes (10 in `the_visaguy/visa_tracking/tests/`, 2 in `the_visaguy/the_visa_guy/doctype/*/`):
  - Removed the stale class-level `setUpClass` SkipTest guard whose reason ("no dedicated test site available") is now false — the classes execute on-site.
  - Kept each placeholder method skipping individually with the honest reason `"Placeholder: integration test body deferred to TASK-010."` — 27 such skips on-site, each individually justified and listed in the verbose log (`/tmp/vt_tests_tvg_09e_v3.log`).
  - Added a conditional class-level guard `if getattr(frappe.local, "db", None) is None: raise unittest.SkipTest(...)` so the **no-site standalone tier** still skips these `FrappeTestCase` classes instead of erroring. (First attempt used `frappe.local.site`; that is polluted process-wide by `FrappeTestCase`'s failed `init("test_site")`, so `db` presence is the correct signal — caught and fixed during verification.)
  - Class docstrings updated to state the dedicated site exists and bodies remain TASK-010 scope. Unused `import unittest` churn avoided (kept where now used by the guard).
- Newly-unskipped outcomes: zero newly-running test **failed or errored**; no genuine app defect surfaced. The only newly-*passing* tests are the 5 in formerly-erroring `TestLookupService`/`TestSettings` and the formerly-erroring `test_unique_status_code_and_sequence` — all green.

## 5. Verification results (dedicated site, worktree-first PYTHONPATH, `--app`-scoped)

| Suite | Before (09d) | After (09e) | Label |
|---|---|---|---|
| `run-tests --app the_visaguy --skip-test-records` | 216 ran / 201 pass / 12 skipped / **3 errors** | **248 ran / 221 pass / 27 skipped / 0 errors**, rc=0 (`/tmp/vt_tests_tvg_09e_v3.log`) | runtime-verified |
| `run-tests --app fileflo` | 6/6 OK | **6 ran / 6 pass / 0 errors**, rc=0 (`/tmp/vt_tests_fileflo_09e.log`) | runtime-verified |
| `bench migrate` | rc=0 | **rc=0** (`/tmp/vt_migrate_09e.log`) | runtime-verified |
| Pure standalone (`visa_tracking/tests`, no site) | 199 ran / 10 skipped / 2 errors | **199 ran / 10 skipped / 2 errors** — exact baseline (`/tmp/vt_tests_standalone_09e_v3.log`) | runtime-verified (execution) |

- Count reconciliation (09d → 09e on-site): +32 counted tests = 27 placeholder methods (now counted, individually skipped) + 5 methods of the two formerly-erroring classes (now passing); test-ID diff of the verbose logs is purely additive — no previously-running test regressed or vanished.
- The 27 on-site skips are **all** the documented TASK-010 placeholders; the dedicated-site guard fired 0 times on-site (db bound).
- Standalone remainder, honestly reported: the 2 errors are the pre-existing unguarded site-bound classes `TestLookupService`/`TestSettings` (`IncorrectSitePath: test_site`). The prompt's speculation that Defect 1's fix would clear them standalone does not hold — standalone they fail simply because no site exists at all; they are sound on-site (5/5 pass). Left as-is to preserve baseline behavior; adding site guards to those two classes is a trivial follow-up if desired.

## 6. Suite quirks (unchanged, re-confirmed)

- `--skip-test-records` still required (plain run aborts in ERPNext's global test-record bootstrap — environmental, out of scope).
- Always `--app`-scoped; unscoped `--module` pulls ERPNext `before_tests`, which crashes on this site.
- Worktree-first `PYTHONPATH` used for every bench/unittest invocation.

## 7. Remaining issues / follow-ups

- 27 placeholder integration methods remain skipped pending real bodies — **TASK-010 scope**, now honestly labeled and visible per-test.
- 2 standalone errors (`TestLookupService`, `TestSettings`, `IncorrectSitePath`) are pre-existing baseline, not a regression.
- Plain (non-`--skip-test-records`) runs remain environmentally blocked by ERPNext test-record bootstrap (unchanged, out of scope).

## 8. Verdicts

- Defect 1: **fixed and runtime-verified** (db connection saved/restored; downstream `AttributeError: db` errors eliminated; sweep clean).
- Defect 2: **fixed and runtime-verified** (`frappe.ValidationError` on duplicate `status_code`; `test_unique_status_code_and_sequence` passes; schema and test assertions untouched).
- Defect 3: **stale guards removed; classes execute on-site with zero new failures**; the "integration tests" were placeholder scaffolding, so 27 honestly-labeled per-method skips remain (documented, TASK-010 scope) rather than vacuous passes.
- On-site suites: the_visaguy **248/221 pass/27 skip/0 error**; fileflo **6/6**; migrate **rc=0**; standalone baseline preserved.
- Commit: `4593a845f336763a4afdce2d155bb96471c6b198` (single commit, worktree clean).
