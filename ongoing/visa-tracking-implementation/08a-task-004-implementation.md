# TASK-004 Implementation Report — FileFlo Queued Passport Detection

> Date: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-004 — FileFlo queued passport detection (resumed interrupted run)
> Repositories: `fileflo`, `the_visaguy`
> Branch: `feat/visa-tracker` in both feature worktrees

## Verdicts

- **fileflo commit SHA:** `fa1d6b38351ef1dfc5e9a4bb66ddae22b26f7866` (`feat: add generic post-persistence extension event`)
- **the_visaguy commit SHA:** `34cb47754e9b31324ac81f64bd923cef7b22c082` (`feat: queue passport extraction from FileFlo`)
- **Pure/static verdict:** pass — all static gates green; pure tests green in both apps.
- **Runtime verdict:** deferred — no dedicated test site; `root_password` absent from bench `common_site_config.json` (same blocker recorded by TASK-003). Deferred to TASK-010.
- **TASK-004 verdict:** static-complete, runtime-deferred.

## Recovery evidence (interrupted-run resumption)

The previous executor's uncommitted work was captured remotely before any repair. Nothing was reset, stashed, cleaned, or overwritten; local `.staging` patches were read only as evidence and matched the remote diffs (not reapplied).

### fileflo worktree (pre-repair)

- Branch `feat/visa-tracker`, HEAD `6683010e89d9209363e6ba3881f4a90a47420bd2` (matches ground facts).
- `git status --short`: `M fileflo/data_collection.py`, `M fileflo/hooks.py`, `?? fileflo/events.py`, `?? fileflo/tests/` (`__init__.py`, `test_events.py`).
- Diff stat: `data_collection.py` +33/-1, `hooks.py` +6. Diff contained only TASK-004 content (generic dispatcher, payload builder, hook declaration).

### the_visaguy worktree (pre-repair)

- Branch `feat/visa-tracker`, HEAD `f7ad8c0518a6442cbb33136b84dba524f2909ecd` (matches ground facts).
- `git status --short`: `M the_visaguy/hooks.py`, plus untracked `visa_tracking/jobs.py`, `services/extraction_orchestrator.py`, `services/fileflo_inspection_service.py`, `utils/idempotency.py`, `utils/provenance.py`, `tests/test_fileflo_inspection.py`.
- Diff: `hooks.py` +5 (subscriber registration only).

### Overlap check

No unrelated changes were mixed into either worktree; every modified/untracked path is in TASK-004 `expected_files`. `processflo` remained dirty only in its pre-existing unrelated file `processflo/generate_file_collection.py` — not touched. `passport_extractor` worktree untouched at `034f1c17bc872fe8ebcd8f55df797b6c401e7eb1` (read-only this task).

## Defects found and repaired

| # | File | Defect | Fix |
|---|------|--------|-----|
| 1 | `the_visaguy/visa_tracking/services/extraction_orchestrator.py` | `frappe.session.user` raises when no site/session is bound (background/test contexts) | Added `_safe_session_user()` helper (try/except with `Guest` fallback) |
| 2 | `the_visaguy/visa_tracking/tests/test_fileflo_inspection.py` | `@patch("...provenance.frappe.db")` crashes on the unbound `frappe.db` LocalProxy | Bound a `MagicMock` to `frappe.local.db` in `setUp`/`tearDown` of `TestProvenanceResolution` |
| 3 | same | `test_creates_extraction_for_private_passport_file` asserted `validate_passport_file.assert_called_once()` while the orchestrator (its only caller) was mocked | Removed the decorator/assertion from that test |
| 4 | same | `FrappeTestCase` integration class errored in `setUpClass` without a site | `setUpClass` now raises `unittest.SkipTest` (deferred to TASK-010) |
| 5 | same | `frappe.utils.now()` touches unbound `frappe.flags` in pure tests | Patched `now` in the orchestrator creation test |
| 6 | `fileflo/fileflo/data_collection.py` | In-memory `ff_file_collection` child rows were stale (children saved via separate doc objects), so the payload could omit uploaded file rows | `ff_file_collection.reload()` before building the payload |
| 7 | `fileflo/fileflo/tests/test_events.py` | Test fixtures contained passport/MRZ terminology (`passport_front`, `MRZ`) inside FileFlo, violating the generic-terminology boundary | Renamed fixtures to generic values; dropped the `MRZ` literal (boundary-guard strings for the forbidden-imports test intentionally retained) |

Coverage added while repairing: missing-file skip case, long-worker enqueue + `last_job_id` trace assertion, bounded retry re-enqueue and retry-limit stop.

## Changed files (committed)

### fileflo @ `fa1d6b3`

- `fileflo/data_collection.py` — reload + dispatch of the generic after-commit extension event; `_build_extension_payload` (stable identifiers only).
- `fileflo/events.py` — `dispatch_after_commit_extension_event`; iterates `fileflo_extension_handlers`, enqueues each with `enqueue_after_commit=True`; silent drop when no handlers.
- `fileflo/hooks.py` — declares `fileflo_extension_handlers = []`.
- `fileflo/tests/__init__.py`, `fileflo/tests/test_events.py` — pure tests: payload shape, after-commit flag, silent drop, forbidden-import guard, no-PII guard.

