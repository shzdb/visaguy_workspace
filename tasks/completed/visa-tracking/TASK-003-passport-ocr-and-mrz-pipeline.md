---
id: TASK-003
feature: FEAT-001
title: Passport OCR and MRZ pipeline
status: completed
repository: passport_extractor
worktree: /home/shahzad/visa-tracker-worktrees/passport_extractor
owners: []
depends_on:
  - TASK-002
  - ADR-004
expected_files:
  - passport_extractor/passport_extractor/ocr/__init__.py
  - passport_extractor/passport_extractor/ocr/pdf_renderer.py
  - passport_extractor/passport_extractor/ocr/image_preprocessor.py
  - passport_extractor/passport_extractor/ocr/mrz_parser.py
  - passport_extractor/passport_extractor/ocr/paddle_ocr_engine.py
  - passport_extractor/passport_extractor/services/__init__.py
  - passport_extractor/passport_extractor/services/extraction_service.py
  - passport_extractor/passport_extractor/jobs.py
  - passport_extractor/passport_extractor/utils.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py
created: 2026-07-21
updated: 2026-07-21
---

# TASK-003: Passport OCR and MRZ pipeline

## Objective

Implement the private-file OCR/MRZ pipeline inside the `passport_extractor` feature worktree. The pipeline must load supported passport files, render PDF pages to images, preprocess images, run PaddleOCR, detect and parse TD3 MRZ lines, validate ICAO check digits, compute a deterministic confidence score, classify the result as `Extracted`, `Needs Review`, or `Failed`, store raw output in restricted private fields, and expose a reusable service API plus a queue-ready worker entry point.

This task covers only the `passport_extractor` side of the long-running extraction worker. It explicitly excludes FileFlo event handling, Visa Tracker Settings inspection, Lead/Customer/PF Process File lifecycle, tracking DocTypes, and public APIs.

## Context

FEAT-001 splits passport processing across repositories per ADR-003 and ADR-004. `passport_extractor` owns the extraction pipeline; `the_visaguy` owns the decision to treat a FileFlo field as a passport and the orchestration that creates and enqueues a `Passport Extraction` record.

TASK-002 delivered the `Passport Extraction` DocType, controller transitions, permissions, and safe file-reference seams in `/home/shahzad/visa-tracker-worktrees/passport_extractor` on branch `feat/visa-tracker`. TASK-003 builds the OCR/MRZ layer on top of those seams.

The target bench already has PaddlePaddle 3.2.0 and PaddleOCR available. PyMuPDF, OpenCV headless, and Pillow must be used only inside the worker path so that importing the `passport_extractor` module in request processes remains lightweight.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `ongoing/visa-tracking-implementation/05b-task-002-implementation.md`
- Feature worktree: `/home/shahzad/visa-tracker-worktrees/passport_extractor` (branch `feat/visa-tracker`)
- Bench Python 3.10 environment with PaddleOCR/PaddlePaddle, PyMuPDF, OpenCV, Pillow
- Dedicated test site: `passport-extractor-test.localhost` — runtime verification is deferred until TASK-010 unblocks test-site creation

## Scope

### Included

- Private file validation, loading, and hashing.
- PDF rendering to images and image preprocessing.
- Lazy PaddleOCR invocation inside the worker.
- TD3 MRZ detection, parsing, and ICAO check-digit validation.
- Deterministic confidence calculation and review thresholds.
- Extraction status classification (`Extracted`, `Needs Review`, `Failed`).
- Redacted, PII-free error codes and messages.
- Reusable Python service API for the pipeline.
- Queue-ready worker entry point callable via `frappe.enqueue`.
- Deterministic synthetic unit and integration tests.

### Excluded

- FileFlo field-ID matching or post-save event handlers (TASK-004).
- `Visa Tracker Settings` reads or business rules (TASK-005).
- Lead, Customer, `PF Process File`, or `Visa Tracking Application` logic (TASK-006).
- Public verification/status APIs (TASK-007).
- Frontend work of any kind (TASK-008/TASK-009).
- Production migration, rollout, or end-to-end verification (TASK-010).
- Runtime verification that requires creating or migrating a Frappe site; this is deferred to TASK-010 because test-site creation is blocked by the missing `root_password` configuration.

## Required behaviour

### 1. Private file loading and format validation

1.1. Reuse the `validate_passport_file()` seam from TASK-002. Reject the request if the referenced `File` does not exist or `is_private != 1`.

1.2. Resolve the absolute file path through Frappe's `File.get_full_path()` API. Do not construct paths from `file_url` manually.

1.3. Enforce a supported-extension allow list: `pdf`, `jpg`, `jpeg`, `png`. Reject unsupported extensions with a stable error code.

