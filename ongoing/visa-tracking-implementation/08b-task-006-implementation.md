# TASK-006 Implementation Report — Tracking Lifecycle and Status Synchronization

> Date: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-006 — Tracking lifecycle and status synchronization
> Repository: `the_visaguy`
> Worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy` (branch `feat/visa-tracker`)

## Verdicts

- **the_visaguy start SHA:** `34cb47754e9b31324ac81f64bd923cef7b22c082` (clean at TASK-004 HEAD; entry gate satisfied)
- **the_visaguy final SHA:** `9222302035c2c077ed91662cc49af784dac3119f` (`feat: add visa tracking lifecycle sync`)
- **Pure/static verdict:** pass — 82 pure tests green (4 deferred integration skips), all static gates green.
- **Runtime verdict:** deferred — no dedicated test site; `root_password` absent from bench `common_site_config.json` (re-verified this run: 0 matches). Deferred to TASK-010.
- **TASK-006 verdict:** static-complete, runtime-deferred.

## Entry gate evidence

- Worktree HEAD was `34cb477…` on `feat/visa-tracker` with `git status --short` empty before any edit (matches the TASK-004 report and coordinator ground facts).
- `processflo` worktree on `develop`, dirty only in the pre-existing unrelated file `processflo/generate_file_collection.py`; untouched by this task (source-evidenced, re-verified after implementation).
- No push, no other git mutation; single authorized commit only.

## Changed files (commit `9222302`)

| Path | Change |
|------|--------|
| `the_visaguy/hooks.py` | doc_events merge: PF Process File `on_update` converted to list (existing WhatsApp handler preserved, sync handler appended); new `Customer` `on_update`/`after_insert` and `Passport Extraction` `on_update` mappings. No existing mapping replaced. |
| `the_visaguy/visa_tracking/utils/constants.py` | Added `EXTRACTION_STATUS_VERIFIED`, `LEAD_DOCTYPES`, `CORRECTION_ALLOWED_ROLES`. |
| `the_visaguy/visa_tracking/services/status_service.py` | Added `update_tracking_status`, `resolve_active_status`, `get_latest_log_name`; `append_status_log` extended with `changed_by` and session-safe user fallback; `get_public_timeline` now honors `Visa Tracker Settings.status_history_limit` (default 20). |
| `the_visaguy/visa_tracking/services/lifecycle_service.py` | New: verified-extraction linking (Lead/CRM Lead/Customer), idempotent `create_tracking_application`, PF link/sync functions, recursion-safe low-level PF write, role-gated `correct_tracking_status`. |
| `the_visaguy/visa_tracking/services/reconciliation_service.py` | New: report-only `reconcile_missing_extractions` and `reconcile_status_mismatches`. |
| `the_visaguy/visa_tracking/handlers/__init__.py` | New package marker. |
| `the_visaguy/visa_tracking/handlers/lead_handlers.py` | New: Customer `on_update`/`after_insert` handler with re-entrancy guard; copies verified links from Lead, sets `Visa Tracking Application.customer`. |
| `the_visaguy/visa_tracking/handlers/process_file_handlers.py` | New: PF Process File `on_update` observing `custom_client_status` changes only. |
| `the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py` | New: Verified-transition handler resolving Lead/CRM Lead via `source_doctype`/`source_document`, FF File Collection `reference_type/reference_name`, or PF `custom_reference_type/custom_reference_name`. |
| `the_visaguy/visa_tracking/tests/test_status_service.py` | New: 15 pure tests + deferred integration class. |
| `the_visaguy/visa_tracking/tests/test_lifecycle_service.py` | New: 34 pure tests + deferred integration class. |
| `the_visaguy/visa_tracking/tests/test_reconciliation_service.py` | New: 8 pure tests + deferred integration class. |

`the_visaguy/fixtures/client_scripts.json` was **not modified**: the TASK-005 fixture already hides/disables `custom_client_status` when `custom_visa_tracking_application` is blank (§10 satisfied, present).

## Behavior matrix

| Requirement | Implementation | Evidence |
|---|---|---|
| Verified-only linking to Lead/CRM Lead/Customer | `link_verified_extraction_to_lead` / `link_verified_extraction_to_customer`; non-Verified throws; unsupported doctype throws; idempotent | pure tests (source-wired) |
| Source-evidenced resolution | FF `reference_type/reference_name`, PF `custom_reference_type/custom_reference_name`; both `Lead` and `CRM Lead` | handler tests (source-wired) |
| Idempotent application creation by identity hash | `verification_lookup_hash` via `compute_lookup_hash`; reuse on match; Lead-mismatch flags review; competing active records flag review and create nothing; never silently merges | pure tests (source-wired) |
| Settings gates | `enabled`, `auto_create_tracking_application`, `auto_link_verified_passport`, `default_lead_status` (active-validated) | pure tests (source-wired) |
| Canonical status service | `update_tracking_status`: active-status validation, idempotent no-write path (explicit `effective_on` participates only when supplied), atomic save + exactly one log, stable `{log_name, changed, status, previous_status}` result | pure tests (source-wired) |
| Public timeline | newest-first visible rows; settings `status_history_limit`; internal fields (`change_reason`, `correction_of`, `source_document`) never selected | pure tests (source-wired) |
| Bidirectional PF sync | PF→VTA via `on_update` handler + `sync_process_file_client_status`; VTA→PF via `sync_tracking_status_to_process_file`; converges, one log per effective change | pure tests (source-wired) |
| Recursion break | narrowly scoped `frappe.db.set_value(..., update_modified=False)` isolated in `_write_process_file_client_status` (documented in docstring) plus thread-local guard; guard tested active-during/released-after | pure tests (source-wired) |
| Direct corrections | reason mandatory; `Visa Tracker Manager`/`System Manager` only; `correction_of` set to previous log row; reason internal-only | pure tests (source-wired) |
| Customer handler | copies verified links, sets `VTA.customer`, no second application, no status change; idempotent; unverified extraction not copied | pure tests (source-wired) |
| Verified-extraction handler | transition-only trigger; FileFlo/PF provenance resolution; idempotent redelivery | pure tests (source-wired) |
| Report-only reconciliation | missing-extraction report (stable identifiers only, private files only) and status-mismatch report; no mutation/enqueue asserted | pure tests (source-wired) |
| PF client script fixture | hides/disables `custom_client_status` without linked application (TASK-005 fixture, unchanged) | present |

## Tests and static gates

All run on the bench host with worktree-first `PYTHONPATH` (`the_visaguy` wt : `passport_extractor` wt : `bench/apps/frappe`) and bench Python 3.10 (`/home/shahzad/bench/env/bin/python`).

| Gate | Result |
|------|--------|
| New pure tests (status/lifecycle/reconciliation) | 57 pass, 3 skipped (deferred integration classes) |
| Regression: TASK-004 `test_fileflo_inspection` | 18 pass, 1 skipped (unchanged) |
| Combined run at final SHA | **82 tests, OK (skipped=4)** |
| `py_compile` on all new/modified `.py` | Pass |
| `the_visaguy.__file__` resolves inside feature worktree | Pass |
| Hook resolution: all 8 `doc_events` dotted paths import and resolve to callables | Pass (importlib check) |
| Fixture JSON validation (all six fixture files) | Pass |
| `git diff --check` | Pass |
| Dependency scan: no `fileflo`/`processflo` imports anywhere in `the_visaguy`; `passport_extractor` references limited to the pre-existing allowed public seam in `extraction_orchestrator.py` | Pass |
| PII/secret scan of new files | Pass — only synthetic values (`P0000000`, `1990-01-01`); `passport_number`/`date_of_birth` appear only as field reads feeding the HMAC hash (never logged); `log_error` calls carry stable identifiers only |
| `processflo` unchanged (only pre-existing unrelated dirty file, on `develop`) | Pass |
| Full diff review | TASK-006 scope only; existing hook mappings preserved |
| `git status --short` after commit | Clean |

Pre-existing, unchanged: TASK-005's `test_lookup_service.py` / `test_settings.py` (`FrappeTestCase`) error without a site (`IncorrectSitePath: test_site does not exist`) — same state recorded by TASK-004; out of scope here.

## Deferred runtime checks (TASK-010)

- Dedicated test site creation (blocked: bench `common_site_config.json` has no `root_password` key — re-verified this run).
- `bench --site <test-site> migrate` with the new handlers; verified-extraction → application with default Lead status; PF `custom_client_status` change → exactly one log row; correction → PF updated without recursion with reason recorded; reconciliation reports on synthetic mismatches.
- Deferred `FrappeTestCase` integration classes written in all three new test modules (6 placeholder tests, all `SkipTest`-guarded; they must never run against `visaguy`).
- No migration, test, or build ran on site `visaguy`. No scheduler registration added (§9.3 allows deferral; reconciliation functions are safe-to-call Python entry points).

## Evidence labels

- **source-wired** — hooks merge, handler registrations, service/handler call chains evidenced in committed code and pure tests.
- **present** — client-script fixture behavior, settings fields consumed.
- **configured-unverified** — `Visa Tracker Settings` values, `visa_tracker_lookup_hmac_key` config key (name only).
- **runtime-verified** — SSH access, bench layout, worktree states, pure-test/static-gate execution. No runtime Frappe behavior verified (deferred).

## Deviations

- Report written to `ongoing/visa-tracking-implementation/08b-task-006-implementation.md` per the dispatch prompt; the task file's `expected_files` lists `05e-task-006-implementation.md`. Discrepancy noted; lifecycle files not moved (coordinator's responsibility).
- `fixtures/client_scripts.json` (listed in `expected_files`) intentionally unchanged: the TASK-005 fixture already implements the required hide/disable behavior.
- VTA→PF synchronization is delivered through explicit service calls (`correct_tracking_status`, `link_process_file_to_tracking`, `sync_tracking_status_to_process_file`) rather than a `Visa Tracking Application` `on_update` hook; this keeps the exactly-one-log guarantee trivially enforceable. Direct desk edits to `current_status` bypassing the service surface in the report-only `reconcile_status_mismatches` output by design.
- `lookup_service.py` needed no changes (TASK-005 seam already complete; `compute_lookup_hash` returns `(hash, version)`).