### the_visaguy @ `34cb477`

- `the_visaguy/hooks.py` — registers `the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection` under `fileflo_extension_handlers`.
- `the_visaguy/visa_tracking/jobs.py` — subscriber (thin enqueue only), `inspect_fileflo_collection` short-queue entry, `enqueue_missing_fileflo_extractions` backfill seam with idempotency-key dedup.
- `the_visaguy/visa_tracking/services/fileflo_inspection_service.py` — settings gate, exact `field_id` set match, private-file skip with redacted outcome, bounded exponential-backoff retry.
- `the_visaguy/visa_tracking/services/extraction_orchestrator.py` — idempotent `Passport Extraction` creation (`Queued`, `FileFlo Submission`, provenance fields, safe `requested_by`), no auto-retry on `Failed`, long-worker enqueue to `passport_extractor.passport_extractor.jobs.run_passport_extraction`, `last_job_id` trace write after enqueue only.
- `the_visaguy/visa_tracking/utils/idempotency.py` — SHA-256 key helper and newest-match lookup.
- `the_visaguy/visa_tracking/utils/provenance.py` — `FF File Collection File` → `FF Document` → private `File` resolution with stable redacted error codes; generic Frappe APIs only.
- `the_visaguy/visa_tracking/tests/test_fileflo_inspection.py` — 18 tests (17 pure pass, 1 integration skipped/deferred).

## Validation commands and results

All run on the bench host with worktree-first `PYTHONPATH` and bench Python 3.10 (`/home/shahzad/bench/env/bin/python`).

| Gate | Command (abbreviated) | Result |
|------|----------------------|--------|
| fileflo pure tests | `PYTHONPATH=<fileflo wt>:<frappe> python -m unittest discover -s <wt>/fileflo/tests -t <wt>` | 6 tests, OK |
| the_visaguy pure tests | `PYTHONPATH=<visaguy wt>:<passport_extractor wt>:<frappe> python -m unittest the_visaguy.visa_tracking.tests.test_fileflo_inspection` | 18 tests, OK (1 skipped — deferred integration) |
| Python compile | `python -m py_compile` on every new/modified `.py` in both worktrees | Pass |
| Module resolution | `fileflo.__file__` / `the_visaguy.__file__` resolve inside their worktrees | Pass |
| Hook resolution | `fileflo.hooks.fileflo_extension_handlers == []`; the_visaguy handler list resolves `enqueue_fileflo_inspection` via importlib | Pass |
| Extractor seam resolution | `passport_extractor.passport_extractor.utils.validate_passport_file` and `.jobs.run_passport_extraction` import from the pinned worktree | Pass |
| `git diff --check` | both worktrees | Pass |
| Working trees after commit | `git status --short` | Both clean |

### Dependency-boundary scans

- fileflo production source: no matches for `the_visaguy`, `passport_extractor`, `processflo`, `Visa Tracker`, `Visa Tracking`, `Passport Extraction`, `passport`, `MRZ`. Test file retains only the intentional forbidden-imports guard list.
- the_visaguy: no `fileflo`/`processflo` imports anywhere. `passport_extractor` references limited to the allowed public seam (`...utils.validate_passport_file`, function-local import) and the worker dotted-path string.
- PII/secret scan: only synthetic fixture values in tests (e.g. fake `P12345678` used to assert absence); no real passport numbers, DOBs, MRZ lines, file paths, or secrets. Pre-existing TASK-005 `test_lookup_service.py` synthetic values unchanged and out of scope.
- `processflo`: untouched; only pre-existing unrelated modification `processflo/generate_file_collection.py` remains.
- Full diff review: both diffs contain TASK-004 scope only.

## Runtime gates deferred to TASK-010

- Dedicated test site creation (blocked: no `root_password` in `common_site_config.json`).
- `bench --site <test-site> migrate`; synthetic FileFlo submission → exactly one `Queued` extraction + one long-queue job; non-configured field → no extraction; repeated event → no duplicates; public/missing file → no extraction/OCR; disabled settings → silent stop; reconciliation backfill behavior.
- `TestFileFloInspectionIntegration` (FrappeTestCase) written but skipped until the site exists.
- Pre-existing note: TASK-005's `FrappeTestCase` suites (`test_settings`, `test_lookup_service`, DocType tests) also require a site and error without one; unchanged by this task.
- No migration, test, or build ran on site `visaguy`. No push performed.

## Deviations

- The enqueue path used is `passport_extractor.passport_extractor.jobs.run_passport_extraction` per the verified ground facts and the installed package layout (outer package has `__init__.py`); TASK-004 §3.10's shorthand `passport_extractor.jobs...` does not resolve in this environment.
- Report written to `ongoing/visa-tracking-implementation/08a-task-004-implementation.md` per the resumption prompt (supersedes the `05c-...` path listed in the task file); task/feature lifecycle files were not moved — left for coordinator reconciliation.
- Repairs were applied directly to the remote worktrees via verified file transfer (the interrupted state already lived there); local `.staging` patches were used as read-only recovery evidence only.