1.4. Enforce a maximum file size. Use a module constant `MAX_FILE_SIZE_MB` defaulting to `10` until `Visa Tracker Settings` becomes available in TASK-005.

1.5. Reject password-protected PDFs with a stable error code.

1.6. Compute or refresh `file_hash` using the chunked SHA-256 seam from TASK-002 after the privacy check passes. Store the hash on the `Passport Extraction` record.

### 2. PDF rendering and image preprocessing

2.1. Use PyMuPDF (`fitz`) to render PDF pages to RGB PIL images. Process pages sequentially; stop at the first page that yields a valid MRZ result satisfying the extraction threshold.

2.2. For direct image uploads, open with Pillow and convert to RGB if needed.

2.3. Preprocessing must be deterministic and headless. Apply the following steps in order, with each step guarded so a failure in one step does not crash the pipeline:

- Convert to grayscale.
- Normalize contrast (for example, CLAHE or histogram equalization).
- Mild noise reduction (for example, median blur).
- Optional deskew using contour or projection-profile methods.
- Rotation recovery: try 0°, 90°, 180°, and 270° and keep the orientation that produces the best MRZ candidate.

2.4. Keep original raw file bytes out of logs and error messages.

### 3. OCR engine wrapper

3.1. Import `paddleocr.PaddleOCR` lazily inside the worker or service function. Do not import PaddleOCR at module top level in files that may be loaded by the request process.

3.2. Initialize PaddleOCR with English language, angle classification enabled, and logging suppressed in production:

```python
PaddleOCR(
    lang="en",
    use_angle_cls=True,
    show_log=False,
    # deterministic, headless defaults
)
```

3.3. Run OCR on each preprocessed image (or each rotation variant). Return a list of text lines with confidence scores.

3.4. If OCR raises an exception, catch it, set status `Failed`, record a redacted `OCR_ENGINE_ERROR` code, and do not leak the exception message.

### 4. TD3 MRZ detection and parsing

4.1. Detect TD3 MRZ candidates from OCR text lines. A valid candidate consists of two consecutive lines, each 44 characters long, drawn from the ICAO 9303 character set (`A-Z`, `0-9`, `<`), with the first line starting with `P<` or an allowed document-type prefix for passports.

4.2. Clean OCR artifacts by stripping spaces and mapping common misreads (`0`/`O`, `1`/`I`, `5`/`S`) only where the MRZ format allows ambiguity. Do not permanently overwrite the raw OCR text.

4.3. Parse the MRZ into the fields required by the `Passport Extraction` DocType:

- `document_type`
- `issuing_country`
- `surname`
- `given_names`
- `passport_number` and `passport_number_normalized`
- `nationality`
- `date_of_birth`
- `sex`
- `expiry_date`
- `personal_number`

4.4. Compute and store ICAO 9303 check digits for:

- `passport_number_check_valid`
- `date_of_birth_check_valid`
- `expiry_date_check_valid`
- `personal_number_check_valid`
- `composite_check_valid`

Set `mrz_valid` to true only when all five check digits are valid.

4.5. Store the detected `mrz_line_1` and `mrz_line_2` values on the record. These fields are permission level 1 per TASK-002 and must never appear in error messages or logs.

### 5. Confidence scoring and review thresholds

5.1. Define confidence algorithmically from the OCR engine output for the detected MRZ lines. A valid approach is the mean of the PaddleOCR confidence scores for the two MRZ lines, normalized to a 0–100 percent scale.

5.2. Use module constants for thresholds until `Visa Tracker Settings` is available:

- `CONFIDENCE_OK_THRESHOLD`: default `75.0` (%)
- `CONFIDENCE_REVIEW_THRESHOLD`: default `50.0` (%)

5.3. Classify the terminal OCR result as follows:

- `Extracted` when:
  - a TD3 MRZ is detected,
  - `mrz_valid` is true,
  - required fields (`passport_number`, `date_of_birth`, `expiry_date`, `nationality`) are present,
  - confidence is at or above `CONFIDENCE_OK_THRESHOLD`.
- `Needs Review` when:
  - a TD3 MRZ is detected but `mrz_valid` is false, or
  - required fields are missing, or
  - confidence is below `CONFIDENCE_OK_THRESHOLD`, or
  - `personal_number_check_valid` is false but other checks pass (optional field inconsistency).
- `Failed` when:
  - no MRZ candidate is found after all pages, rotations, and preprocessing attempts, or
  - the file cannot be read/rendered, or
  - the OCR engine fails.

5.4. Set `requires_review` to true for `Needs Review` and false for `Extracted` and `Failed`.

5.5. Set `processing_completed_on` when entering any terminal OCR state (`Extracted`, `Needs Review`, `Failed`).

