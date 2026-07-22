# TASK-003 Implementation Report — Passport OCR and MRZ Pipeline

**Date:** 2026-07-21
**Feature worktree:** `/home/shahzad/visa-tracker-worktrees/passport_extractor`
**Branch:** `feat/visa-tracker`
**Implementation commit SHA:** `a13fa3c`
**Correction commit SHA:** `034f1c1`
**TASK-003 verdict:** `runtime-blocked`

---

## Summary

Implemented the private-file OCR/MRZ pipeline for `passport_extractor` in the dedicated feature worktree. The pipeline validates private Frappe Files, renders PDF pages to images, preprocesses images with deterministic OpenCV operations, runs PaddleOCR lazily, detects and parses TD3 MRZ lines, validates ICAO 9303 check digits, computes a deterministic confidence score, classifies the result as `Extracted`, `Needs Review`, or `Failed`, and exposes a reusable service API plus a queue-ready worker entry point.

All changes were delivered via the mandatory patch-only method: a local staging clone was used to produce a unified diff, the diff was copied to the remote worktree, checked with `git apply --check`, applied, validated, and committed locally using the remote environment's existing Git identity. No edits occurred outside the feature worktree, no migration or tests ran on `visaguy`, no asset build ran, and no push was performed.

Runtime verification is deferred to TASK-010 because the dedicated test site `passport-extractor-test.localhost` cannot be created: `root_password` is absent from `/home/shahzad/bench/sites/common_site_config.json`.

---

## Changed files

| File | Purpose |
|------|---------|
| `passport_extractor/passport_extractor/ocr/__init__.py` | OCR sub-package marker (no heavy imports at module level) |
| `passport_extractor/passport_extractor/ocr/mrz_parser.py` | Pure TD3 MRZ detection, parsing, and ICAO 9303 check-digit validation |
| `passport_extractor/passport_extractor/ocr/image_preprocessor.py` | Lazy OpenCV/Numpy preprocessing with grayscale, CLAHE, median blur, deskew, and 0/90/180/270° rotations |
| `passport_extractor/passport_extractor/ocr/pdf_renderer.py` | Lazy PyMuPDF PDF-to-image rendering |
| `passport_extractor/passport_extractor/ocr/paddle_ocr_engine.py` | Lazy PaddleOCR singleton wrapper and version reporting |
| `passport_extractor/passport_extractor/services/__init__.py` | Service-layer package marker |
| `passport_extractor/passport_extractor/services/extraction_service.py` | Reusable service API: `run_ocr_pipeline`, `retry_extraction`, and pure helpers |
| `passport_extractor/passport_extractor/jobs.py` | Queue-ready idempotent worker `run_passport_extraction` for `frappe.enqueue` |
| `passport_extractor/passport_extractor/utils.py` | Extended with error-code constants, `MAX_FILE_SIZE_MB`, `EXTRACTION_RETRY_LIMIT`, `ALLOWED_EXTENSIONS`, and `validate_passport_file_format` |
| `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py` | Pure `TestMRZParser`/`TestImagePreprocessor` unit tests and deferred `TestPassportExtractionPipeline` integration tests |

No scaffold files (`pyproject.toml`, `README.md`, `license.txt`, top-level `__init__.py`, or `hooks.py`) were modified.

---

## Static validation gates

All static checks passed before commit.

| Gate | Result | Evidence label |
|------|--------|----------------|
| `git diff --check` | Pass (no whitespace errors) | source-wired |
| JSON parse — all `.json` files in app | Pass | present |
| Python compile — all changed `.py` files (bench Python 3.10) | Pass | source-wired |
| Module resolution with worktree-first `PYTHONPATH` | Pass (`passport_extractor.__file__` resolves inside feature worktree) | source-wired |
| Lazy CV/OCR import check — request-loaded modules | Pass (`fitz`, `paddle`, `paddleocr`, `cv2`, `numpy` not loaded on import of `utils`, controller, `services`, `jobs`) | source-wired |
| Forbidden dependency scan | Pass — no references to `the_visaguy`, `fileflo`, `processflo`, `Lead`, `Customer`, `Visa Tracking Application`, `PF Process File`, or `FF File Collection` | source-wired |
| PII/error-message review | Pass — `error_message` assignments contain no MRZ text, passport numbers, file paths, or raw OCR output | source-wired |
| Pure unit tests (`TestMRZParser`, `TestImagePreprocessor`) | Pass — 9 tests with worktree-first `PYTHONPATH`, no site required | source-wired |
| `ruff` | Not available on the bench; no tools installed | configured-unverified |

### Error-code constants

Stable, PII-free error codes added to `utils.py`:

- `UNSUPPORTED_FILE_TYPE`
- `FILE_TOO_LARGE`
- `PASSWORD_PROTECTED_PDF`
- `FILE_READ_ERROR`
- `OCR_ENGINE_ERROR`
- `NO_MRZ_FOUND`
- `CHECK_DIGIT_FAILURE`
- `LOW_CONFIDENCE`

---

## Runtime validation gates

| Gate | Result | Evidence label |
|------|--------|----------------|
| Dedicated test site exists | `passport-extractor-test.localhost` does **not** exist | runtime-verified |
| `root_password` configured in `common_site_config.json` | **No** — the key is absent | configured-unverified |
| Test-site creation | Blocked by missing `root_password` | — |
| `bench --site passport-extractor-test.localhost migrate` | Not run (site cannot be created) | — |
| `bench --site passport-extractor-test.localhost run-tests --app passport_extractor` | Not run (site cannot be created) | — |
| Migration/tests on `visaguy` | Not performed (explicitly excluded) | — |

