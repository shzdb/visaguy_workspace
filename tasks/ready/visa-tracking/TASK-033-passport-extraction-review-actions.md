---
id: TASK-033
feature: FEAT-001
title: Retry, search and list view for Passport Extraction
status: ready
repository: passport_extractor
app_path: /home/shahzad/bench/apps/passport_extractor
owners: []
depends_on:
  - ADR-004
  - ADR-007
expected_files:
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.js
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction_list.js
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.json
created: 2026-09-28
updated: 2026-09-28
---

# TASK-033: Retry, search and list view for Passport Extraction

## Objective

Let staff retry a failed extraction and find extraction records, without a
developer. Verification stays automatic (ADR-007 amendment, 2026-09-28).

## Context

- `Passport Extraction.status` is `read_only` in the DocType, and the
  DocType has no form script and no whitelisted method.
- Owner decision D2 (2026-09-28): verification is always automatic. There
  is no manual verify step. So this task adds no Verify or Reject button.
  What happens to a `Needs Review` record is an open question (risk 46).
- The list has no list-view columns or filters.

## Required behaviour

1. **Retry extraction** button on a `Failed` record. It calls a whitelisted
   method that creates a new record with `triggered_by = "Retry"` and the
   same source, and enqueues it. It does not reuse the failed record.
   Permission: the caller must have create permission on Passport
   Extraction. The TASK-031 Process File action calls the same function
   after its own role check.
2. The form shows the passport file preview near the top for image and PDF
   files.
3. List view: status indicator colours, columns for status, confidence,
   error code, source document, requested on. Standard filters: status,
   error code.
4. Search fields: `passport_number_normalized`, `surname`, `given_names`,
   so support staff can find a client's record from the passport the
   client quotes.
5. Expiry warning: if `expiry_date` is before today, show a red note on the
   form.

## Constraints

- Keep the extractor independent: no import from `the_visaguy`, FileFlo,
  ProcessFlo or Lead (ADR-003).
- Do not show `mrz_line_*`, `raw_ocr_text` or `raw_extraction_result` to
  users without permlevel 1.
- Do not log passport values.

## Validation

- Tests for the retry method: a `Failed` record gets a new record; a
  record in another status is refused; a user without permission is
  refused.
- On-site: a retried extraction that ends `Extracted` is verified
  automatically and creates the tracking application.
- Desk check on an image and on a PDF extraction: preview, list filters,
  search by passport number.

## Definition of done

Validation passes and the commit SHA is recorded here.
