# TASK-002/003 Corrective Report — 09b Runtime Defect Fixes

**Date:** 2026-07-22
**Prompt:** `ongoing/visa-tracking-implementation/prompts/09b-task-002-003-corrective.txt`
**Bench:** `/home/shahzad/bench` on `erpcode.tridz.in:2257` (SSH user `shahzad`)
**Feature worktree:** `/home/shahzad/visa-tracker-worktrees/passport_extractor`, branch `feat/visa-tracker`
**Base HEAD:** `034f1c17bc872fe8ebcd8f55df797b6c401e7eb1`
**Corrective commit:** `cbea2159cc189debd36bc69d661aee434396b4fc` (local only; no push; environment-default Git identity; no `--author`)
**Dedicated test site:** `visa-tracker-test.localhost`
**Verdict:** `defects 1-3 fixed` / `defect 4 partially resolved` — suite improved 38p/16e/7f → **55 pass / 0 errors / 6 failures**; the 6 remaining failures are genuine preprocessing-pipeline defects, diagnosed exactly and left untouched per the executor contract ("report exact failures and stop").

---

## Test counts (reproducible, worktree-first `PYTHONPATH`, `bench --site visa-tracker-test.localhost run-tests --app passport_extractor`)

| Stage | Tests | Passed | Errors | Failures | Evidence label |
|-------|------:|-------:|-------:|---------:|----------------|
| Before (09b baseline re-run, identical to 09a) | 61 | 38 | 16 | 7 | runtime-verified |
| After defects 1–3 fixes | 61 | 54 | 0 | 7 | runtime-verified |
| After defect 4 (models + engine compat) | 61 | 56 | 0 | 5 | runtime-verified |
| After fixture legibility repair | 61 | 55 | 0 | 6 | runtime-verified |
| **Final (confirming re-run at commit `cbea215`)** | **61** | **55** | **0** | **6** | runtime-verified |

Pure/unit tiers standalone (no site bound): `TestPassportExtractionUtils`, `TestMRZParser`, `TestImagePreprocessor`, `TestExtractionServiceCodes` — **26/26 OK** with worktree-first `PYTHONPATH` (runtime-verified).

Logs on the bench host (synthetic data only): `/tmp/vt_tests_before_09b.log`, `/tmp/vt_tests_after_defect123.log`, `/tmp/vt_tests_after_09b.log`, `/tmp/vt_tests_after_09b_r2.log`, `/tmp/vt_tests_final_09b.log`.

## DEFECT 1 — controller audit datetime comparison (12 integration errors) — FIXED

**Root cause confirmed.** `before_insert`/`_validate_verified_state` assign `frappe.utils.now()` (a string with microseconds); `get_doc_before_save()` returns database values as datetime objects. `requested_on`/`verified_on` columns are `datetime(6)` (verified via `SHOW COLUMNS`, runtime-verified), so full precision is preserved and the mismatch was purely string-vs-datetime type inequality.

**Diff (`passport_extraction.py`):**

- Import `get_datetime` alongside `now`.
- New module helper `_same_datetime(value, other)`: both empty → equal; exactly one empty → not equal; otherwise `get_datetime(value) == get_datetime(other)`.
- `_validate_request_audit`: early-return when no `old`; compare `requested_by` directly and `requested_on` via `_same_datetime`. Same error string retained (`Request audit fields cannot be changed.`).
- `_preserve_verification_audit`: `verified_on` compared via `_same_datetime` (same retained error string).
- Sweep for the same pattern: no other controller/utils code compares stored datetime fields against `get_doc_before_save()` values (`processing_started_on`/`processing_completed_on` are set-if-empty only; retry comparisons are integer-based). `verified_on` re-stamping behavior unchanged — `_validate_verified_state` still sets it only when empty on entry to `Verified`.

**Immutability not weakened (re-verified in the passing suite):** `test_request_audit_is_server_owned_and_immutable` (tampering with `requested_by` still raises), `test_verified_audit_preserved_after_superseded`, `test_full_lifecycle_sets_timestamps_and_verified_audit`, all retry/duplicate/supersession tests — all pass (runtime-verified).

## DEFECT 2 — fixture invariant mismatch (3 errors) — FIXED