### Exact blocker

Dedicated-site runtime verification is blocked because the bench's `common_site_config.json` does **not** contain a `root_password` key. Without it, `bench new-site passport-extractor-test.localhost` cannot create the isolated test database, and therefore migration and the full app test suite (including synthetic OCR integration tests) cannot be executed. No password value was requested, printed, copied, or exposed.

---

## Implementation notes

- **Lazy imports:** `fitz`, `cv2`, `numpy`, and `paddleocr` are imported only inside worker functions. Request-loaded modules (`utils`, controller, `services/__init__`, `jobs` top level) do not load them.
- **Private-file validation:** `validate_passport_file_format()` reuses the TASK-002 `validate_passport_file()` seam, checks extension against `ALLOWED_EXTENSIONS`, enforces `MAX_FILE_SIZE_MB`, and detects password-protected PDFs before any byte access.
- **File hashing:** `compute_file_hash()` is invoked after the privacy/format checks pass and stores the SHA-256 digest on the record.
- **PDF rendering:** PyMuPDF renders pages sequentially at 200 DPI; the pipeline stops at the first page producing a valid MRZ with confidence at or above `CONFIDENCE_OK_THRESHOLD`.
- **MRZ parsing:** Pure deterministic functions parse TD3 lines, correct common OCR misreads (`0/O`, `1/I`, `5/S`) within digit/letter fields, validate all five ICAO 9303 check digits, and compute `mrz_valid`.
- **Confidence and thresholds:** Confidence is the mean PaddleOCR score for the two MRZ lines, normalized to 0–100. Thresholds default to `CONFIDENCE_OK_THRESHOLD = 75.0` and `CONFIDENCE_REVIEW_THRESHOLD = 50.0` until `Visa Tracker Settings` is available.
- **Classification:** Terminal states are set through the document controller so transition rules and timestamps are enforced; `requires_review` is true only for `Needs Review`.
- **Redaction:** `error_message` is always generic; raw OCR/MRZ/output is written only to permission-level-1 fields.
- **Worker idempotency:** `run_passport_extraction()` returns silently if the record is not `Queued`, transitions to `Processing` through the controller, runs the pipeline, and captures unhandled failures without re-raising (no automatic retry).
- **Bounded retry:** `retry_extraction()` validates `Failed` status and `retry_count < EXTRACTION_RETRY_LIMIT` (2) before transitioning back to `Queued`; the controller increments `retry_count`.
- **Tests:** `TestMRZParser` and `TestImagePreprocessor` run without a site. Synthetic image/PDF-based integration tests are written under `TestPassportExtractionPipeline` and await the dedicated test site.

---

## Correction — harden MRZ and extraction error handling

A follow-up commit (`034f1c1`) addressed the reviewed defects without migrating or testing on `visaguy`, without pushing, and without broadening scope.

### Defects fixed

| # | File | Fix |
|---|------|-----|
| 1 | `passport_extractor/passport_extractor/services/extraction_service.py` | Imported and preserved `FILE_TOO_LARGE` and `PASSWORD_PROTECTED_PDF` as known stable error codes with generic redacted messages instead of mapping them to `OCR_ENGINE_ERROR`. |
| 2 | `passport_extractor/passport_extractor/ocr/mrz_parser.py` | Added `_parse_check_digit()` to safely evaluate OCR-supplied check characters; malformed characters and the ICAO filler `<` now yield `None`, which sets the corresponding validation flag to `False` instead of raising `ValueError`. `_correct_field()` now uses the same safe helper. |
| 3 | `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py` | Added pure synthetic unit tests covering malformed passport/DOB/expiry/composite check digits, filler optional-data check digits, and service error-code/message coverage without a site. |

### Correction validation gates

| Gate | Result | Evidence label |
|------|--------|----------------|
| `git apply --check -p0` on local unified patch | Pass | source-wired |
| `git diff --check` | Pass (no whitespace errors) | source-wired |
| Python compile — changed `.py` files (bench Python 3.10) | Pass | source-wired |
| Lazy CV/OCR import check — request-loaded modules | Pass (`fitz`, `paddle`, `paddleocr`, `cv2`, `numpy` not loaded on import of `utils`, controller, `services`, `jobs`) | source-wired |
| Forbidden dependency scan | Pass — no references to `the_visaguy`, `fileflo`, `processflo`, `Lead`, `Customer`, `Visa Tracking Application`, `PF Process File`, or `FF File Collection` | source-wired |
| Pure unit tests | Pass — 26 tests (`TestPassportExtractionUtils`, `TestMRZParser`, `TestImagePreprocessor`, `TestExtractionServiceCodes`) with worktree-first `PYTHONPATH`, no site required | runtime-verified |

---

## Verdict

**TASK-003 is `runtime-blocked`**, not incomplete. Static implementation and validation are finished and committed locally on `feat/visa-tracker` at `a13fa3c`, with reviewed-defect corrections committed at `034f1c1`. Runtime verification (dedicated test-site migration and full integration test execution) is blocked solely by the missing `root_password` configuration, which prevents safe test-site creation. No credentials were requested or exposed.
