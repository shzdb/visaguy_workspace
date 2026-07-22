# TASK-003 Corrective Report — 09c Preprocessor Defect Fixes

**Date:** 2026-07-22
**Prompt:** `ongoing/visa-tracking-implementation/prompts/09c-task-003-preprocessor-corrective.txt`
**Bench:** `/home/shahzad/bench` on `erpcode.tridz.in:2257` (SSH user `shahzad`)
**Feature worktree:** `/home/shahzad/visa-tracker-worktrees/passport_extractor`, branch `feat/visa-tracker`
**Base HEAD:** `cbea2159cc189debd36bc69d661aee434396b4fc` (verified clean before starting)
**Corrective commit:** `3486fccd8fc8272f93ee97d049b951d201296cad` (local only; no push; environment-default Git identity; no `--author`)
**Dedicated test site:** `visa-tracker-test.localhost`
**Verdict:** `defect A fixed` / `defect B fixed` — suite improved 55 pass / 0 errors / 6 failures → **61 pass / 0 errors / 0 failures (61/61)**; pure tier **26/26** standalone.

---

## Root-cause restatement (from 09b, confirmed)

Both defects were localized to `passport_extractor/passport_extractor/ocr/image_preprocessor.py`:

1. **Defect A — rotation recovery crops non-square images.** `_preprocess_with_opencv` rotated with `cv2.warpAffine(..., (w, h))` — same-canvas rotation — so a 1200×400 image rotated 90°/270° kept only the central vertical band. Rotated documents could never yield a full 44-char MRZ line, defeating the mandated rotation recovery (TASK-003 §2.3).
2. **Defect B — CLAHE → median-blur chain degrades clean text.** On the already-legible synthetic fixture, the enhanced 0° variant yielded only ~20-char fragments instead of the full 44-char MRZ lines the raw image produces (raw reads at 0.995 confidence). `detect_mrz_candidates` found 0 candidates in all 4 variants and the pipeline correctly classified `Failed`/`NO_MRZ_FOUND`.

## Exact diffs summarized (commit `3486fccd`, 2 files, +56/−21)

### `passport_extractor/passport_extractor/ocr/image_preprocessor.py`

- **Defect A fix:** new helper `_rotate_expand(image, angle, cv2)` — computes the rotated bounding box from the rotation matrix (`new_w = h·|sin| + w·|cos|`, `new_h = h·|cos| + w·|sin|`), adjusts the translation so the full rotated content fits, and warpAffine's onto the expanded canvas. Same flags (`INTER_CUBIC`, `BORDER_REPLICATE`) and the same angle set `ROTATION_ANGLES = (0, 90, 180, 270)`; deskew logic untouched.
- **Defect B fix (option (a), per-angle form):** `_preprocess_with_opencv` now emits, for each rotation angle, the enhanced variant (grayscale → CLAHE → median blur → deskew) **followed by an unenhanced raw-grayscale variant** (no CLAHE, no blur, no deskew). The enhancement chain still serves degraded scans; clean input is no longer destroyed. 4 enhanced + 4 raw = 8 deterministic candidates, angle-major order. `_preprocess_with_pil` fallback updated identically (enhanced + raw grayscale per angle; PIL rotation already used `expand=True`).
- Docstrings updated to describe the new candidate set; no changes to the OCR engine, parser, service, or controller.

### `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py`

- `test_preprocess_image_returns_rotated_candidates`: exact-count assertion updated 4 → 8 (the candidate set grew by design; the assertion remains an exact-count check — strengthened, not weakened), and **new assertions added** that 90°/270° variants swap dimensions (`(200,100)` → `(100,200)`) while 0°/180° variants keep them — direct regression coverage for Defect A.
- No other test logic, fixture, or assertion was changed; no engine mocking; no fixture special-casing in app code.

## Test counts (reproducible, worktree-first `PYTHONPATH`, `bench --site visa-tracker-test.localhost run-tests ...`)

| Stage | Tests | Passed | Errors | Failures | Evidence label |
|-------|------:|-------:|-------:|---------:|----------------|
| Before (09b final, commit `cbea215`) | 61 | 55 | 0 | 6 | runtime-verified |
| Targeted re-run: `test_service_extracts_valid_synthetic_mrz` | 1 | 1 | 0 | 0 | runtime-verified |
| Targeted re-run: `test_corrupted_check_digit_needs_review`, `test_multi_page_pdf_finds_mrz_on_second_page` | 2 | 2 | 0 | 0 | runtime-verified |
| Targeted re-run: `test_rotated_synthetic_image_extracts` (90/180/270 subtests) | 1 | 1 | 0 | 0 | runtime-verified |
| **Full suite after fix (commit `3486fccd`)** | **61** | **61** | **0** | **0** | runtime-verified |

Full-suite result line: `Ran 61 tests in 264.060s — OK`. Log on the bench host (synthetic data only): `/tmp/vt_tests_after_09c.log`.

Pure/unit tier standalone (no site bound): `TestPassportExtractionUtils`, `TestMRZParser`, `TestImagePreprocessor`, `TestExtractionServiceCodes` — **26/26 OK** in 0.221s with worktree-first `PYTHONPATH` (runtime-verified).

## TASK-002 invariant re-verification (runtime-verified in the 61/61 suite)

- Audit-field immutability: `test_request_audit_is_server_owned_and_immutable`, `test_verified_audit_preserved_after_superseded`, `test_full_lifecycle_sets_timestamps_and_verified_audit` — pass.
- Retry bounds: `test_retry_count_bounds_enforced`, `test_retry_count_increments_from_failed_to_queued`, `test_retry_count_cannot_change_outside_retry_transition`, `test_retry_extraction_enforces_limit` — pass.
- Duplicate/supersession rules: all six duplicate/superseded tests — pass.
- Public-file rejection before byte access: `test_public_file_rejected_before_byte_access` — pass.

## Static gates

| Gate | Result | Evidence label |
|------|--------|----------------|
| `py_compile` on both changed files (bench Python 3.10) | Pass | source-wired |
| `git diff --check` | Pass (no whitespace errors) | source-wired |
| Scope of diff | Only `image_preprocessor.py` + its unit test; no engine/parser/service/controller changes | source-wired |

## Safety attestations

- Site `visaguy` was never targeted; original app checkouts and `processflo` untouched; all edits in the feature worktree only.
- Single local commit `3486fccd8fc8272f93ee97d049b951d201296cad` on `feat/visa-tracker`; worktree verified clean after commit; no push, no `--author`, no Git identity changes.
- No OCR engine mocking, no weakened assertions, no skipped tests, no fixture special-casing in app code.
- Synthetic data only; no secrets, PII, real passport data, or MRZ from real documents handled or stored.
- Redis services and the dedicated site left running/in place; task files not moved.

## Remaining issues / follow-ups

- None for TASK-003 preprocessing: suite target 61/61 reached and pure tier 26/26 holds. Per the contract, no forced-green measures were needed.
- Note: suite runtime grew (264s vs ~9s at the pre-OCR baseline) because all OCR integration tests now exercise the real engine across 8 variants per page — expected cost of genuine runtime verification, not a defect.
