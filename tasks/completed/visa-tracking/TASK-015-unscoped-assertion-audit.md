---
id: TASK-015
feature: FEAT-001
title: Audit visa-tracking tests for assertions that depend on global table state
status: completed
repository: the_visaguy
owners: []
depends_on:
  - TASK-011
created: 2026-09-01
updated: 2026-09-14
---

# TASK-015: Audit visa-tracking tests for assertions that depend on global table state

## Objective

Sweep `the_visaguy`'s visa-tracking test suite for assertions that depend on
global/shared table state instead of being scoped to the records the test
itself created, and fix each instance found. One known instance is already
fixed; nobody has audited the rest of the suite for the same pattern.

## Context

During the 2026-09-01 session, three of the suite's five triaged failures
turned out to be test-isolation bugs, not application defects. The test site
(`visa-tracker-test.localhost`) is persistent and does not roll back between
runs. `test_audit_rows_contain_no_pii` was the clearest case: it asserted an
exact count of rows (`== 2`) in `Visa Tracker Audit Log` — a table shared
across the entire suite and every prior run against that site — rather than
scoping its assertion to the audit rows produced by its own activity. The
table held 37 rows by the time the test ran, so the hardcoded `2` failed.

A related failure in the same triage: `tabVisa Tracking Application` still
held `VTA-2026-00041`, created 2026-07-22, because every test in the suite
used the same synthetic identity (`P0000000` / `1990-01-01`) and
`lifecycle_service.create_tracking_application` correctly enforces "one
active application per identity" — so tests collided with each other's
leftover data across runs, not just within a single run.

That specific instance (`test_audit_rows_contain_no_pii` and its neighbors in
the same triage) has been fixed this session: unique synthetic identities per
test, assertions scoped to each test's own records, and cleanup in
`tearDown`. **This task is the follow-up nobody has done yet: sweep the rest
of the suite for the same pattern**, since the site's persistence means any
other test asserting a global count, a global "no rows besides mine" claim,
or an unqualified `frappe.db.count(...)` / `frappe.get_all(...)` without a
filter scoping it to the test's own data is exposed to the same failure mode,
today or on the next accumulation of leftover data.

## Inputs

- `the_visaguy/the_visaguy/visa_tracking/tests/` — the full test module set.
- The already-fixed instance, for the pattern to search for: assertions on
  `Visa Tracker Audit Log` row counts and on `Visa Tracking Application`
  identity uniqueness that were previously unscoped.
- `ongoing/visa-tracking-implementation/12-session-2026-09-01-task-011-012.md`
  — this session's full triage narrative, including the exact failure modes
  and fixes for reference.

## Required behaviour

1. Search every test module under `visa_tracking/tests/` for:
   - assertions on `frappe.db.count(...)` or `len(frappe.get_all(...))`
     against any DocType without a filter that scopes to records the test
     itself created (by name, by a unique synthetic identity, by a
     test-specific tag/timestamp, etc.),
   - assertions that assume a table starts empty or at a specific count,
   - reliance on a shared/hardcoded synthetic identity (e.g. a fixed
     passport number + DOB) across multiple tests where the underlying
     business rule enforces uniqueness per identity (as
     `create_tracking_application` does).
2. For each instance found, either scope the assertion to the test's own
   records, or give the test a unique synthetic identity per test (not
   reused across the suite), and add `tearDown` cleanup where appropriate —
   following the same fix pattern already applied to
   `test_audit_rows_contain_no_pii`.
3. Record which files/tests were audited and which were changed, even if the
   answer for some files is "audited, no issue found."

## Constraints

- Synthetic data only: `P0000000`-style passport numbers, `1990-01-01`-style
  DOBs, `203.0.113.x` IPs — but per this task's own finding, do not reuse the
  exact same synthetic identity across tests that exercise
  one-active-application-per-identity logic.
- Test on `visa-tracker-test.localhost`, not `visaguy`.
- Do not push to any Git remote.
- Do not weaken an assertion to make it pass; scope it correctly instead.

## Expected changes

- Fixes to any additional unscoped assertions found in
  `visa_tracking/tests/`.
- No production/application logic changes are expected; this is test-only
  work unless the audit surfaces an actual defect, in which case stop and
  report rather than silently fixing application code under a test-audit
  task.

