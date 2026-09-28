---
id: TASK-033
feature: FEAT-001
title: Review actions on Passport Extraction (verify, reject, retry)
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

# TASK-033: Review actions on Passport Extraction (verify, reject, retry)

## Objective

Give reviewers a desk path to verify, reject or retry an extraction. Today
there is none.

## Context

- `Passport Extraction.status` is `read_only` in the DocType, and the
  DocType has no form script and no whitelisted method. A reviewer cannot
  move a record from `Extracted` or `Needs Review` to `Verified` in the desk
  (risk 46).
- With `require_manual_verification` set (the ADR-007 production
  recommendation), no application is ever created without this.
- Every `Needs Review` record is stuck the same way, whatever the setting.
- The allowed transitions are already defined in
  `passport_extractor.utils` (`Extracted → Verified | Needs Review |
  Duplicate`, `Needs Review → Verified | Rejected | Duplicate`).
- The list has no list-view columns or filters.

## Required behaviour

1. Form buttons, shown only for the allowed transitions and for users with
   write permission:
   - **Verify**: opens a dialog that shows the passport values (number,
     DOB, names, nationality, expiry) and the file preview. The reviewer can
     correct the values, then confirms. Sets `status = Verified`,
     `verified_by`, `verified_on`, optional `verification_notes`.
   - **Reject**: needs a note. Sets `status = Rejected`.
   - **Mark duplicate**: asks for `duplicate_of`.
   - **Retry extraction**: for `Failed`. Creates a new record with
     `triggered_by = "Retry"` and the same source. It does not reuse the
     failed record.
2. Each button calls a whitelisted method that checks the permission and
   the transition on the server. The method runs the change through the
   normal save, so the `the_visaguy` `on_update` hook still creates the
   tracking application.
3. The form shows the passport file preview near the top for image and PDF
   files.
4. List view: status indicator colours, columns for status, confidence,
   error code, source document, requested on. Standard filters: status,
   error code.
5. Search fields: `passport_number_normalized`, `surname`, `given_names`,
   so support staff can find a client's record from the passport the
   client quotes. The fields stay permlevel 0 as now.
6. Expiry warning: if `expiry_date` is before today, show a red note on the
   form. Do not block verification.

## Constraints

- Keep the extractor independent: no import from `the_visaguy`, FileFlo,
  ProcessFlo or Lead (ADR-003).
- Do not show `mrz_line_*`, `raw_ocr_text` or `raw_extraction_result` to
  users without permlevel 1.
- Do not log passport values.

## Validation

- Tests for each method: allowed transition, refused transition, user
  without permission, verification audit fields set.
- On-site: verifying a `Needs Review` record creates the tracking
  application through the existing hook.
- Desk check by a reviewer on an image and on a PDF extraction.

## Definition of done

Validation passes and the commit SHA is recorded here.