### 6. Redacted failures

6.1. Error codes must be stable, countable strings such as:

- `UNSUPPORTED_FILE_TYPE`
- `FILE_TOO_LARGE`
- `PASSWORD_PROTECTED_PDF`
- `FILE_READ_ERROR`
- `OCR_ENGINE_ERROR`
- `NO_MRZ_FOUND`
- `CHECK_DIGIT_FAILURE`
- `LOW_CONFIDENCE`

6.2. `error_message` must be generic and must not contain any of the following:

- passport numbers,
- dates of birth,
- MRZ text,
- raw OCR output,
- file paths,
- exception tracebacks,
- any other PII.

6.3. Raw OCR text and raw extraction results must still be written to `raw_ocr_text` and `raw_extraction_result` so operators can diagnose failures during review. These fields remain permission level 1.

### 7. Reusable service API

7.1. Provide `passport_extractor/services/extraction_service.py` with at least these functions:

- `run_ocr_pipeline(passport_extraction_name: str) -> None`
  - Loads the record, validates the private file, runs the full pipeline, classifies the result, and saves the document through the controller so transition rules are enforced.
- `retry_extraction(passport_extraction_name: str) -> None`
  - Validates that the record is in `Failed` status and that `retry_count` is below `EXTRACTION_RETRY_LIMIT` (default 2), transitions it to `Queued`, and increments `retry_count` through the controller.
- Pure helper functions for reuse and testing:
  - `parse_td3_mrz(line1: str, line2: str) -> dict`
  - `compute_icao_check_digit(value: str) -> int`
  - `preprocess_image(image) -> list` (returns candidate images/rotations)

7.2. The service must not import from `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, or `Visa Tracking Application`.

### 8. Worker behaviour

8.1. Provide `passport_extractor/jobs.py` with a queue-ready function:

```python
def run_passport_extraction(passport_extraction_name: str):
    run_ocr_pipeline(passport_extraction_name)