## Validation

- Full `the_visaguy` suite run twice in succession against the same
  persistent test site, back to back, with no site reset between runs —
  the second run must pass identically to the first. (This is the
  reproduction of the actual failure mode: the first session's fresh-site run
  passed while a later run against the same accumulated-state site failed.)
- Report the before/after test count, per this feature's standing practice of
  reporting suite progression numbers.

## Definition of done

- Every test module under `visa_tracking/tests/` has been reviewed for the
  pattern described above.
- All instances found are fixed and verified by the twice-in-a-row run
  described in Validation.
- A short audit note lists every file reviewed and its outcome (fixed /
  no issue found).

## Extension (2026-09-03) — two `TestPublicApiSecurity` tests still count audit rows globally

Found during the ADR-011 (unkeyed lookup hash) change: **two tests in
`TestPublicApiSecurity` still count `Visa Tracker Audit Log` rows without
scoping the count to their own test's activity**, and were not caught by
this task's original sweep:

- `test_audit_rows_contain_no_pii`
- `test_invalid_combination_matches_not_found_shape`

Both fail once enough `Visa Tracker Audit Log` rows have accumulated under
one hash value — the same class of failure this task was written to sweep
for and fix. This is not a new product risk; it is the same test-fragility
pattern this task already covers, found to be incomplete. **Add these two
tests explicitly to the required sweep scope (item 1/2 of "Required
behaviour" above)**, scope their assertions to rows produced by their own
test activity (unique synthetic identity and/or a filter on the test's own
audit rows, following the pattern already applied to the original
`test_audit_rows_contain_no_pii` fix referenced in "Context" above), and add
`tearDown` cleanup where appropriate. Do not close this task on the original
scope alone — the twice-in-a-row validation run must also cover these two
tests.

## Completion evidence (2026-09-14)

**Audit** of every module under `visa_tracking/tests/` and
`the_visa_guy/doctype/visa_tracking_application/test_visa_tracking_application.py`
for unscoped counts, table-starts-empty assumptions, and shared identities on
uniqueness-enforcing paths.

| File | Outcome |
|---|---|
| `test_visa_tracking_application.py` | **Fixed** `test_invalid_combination_matches_not_found_shape`: audit rows filtered by endpoint + IP hash only; now also excludes rows that existed before the test. `test_audit_rows_contain_no_pii` was already scoped (2026-09-03). Other counts are scoped (`DocPerm` Guest rows is a genuine global invariant). |
| `test_reconciliation_service.py` | No issue. `frappe.db.count("Passport Extraction")` is a before/after equality inside one test transaction with no workers; other counts filter by application or Process File. |
| `test_lifecycle_service.py` | No issue. Counts filter by application or hash; identities `P0000101`/`P0000102` unique; `P0000000` only in direct inserts that bypass `create_tracking_application`. |
| `test_public_api.py` | No issue. `P0000402` shared by two tests in one class, both clean up in `tearDown`; list endpoint assertions scoped to the session. |
| `test_passport_extraction_auto_verify.py` | No issue. Counts filter by extraction; `P0000201` also appears in `test_pf_process_file_status_trigger.py`, but since ADR-015 reuse is per applicant row, not per identity, so they cannot collide. |
| `test_audit_service.py` | No issue. Rows filtered by the names the test created. |
| `test_fileflo_inspection.py`, `test_status_service.py`, `test_pf_process_file_status_trigger.py`, `test_response_service.py`, `test_recompute_lookup_hash_unkeyed.py`, `test_link_tracking_applications_patch.py`, `test_session_service.py` | No issue. Counts filter by application, collection or extraction. |
| `test_lookup_service.py`, `test_rate_limit_service.py`, `test_security_utils.py`, `test_settings.py`, `test_status_resolution.py`, `test_request_handlers.py`, `test_process_file_status_validate.py` | No issue. Pure tests, no database. |

**Change.** `the_visaguy` `12ded1a` (test only; no application code).

**Validation.** Full on-site suite twice back to back on
`visa-tracker-test.localhost`, no reset in between: **425 run, OK** and
**425 run, OK** (before this session's work: 418 run).