The "new records begin Queued" invariant is unchanged. Fixtures now reach non-Queued states through legitimate controller transitions via a new `_transition` helper on `TestPassportExtractionPipeline` (mirrors the integration-class helper):

- `test_retry_extraction_transitions_failed_to_queued`: insert Queued → Processing → Failed, then `retry_extraction`; assertions unchanged (Queued, `retry_count == 1`).
- `test_retry_extraction_enforces_limit`: exhausts the budget legitimately (`Processing → Failed → Queued` × `EXTRACTION_RETRY_LIMIT`, then Processing → Failed), asserts `retry_count == EXTRACTION_RETRY_LIMIT`, then asserts `retry_extraction` raises. Controller `MAX_RETRY_COUNT` (3) accommodates the two increments.
- `test_worker_is_idempotent_for_non_queued_record`: reaches `Extracted` via Queued → Processing → Extracted; assertion intent unchanged.

## DEFECT 3 — public-file assertion bug (1 error) — FIXED

`test_public_file_rejected_before_byte_access` now asserts the designed behavior (TASK-002 §5.3: public files are rejected at insert):

- `assertRaises(frappe.ValidationError)` around the record-creation helper; message contains "private".
- No byte access: `mock.patch.object(PassportExtraction, "compute_and_set_file_hash")` with `assert_not_called()` (a negative call assertion only — no OCR engine or pipeline behavior is mocked).
- Message PII-freeness asserted (no file URL, no MRZ text, no passport number); no `Passport Extraction` record persists for the public file.

## DEFECT 4 — OCR pipeline runtime (7 failures) — PARTIALLY RESOLVED; 6 genuine preprocessing defects remain

### 4a. Model preload — SUCCEEDED (runtime-verified)

The first engine-init attempt failed before any download: `ValueError: Unknown argument: use_gpu` from `paddleocr/_common_args.py` — the wrapper's `PaddleOCR(...)` call used PaddleOCR 2.x-era kwargs against the installed `paddleocr 3.7.0`. This made the mandated preload impossible without a minimal compatibility repair.

**Engine wrapper fix (`paddle_ocr_engine.py`, verified against the installed 3.7 signature and `parse_common_args` allow-list):**

- `use_angle_cls=True` → `use_textline_orientation=True` (3.x replacement; keeps the TASK-003 §3.2 angle-classification mandate).
- `use_gpu=False` → `device="cpu"`.
- `det_db_thresh`/`det_db_box_thresh` → `text_det_thresh`/`text_det_box_thresh`.
- `show_log=False` dropped (no 3.x equivalent in the accepted common args).
- `use_doc_orientation_classify=False`, `use_doc_unwarping=False` — the pipeline does its own deterministic rotation recovery; this also keeps the preload minimal.
- `engine.ocr(path, cls=True)` → `engine.predict(path)`; result parsing updated to the 3.x mapping format (`rec_texts`/`rec_scores`). `ocr()` in 3.x is a deprecated alias that forwards `**kwargs` to `predict()`, so `cls=True` raised `TypeError`.

**Preload outcome:** engine init via the app's own `_get_engine()` (worktree-first `PYTHONPATH`, bench env python) printed `ENGINE_INIT_OK` after downloading into the `shahzad` user's own cache (`~/.paddlex/official_models`): `PP-LCNet_x1_0_textline_ori`, `PP-OCRv6_medium_det`, `PP-OCRv6_medium_rec`. Downloads stayed on the bench host; nothing printed or exfiltrated beyond progress/logs. Network path for model download works.

### 4b. Synthetic fixture legibility — test-artifact repair

With the engine running, offline diagnostics showed the fixture's Pillow default bitmap font (~6×11 px glyphs) is far below OCR resolution — recognition returned garbage (`'そう9,♡、Cじ」'`) and zero MRZ candidates. Repaired `_synthetic_mrz_image` to render with a scalable monospace font (DejaVu Sans Mono 32 px, with Noto Sans Mono and `load_default(size)` fallbacks) on a 1200×400 canvas. Same offline image then read at **0.995 confidence** on both MRZ lines (including the classic `UTO`→`UT0` misread the parser is designed to correct). No assertions were weakened and no real data was used.