```

8.2. The worker function must be enqueueable from `the_visaguy` using `frappe.enqueue`:

```python
frappe.enqueue(
    "passport_extractor.jobs.run_passport_extraction",
    queue="long",
    passport_extraction_name=pex_name,
)
```

8.3. On entry, if the record status is not `Queued`, log an idempotency message and return without reprocessing.

8.4. Transition the record to `Processing` and set `processing_started_on`, `extraction_engine` (`PaddleOCR`), and `engine_version` (PaddleOCR/PaddlePaddle version strings).

8.5. Run the pipeline. On success, set the classified terminal state and `processing_completed_on`. On unhandled exception, set `Failed` with a redacted error and `processing_completed_on`.

8.6. The worker must not automatically retry failed jobs. Bounded retry is triggered explicitly through `retry_extraction` by the orchestrator (TASK-004/TASK-006).

### 9. Deterministic synthetic tests

9.1. Generate synthetic passport images at test time using Pillow. Each fixture must use an obviously fake MRZ string (for example, `P<UTOFAKE<<NAME<<<<<<<<<<<<<<<<<<<<<<<`, `A12345678<7UTO8601011M2301015<<<<<<<<<<<<<<02`).

9.2. Cover the following scenarios:

- Valid TD3 MRZ on a clean synthetic image → `Extracted`, all check digits valid.
- Rotated image (90°, 180°, 270°) → still parses correctly.
- Low-resolution or noisy image → may drop below threshold and classify `Needs Review`.
- Corrupted MRZ check digit → `Needs Review` with `mrz_valid = false`.
- Multi-page PDF fixture with MRZ on page 2 → finds MRZ and stops.
- Unsupported file type → stable error code.
- Public file reference → rejected before byte access.
- Missing MRZ image → `Failed` with `NO_MRZ_FOUND`.
- Redaction: assert `error_message` does not contain MRZ text, passport number, or file path.

9.3. Keep pure-function tests (MRZ parser, check-digit computation, preprocessing helpers) runnable without a Frappe site. Integration tests that create `Passport Extraction` records through Frappe are written and statically reviewed but execution is deferred to TASK-010.

9.4. Never commit real passport images, MRZ strings from real documents, or production PII.

## Constraints

- Work only in `/home/shahzad/visa-tracker-worktrees/passport_extractor`. Do not modify original repository checkouts.
- Do not import from or reference `the_visaguy`, `fileflo`, `processflo`, `erpnext.crm.doctype.lead`, Lead, Customer, `PF Process File`, `FF File Collection`, or `Visa Tracking Application`.
- Do not implement FileFlo event handlers, Visa Tracker Settings access, or public APIs.
- Do not run migrations or tests on the `visaguy` production-like site.
- Do not push to any Git remote.
- Do not commit secrets, production data, real passport samples, or sensitive raw data.
- Keep heavy CV/OCR imports lazy; module-level imports of PaddleOCR, PyMuPDF, or OpenCV in request-loaded files are prohibited.

## Expected changes

- `passport_extractor/passport_extractor/ocr/__init__.py`
- `passport_extractor/passport_extractor/ocr/pdf_renderer.py`
- `passport_extractor/passport_extractor/ocr/image_preprocessor.py`
- `passport_extractor/passport_extractor/ocr/mrz_parser.py`
- `passport_extractor/passport_extractor/ocr/paddle_ocr_engine.py`
- `passport_extractor/passport_extractor/services/__init__.py`
- `passport_extractor/passport_extractor/services/extraction_service.py`
- `passport_extractor/passport_extractor/jobs.py`
- `passport_extractor/passport_extractor/utils.py` (extended with hashing/format helpers if needed)
- `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py` (extended with synthetic OCR/MRZ tests)

## Validation

### Static validation (required now)

- [ ] All new `.py` files compile with the bench Python environment (`python -m py_compile <file>`).
- [ ] `PYTHONPATH=/home/shahzad/visa-tracker-worktrees/passport_extractor` resolves `passport_extractor.__file__` inside the feature worktree.
- [ ] Module-level imports of PaddleOCR, PyMuPDF, or OpenCV do not exist in request-loaded modules (controller, `utils`, `services/__init__`, `jobs` top level).
- [ ] Forbidden dependency scan passes: no references to `the_visaguy`, `fileflo`, `processflo`, `Lead`, `Customer`, `PF Process File`, `FF File Collection`, or `Visa Tracking Application`.
- [ ] Pure-function unit tests for MRZ parsing and check-digit computation run successfully with the worktree-first `PYTHONPATH` and do not require a Frappe site.
- [ ] Synthetic fixture generation runs without real passport data and produces deterministic images.
- [ ] `error_message` strings are reviewed to confirm they contain no MRZ text, passport numbers, file paths, or raw OCR output.
- [ ] `git diff --check` passes (no whitespace errors).

### Runtime validation (deferred to TASK-010)

- [ ] Dedicated test site `passport-extractor-test.localhost` is created and migrated once `root_password` is configured and safe test-site creation is unblocked.
- [ ] `bench --site passport-extractor-test.localhost migrate` succeeds with the new code.
- [ ] `bench --site passport-extractor-test.localhost run-tests --app passport_extractor` passes all new synthetic integration tests.
- [ ] No migration or test is run on the `visaguy` site.

## Definition of done

- The OCR/MRZ pipeline is implemented entirely inside `/home/shahzad/visa-tracker-worktrees/passport_extractor` and committed locally on `feat/visa-tracker`.
- Private file validation, PDF rendering, image preprocessing, PaddleOCR invocation, TD3 MRZ parsing, check-digit validation, confidence scoring, review thresholds, and redacted failures are all in place.
- A reusable service API and queue-ready worker entry point are available for `the_visaguy` to enqueue.
- Static validation gates pass; pure-function tests pass.
- Integration tests and full-site runtime validation are written and ready to execute as soon as the dedicated test site is unblocked in TASK-010.
- No dependency leak to FileFlo, ProcessFlo, Lead, Customer, or VisaGuy tracking logic exists.
- No migration, test, or modification is performed on the `visaguy` site.
- No secrets, PII, real passport samples, or raw production data are committed.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Missing OCR runtime**: PaddleOCR, PaddlePaddle, PyMuPDF, OpenCV, or Pillow cannot be imported in the bench worker environment.
2. **Dependency leak**: the required behaviour forces an import, Link field, or hardcoded reference to a forbidden app or DocType.
3. **DocType schema mismatch**: the existing `Passport Extraction` schema from TASK-002 lacks fields required for the pipeline output.
4. **Missing architecture decision**: an implementation question arises that is not answered by FEAT-001, ADR-004, or `01-architecture-and-data-model.md`.
5. **Permission denial**: any required repository, bench, or worktree operation is denied by host policy or user approval.
6. **Unsafe test-site demand**: a stakeholder requires running migrations or tests on `visaguy` instead of a dedicated isolated test site.

## Completion evidence

- Implementation commit: `a13fa3cdcafca0377561886513b12a62ed407deb`.
- Corrective review commit: `034f1c17bc872fe8ebcd8f55df797b6c401e7eb1`.
- Twenty-six pure tests and all static compile/import/dependency/redaction gates pass.
- Dedicated-site migration, OCR runtime, worker, and Frappe integration tests remain deferred to TASK-010; `visaguy` was not migrated or tested.
- Evidence: `ongoing/visa-tracking-implementation/07a-task-003-implementation.md`.
