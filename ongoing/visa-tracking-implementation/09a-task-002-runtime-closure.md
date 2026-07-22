# TASK-002 Runtime Closure Report — Passport Extractor Scaffold and DocType

**Date:** 2026-07-22
**Prompt:** `ongoing/visa-tracking-implementation/prompts/09a-task-002-runtime-closure.txt`
**Bench:** `/home/shahzad/bench` on `erpcode.tridz.in:2257` (SSH user `shahzad`)
**Feature worktree:** `/home/shahzad/visa-tracker-worktrees/passport_extractor`, branch `feat/visa-tracker`, HEAD `034f1c17bc872fe8ebcd8f55df797b6c401e7eb1` (verified clean)
**Dedicated test site:** `visa-tracker-test.localhost`
**Verdict:** `runtime-failed` — dedicated-site runtime verification executed; a genuine controller defect surfaced (no app logic edited)

---

## Summary

The previously blocking condition is resolved: the `root_password` JSON key is **present** in `/home/shahzad/bench/sites/common_site_config.json` (count-only check, value never printed). The ENTRY/STOP GATE therefore passed and the SAFE RUNTIME WORK was executed: the dedicated nonproduction site `visa-tracker-test.localhost` was created (it did not previously exist), `passport_extractor` was installed from the feature worktree with worktree-first `PYTHONPATH`, tests were enabled on that site only, migration succeeded, and the DocType schema/permissions were verified against the database.

The full `passport_extractor` test suite was then run twice (targeted `--doctype` run and full `--app` run) with identical, reproducible results: **61 tests, 38 passed, 16 errors, 7 failures**. All 12 TASK-002 integration errors share one root cause — a genuine controller defect (`_validate_request_audit` rejects legitimate post-insert status transitions). Per the executor contract, no app logic was edited to force a pass; the exact failing tests and trace summaries are recorded below for a separate implementation-fix task. Site `visaguy` was never touched; no commits, pushes, or deploys occurred; only synthetic data was used.

---

## Entry/stop gate evidence

| Check | Command (redacted) | Result | Evidence label |
|-------|--------------------|--------|----------------|
| `root_password` key presence | `grep -c '"root_password"' /home/shahzad/bench/sites/common_site_config.json` | **1 — key present** | configured-unverified |
| Worktree HEAD/branch/cleanliness | `git -C <worktree> rev-parse HEAD && git branch --show-current && git status --short` | HEAD `034f1c17bc872fe8ebcd8f55df797b6c401e7eb1`, branch `feat/visa-tracker`, clean | source-wired |
| Pre-existing dedicated site | `ls /home/shahzad/bench/sites` | Only `visaguy` present; `visa-tracker-test.localhost` did **not** exist — no ambiguity | runtime-verified |
| TASK-003 PDF prerequisite | `<bench>/env/bin/python -c "import fitz; print(fitz.__version__)"` | `pymupdf 1.28.0` importable | runtime-verified |
| OCR stack presence | `importlib.util.find_spec` for `paddleocr`, `paddle`, `cv2`, `numpy` | All present (`paddle 3.2.0`, `paddleocr 3.7.0`) | present |

Only key presence was inspected. The config file contents and no credential value of any kind were printed, copied, logged, or stored.

## Dedicated-site creation evidence

| Step | Command (redacted) | Result | Evidence label |
|------|--------------------|--------|----------------|
| Create site | `PW=$(openssl rand -base64 24) && bench new-site visa-tracker-test.localhost --admin-password "$PW"; unset PW` (from `/home/shahzad/bench`) | Exit 0; Frappe installed; scheduler-disabled notice only | runtime-verified |
| Worktree-first module resolution | `PYTHONPATH=<worktree> ./env/bin/python -c "import passport_extractor; print(passport_extractor.__file__)"` | Resolves to `/home/shahzad/visa-tracker-worktrees/passport_extractor/passport_extractor/__init__.py` | runtime-verified |
| Install app | `PYTHONPATH=<worktree> bench --site visa-tracker-test.localhost install-app passport_extractor` | `Updating DocTypes for passport_extractor: 100%` | runtime-verified |
| Enable tests (dedicated site only) | `bench --site visa-tracker-test.localhost set-config allow_tests true` | OK | configured-unverified |
| Migrate | `PYTHONPATH=<worktree> bench --site visa-tracker-test.localhost migrate` | Success — frappe + passport_extractor DocTypes and dashboards synced, `after_migrate` hooks executed | runtime-verified |

