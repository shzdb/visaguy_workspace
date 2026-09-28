---
id: TASK-037
feature: FEAT-001
title: Clear message for unsupported passport file types (HEIC)
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-031
  - TASK-035
expected_files:
  - the_visaguy/visa_tracking/utils/constants.py
  - the_visaguy/visa_tracking/services/ensure_service.py
  - the_visaguy/visa_tracking/api/desk.py
  - the_visaguy/the_visa_guy/report/visa_tracking_coverage/visa_tracking_coverage.py
created: 2026-09-28
updated: 2026-09-28
---

# TASK-037: Clear message for unsupported passport file types (HEIC)

## Objective

When a passport extraction failed because the file type is not supported
(for example HEIC from an iPhone), tell staff exactly what to do. HEIC
support itself is out of scope (owner, 2026-09-28).

## Context

- `passport_extractor` accepts pdf, jpg, jpeg, png only. A HEIC file ends
  `Failed` with `error_code = "UNSUPPORTED_FILE_TYPE"`
  (`passport_extractor.passport_extractor.utils.UNSUPPORTED_FILE_TYPE`).
- Today `ensure_tracking` returns `extraction_failed`, whose message says
  "Use Retry passport extraction, or ask for a clearer upload". Retry cannot
  help: the same file fails again.
- About 1 in 6,000 passport files is HEIC.

## Required behaviour

1. New outcome code `unsupported_file_type` (`ENSURE_OUTCOME_UNSUPPORTED_FILE_TYPE`),
   added to `ENSURE_OUTCOMES`.
2. `ensure_tracking` (and its diagnose mode): when the outcome would be
   `extraction_failed` and the latest extraction of a failed passport row
   has `error_code = "UNSUPPORTED_FILE_TYPE"`, return
   `unsupported_file_type` instead. Read the error code with one query; do
   not import `passport_extractor` for the constant (define the string in
   `constants.py`).
3. Message (desk Generate and report Next Step): "The passport file type
   cannot be read (for example HEIC photos from an iPhone). Ask the client
   to upload the passport again as JPG, PNG or PDF, then mark the row
   Completed."
4. `retry_passport_extraction`: when the latest failed extraction has that
   error code, refuse with the same message instead of retrying.
5. Coverage report: same reason and Next Step, computed from the
   extraction records it already loads (add `error_code` to that query;
   no extra query per row).

## Constraints

No change to `passport_extractor`. No new query per row in the report.

## Validation

- Pure tests: ensure outcome with an UNSUPPORTED_FILE_TYPE failure; another
  failure code keeps `extraction_failed`; desk message; retry refused;
  report reason and Next Step.
- Test site: a Failed extraction with that error code shows the new
  message in Generate and in the report.

## Definition of done

Validation passes and the commit SHA is recorded here.

## Implementation (2026-09-28)

`the_visaguy` `96dadd4`, merged into `feat/visa-tracker` as `a318f8c` on the bench. Not pushed or deployed.

Evidence: 19 new pure tests (pure tier 556, only the 2 known errors). On
`visa-tracker-test.localhost` (rolled back): a Failed extraction with
`UNSUPPORTED_FILE_TYPE` gives `unsupported_file_type` with the new message in
Generate, Retry is refused with the same message, the coverage report shows
the same reason and Next Step; a `NO_MRZ_FOUND` failure keeps
`extraction_failed`. Full on-site suite 657 OK.

## What remains

Owner test on `visaguy`, push and deploy.
