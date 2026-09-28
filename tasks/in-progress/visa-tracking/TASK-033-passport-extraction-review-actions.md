---
id: TASK-033
feature: FEAT-001
title: Needs Review verification, retry, search and list view for Passport Extraction
status: in-progress
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

# TASK-033: Needs Review verification, retry, search and list view for Passport Extraction

## Objective

Let staff verify a `Needs Review` extraction, retry a failed one, and find
extraction records, without a developer. All other verification stays
automatic (ADR-007 amendment, 2026-09-28).

## Context

- `Passport Extraction.status` is `read_only` in the DocType, and the
  DocType has no form script and no whitelisted method.
- Owner decision D2 (2026-09-28): verification is automatic, with one
  exception: a person may correct and verify a `Needs Review` record.
  Roles: `Operations Associate`, `Operations Team Lead`. No Reject action.
  Without this, a `Needs Review` record never creates tracking (risk 46).
- The list has no list-view columns or filters.

## Required behaviour

1. **Verify** button, only on a `Needs Review` record. It opens a dialog
   with the file preview beside the passport number, date of birth, surname,
   given names, nationality and expiry date, filled with the extracted
   values. The user corrects them if needed and confirms. The method:
   - refuses any status other than `Needs Review`;
   - refuses a user without write permission on Passport Extraction (the
     roles are granted in TASK-034);
   - requires passport number and date of birth;
   - saves the values, sets `status = Verified`, `verified_by`,
     `verified_on`, and records in `verification_notes` that the values
     were checked by hand, and whether any were changed;
   - saves through the normal document save, so the `the_visaguy`
     `on_update` hook creates the tracking application.
   No Reject button. `Extracted` records get no Verify button: they are
   verified automatically.
2. **Retry extraction** button on a `Failed` record. It calls a whitelisted
   method that creates a new record with `triggered_by = "Retry"` and the
   same source, and enqueues it. It does not reuse the failed record.
   Permission: the caller must have create permission on Passport
   Extraction. The TASK-031 Process File action calls the same function
   after its own role check.
3. The form shows the passport file preview near the top for image and PDF
   files.
4. List view: status indicator colours, columns for status, confidence,
   error code, source document, requested on. Standard filters: status,
   error code.
5. Search fields: `passport_number_normalized`, `surname`, `given_names`,
   so support staff can find a client's record from the passport the
   client quotes.
6. Expiry warning: if `expiry_date` is before today, show a red note on the
   form.

## Constraints

- Keep the extractor independent: no import from `the_visaguy`, FileFlo,
  ProcessFlo or Lead (ADR-003).
- Do not show `mrz_line_*`, `raw_ocr_text` or `raw_extraction_result` to
  users without permlevel 1.
- Do not log passport values.

## Validation

- Tests for the verify method: `Needs Review` is verified with corrected
  values; `Extracted`, `Failed` and `Verified` are refused; a user without
  write permission is refused; missing passport number or DOB is refused;
  the audit fields are set.
- On-site: verifying a `Needs Review` record creates the tracking
  application through the existing hook, and the public lookup works with
  the corrected values.
- Tests for the retry method: a `Failed` record gets a new record; a
  record in another status is refused; a user without permission is
  refused.
- On-site: a retried extraction that ends `Extracted` is verified
  automatically and creates the tracking application.
- Desk check on an image and on a PDF extraction: preview, list filters,
  search by passport number.

## Definition of done

Validation passes and the commit SHA is recorded here.

## Implementation (2026-09-28)

Branch `feat/visa-tracker` in `passport_extractor` on the bench (installed checkout), commits `2a00d00`, merged `fa97752`, test fix `84da2fe`. Not pushed, not deployed.
Built by Cursor executors, reviewed and merged by the orchestrator; records in
`ongoing/visa-tracking-soft-launch/`.

Evidence: 25 pure tests; on-site suite 98 OK; smoke test verified a Needs Review record through the normal save and the tracking hook. Full suites on `visa-tracker-test.localhost` after all merges: `the_visaguy` 638 OK, `passport_extractor` 98 OK (`--skip-test-records`).

## What remains

1. Owner migrates and tests `visaguy` (never run by Claude; see memory rule).
2. Browser check of the desk UI.
3. Push and deploy (owner).