The Administrator password was a generated random disposable value, passed non-interactively via `--admin-password`, and was never printed or recorded. The DB root password was picked up by `bench new-site` from the bench config; it was never requested, printed, or handled.

### Environmental note — bench redis services

`bench migrate` initially refused to run because this bench's redis services were stopped. They were started using the bench's own `config/redis_cache.conf`, `config/redis_queue.conf`, and `config/redis_socketio.conf` (ports `13008`/`11008`/`12008`, matching the bench's `redis_cache`/`redis_queue`/`redis_socketio` config keys; `use_redis_auth` key present). All three answered `PONG`. This is the bench's own documented service set (its `Procfile`); no other user's redis instance was touched. They were left running for TASK-010 reuse.

## DocType / schema / permissions verification (read-only SQL via `bench --site visa-tracker-test.localhost mariadb`)

| Check | Result | Evidence label |
|-------|--------|----------------|
| `tabPassport Extraction` table exists | Yes | runtime-verified |
| Data-field count (excluding layout fields) | **47** | runtime-verified |
| `status` options | Exactly `Queued, Processing, Extracted, Needs Review, Verified, Rejected, Failed, Duplicate, Superseded` | runtime-verified |
| Permlevel-1 fields | `error_message`, `mrz_line_1`, `mrz_line_2`, `raw_extraction_result`, `raw_ocr_text` | runtime-verified |
| `Passport Extractor User` DocPerms | level 0: read/write/create/delete; level 1: read/write | runtime-verified |
| `System Manager` DocPerms | level 0 full access | runtime-verified |
| Guest DocPerms | **0 rules** | runtime-verified |
| `Passport Extractor User` Role exists | Yes | runtime-verified |

## Test execution

Both runs used `PYTHONPATH=/home/shahzad/visa-tracker-worktrees/passport_extractor` and `--site visa-tracker-test.localhost`:

1. Targeted: `bench --site visa-tracker-test.localhost run-tests --doctype "Passport Extraction"` → `Ran 61 tests` / `FAILED (failures=7, errors=16)`
2. Full app: `bench --site visa-tracker-test.localhost run-tests --app passport_extractor` → identical result (`Ran 61 tests in 9.3s`, `FAILED (failures=7, errors=16)`). Full log retained on the bench host at `/tmp/vt_tests_full.log` (contains only synthetic data).

### Results by suite

| Suite (class) | Task | Tests | Passed | Errors | Failures |
|---------------|------|------:|-------:|-------:|---------:|
| `TestPassportExtractionUtils` | TASK-002 (unit) | 8 | 8 | 0 | 0 |
| `TestPassportExtractionIntegration` | TASK-002 (integration) | 24 | 12 | **12** | 0 |
| `TestMRZParser` | TASK-003 (unit) | 13 | 13 | 0 | 0 |
| `TestImagePreprocessor` | TASK-003 (unit) | 2 | 2 | 0 | 0 |
| `TestExtractionServiceCodes` | TASK-003 (unit) | 3 | 3 | 0 | 0 |
| `TestPassportExtractionPipeline` | TASK-003 (integration) | 11 | 0 | **4** | **7** |
| **Total** | | **61** | **38** | **16** | **7** |

### TASK-002 failures — exact tests and root cause

All 12 TASK-002 errors are in `TestPassportExtractionIntegration` and share one root cause:

- `test_duplicate_rejects_missing_target`
- `test_duplicate_rejects_self_reference`
- `test_duplicate_requires_existing_target`
- `test_full_lifecycle_sets_timestamps_and_verified_audit`
- `test_retry_count_bounds_enforced`
- `test_retry_count_increments_from_failed_to_queued`
- `test_superseded_rejects_self_reference`
- `test_superseded_rejects_unverified_target`
- `test_superseded_requires_verified_target`
- `test_terminal_ocr_failed_sets_processing_completed_on`
- `test_verified_audit_preserved_after_superseded`
- `test_verified_requires_verified_by_and_verified_on`

**Trace summary (representative, `test_full_lifecycle_sets_timestamps_and_verified_audit`):** the test performs a legitimate `Queued -> Processing` transition via `doc.save(ignore_permissions=True)`; `validate()` calls `_validate_request_audit()` (`passport_extraction.py:31` → `:82`), which raises `frappe.exceptions.ValidationError: Request audit fields cannot be changed.` even though the test did not modify request-audit fields. The string appears 24 times in the log (12 errors × 2 lines each), confirming a single shared root cause. This is a **genuine controller defect that only surfaces against a real database** (consistent with a value-comparison mismatch against `get_doc_before_save()`, e.g. datetime handling of `requested_on`) — it blocks every multi-save lifecycle path, including the valid transitions from TASK-002 §3.2. The 12 integration tests that passed are the single-insert/negative-path cases that never perform a second save.

### TASK-003 failures — exact tests and causes

Errors (4):

- `test_retry_extraction_transitions_failed_to_queued`, `test_retry_extraction_enforces_limit`, `test_worker_is_idempotent_for_non_queued_record` — helper inserts a record directly in `Failed` status; controller raises `ValidationError: New Passport Extraction records must start in Queued status.` (`passport_extraction.py:48`). Test/design mismatch to be resolved by the fix task (controller intent vs test fixture approach).
- `test_public_file_rejected_before_byte_access` — `ValidationError: Passport file must be private.` (`utils.py:87`) propagates out of the test's record-creation helper instead of being asserted; the underlying validation itself fired as designed.

Failures (7), all showing the OCR pipeline landing in `Failed`/`OCR_ENGINE_ERROR` at runtime instead of the expected outcome:

- `test_service_extracts_valid_synthetic_mrz` — `status 'Failed' != 'Extracted'`
- `test_corrupted_check_digit_needs_review` — `status 'Failed' != 'Needs Review'`
- `test_multi_page_pdf_finds_mrz_on_second_page` — `'Failed' not in ('Extracted', 'Needs Review')`
- `test_rotated_synthetic_image_extracts` (rotations 90/180/270) — `'Failed' not in ('Extracted', 'Needs Review')`
- `test_missing_mrz_image_fails_no_mrz_found` — `error_code 'OCR_ENGINE_ERROR' != 'NO_MRZ_FOUND'`

`~/.paddlex` exists but contains no downloaded official models, so the PaddleOCR engine cannot produce results in this environment; every synthetic OCR case degrades to `Failed`/`OCR_ENGINE_ERROR`. Whether this is purely environmental (models not preloaded — cf. TASK-010 rollout checklist item "PaddleOCR models preloaded") or also masks a pipeline defect is for the fix task to determine after models are available.

## Safety attestations

- Site `visaguy` was never migrated, tested, installed to, or written to; no command targeted it.
- Original app checkouts and `processflo` untouched; all app code used came from the clean feature worktree at the expected HEAD.
- No app logic, test code, or schema was edited — the defect is reported, not worked around.
- No Git identity changes, commits, pushes, or deploys.
- No credential value, real passport data, MRZ, DOB, or PII was printed, copied, or stored; test data was synthetic only.
- The dedicated site `visa-tracker-test.localhost` was **left in place** (not dropped) for TASK-010 reuse; redis services left running; full test log at `/tmp/vt_tests_full.log` on the bench host.
- TASK-002's task file was not moved; the coordinator reconciles status.

## Verdict

**TASK-002 runtime: `runtime-failed`.** The runtime gate is no longer environmentally blocked — site creation, worktree-first install, migration, and schema/permission verification all succeeded (runtime-verified). However, the TASK-002 integration suite surfaces a genuine controller defect (`_validate_request_audit` rejecting legitimate post-insert transitions; 12/24 integration tests error, reproducible across two runs). Per the executor contract, execution stopped here without editing app logic. Recommended follow-up: a TASK-002 fix task for the request-audit comparison defect, and a TASK-003 follow-up covering the four errored pipeline tests and OCR model availability before re-running `TestPassportExtractionPipeline`.