### 4c. Remaining 6 failures — GENUINE preprocessing-pipeline defects (reported, not fixed, per contract)

Failing tests (identical across two full runs):

- `test_service_extracts_valid_synthetic_mrz` — `'Failed' != 'Extracted'`
- `test_corrupted_check_digit_needs_review` — `'Failed' != 'Needs Review'`
- `test_multi_page_pdf_finds_mrz_on_second_page` — `'Failed' not in ('Extracted', 'Needs Review')`
- `test_rotated_synthetic_image_extracts` (rotation=90, 180, 270) — `'Failed' not in ('Extracted', 'Needs Review')`

**Exact diagnosis (offline replication of the service's image path: `preprocess_image` → `run_ocr` → `detect_mrz_candidates` → `parse_td3_mrz`):**

1. **Rotation recovery crops non-square images.** `_preprocess_with_opencv` rotates with `cv2.warpAffine(..., (w, h))` — same-canvas rotation without expansion — so a 1200×400 image rotated 90°/270° keeps only the central vertical band (evidenced fragment: `'>>>>>>>>>>>>>>>>>>>'`). Rotated documents can never yield a full MRZ line. This defeats the mandated rotation recovery (TASK-003 §2.3).
2. **The CLAHE → median-blur chain degrades clean text.** On the legible fixture, the 0° preprocessed variant yields only line fragments (`'11M2301015<<<<<<<<<<'`, 20 chars) instead of the full 44-char lines the raw image produces; `detect_mrz_candidates` therefore finds 0 candidates in all 4 variants and the pipeline correctly classifies `Failed`/`NO_MRZ_FOUND`. The raw image bypassing preprocessing reads perfectly (0.995).

The pipeline's classification, redaction, file-format validation, worker idempotency, and retry logic all behave correctly — the defect is localized to `ocr/image_preprocessor.py`. Per the executor contract ("If models download and tests still fail, a genuine pipeline defect exists: report exact failures and stop; do not redesign the pipeline"), no preprocessing redesign was attempted. **Recommended follow-up:** a TASK-003 corrective task for `image_preprocessor.py` (canvas-expanding rotation; non-destructive preprocessing or inclusion of the raw image among candidates).

**Note on the 5→6 shift:** with the old unreadable bitmap fixture, `test_multi_page_pdf_finds_mrz_on_second_page` incidentally passed (garbage OCR produced a false `Needs Review`); with the legible fixture it now correctly reaches the preprocessing defect and fails — same underlying root cause, now honestly exposed.

## Invariant re-verification (TASK-002 §3, runtime-verified in the final suite)

- Audit-field tampering still raises (`test_request_audit_is_server_owned_and_immutable`).
- Retry bounds enforced (`test_retry_count_bounds_enforced`, `test_retry_count_increments_from_failed_to_queued`, `test_retry_count_cannot_change_outside_retry_transition`).
- Duplicate/supersession rules intact (all six duplicate/superseded tests pass).
- New-record Queued invariant intact (`test_new_record_must_start_queued` plus the repaired fixtures).
- Public files rejected before byte access (Defect 3 test).

## Safety attestations

- Site `visaguy` was never targeted; original app checkouts and `processflo` untouched.
- All edits in the feature worktree only; single local commit `cbea2159cc189debd36bc69d661aee434396b4fc` on `feat/visa-tracker`; worktree clean after commit; no push, no `--author`, no Git identity changes.
- No OCR engine mocking, no weakened assertions, no skipped tests; the 6 remaining failures are reported honestly.
- Synthetic data only; no secrets, PII, real passport data, or MRZ from real documents handled or stored. Model downloads stayed in the bench user's own cache.
- Redis services and the dedicated site left running/in place for reuse; task files not moved.

## Remaining blockers / follow-ups

1. **6 pipeline tests failing** on genuine `image_preprocessor.py` defects (cropped rotations; destructive CLAHE/blur chain) — needs a coordinator-authorized TASK-003 pipeline corrective task.
2. Suite target 61/61 not reached: **55 pass / 0 errors / 6 failures** (all 6 documented above with exact reproduction evidence).
