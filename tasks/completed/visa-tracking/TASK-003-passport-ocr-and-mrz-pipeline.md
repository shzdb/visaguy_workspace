---
id: TASK-003
feature: FEAT-001
title: PaddleOCR and MRZ extraction pipeline
status: completed
repository: passport_extractor
owners: []
depends_on:
  - TASK-002
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# PaddleOCR and MRZ extraction pipeline

## Objective

Extract passport number and date of birth from an uploaded passport using local PaddleOCR and TD3 MRZ parsing with check-digit validation, entirely inside a background worker.

## Required behaviour

The long-queue extraction worker must: mark Processing; resolve the private file safely; render PDF pages as images where needed; perform orientation, cropping, and preprocessing; run PaddleOCR; detect TD3 MRZ candidates; parse values and check digits; store the raw result and reviewed-value candidates; classify the record as Extracted, Needs Review, or Failed; avoid logging raw passport details; and keep retry behaviour bounded and auditable.

## Constraints

- No passport file or passport data may be sent to an external OCR service or LLM.
- OCR must never run in a web request.
- Low-confidence or check-digit-invalid results must require review.

## Validation

- A valid passport scan yields parsed MRZ values and stored check digits.
- A rotated, blurred, or MRZ-less image is classified rather than crashing.
- Logs contain no raw passport values.

## Definition of done

The pipeline classifies every input into Extracted, Needs Review, or Failed without leaking passport data.

## Implementation evidence

Repository `tridz-dev/passport_extractor`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `a13fa3c` | 2026-07-21 | feat: add passport OCR and MRZ pipeline |
| `034f1c1` | 2026-07-21 | fix: harden MRZ and extraction error handling |
| `cbea215` | 2026-07-22 | Fix audit datetime comparison, repair pipeline test fixtures, PaddleOCR 3.x compat |
| `3486fcc` | 2026-07-22 | Fix OCR preprocessing: canvas-expanding rotation and raw-image candidates |
| `0216829` | 2026-07-22 | fix: accept state-specific MRZ document subtypes |

Modules: `ocr/paddle_ocr_engine.py`, `ocr/mrz_parser.py`, `ocr/image_preprocessor.py`, `ocr/pdf_renderer.py`, `services/extraction_service.py` (317 lines), `jobs.py`.

Total app size at `0216829`: 14 files, 2,803 insertions.

## Known limitations

PaddleOCR model-file availability to production workers is not yet verified. Per the feature document's dependency list, extraction cannot be called **runtime-verified** until a live OCR run succeeds on the target bench. Current label: **source-wired**.
