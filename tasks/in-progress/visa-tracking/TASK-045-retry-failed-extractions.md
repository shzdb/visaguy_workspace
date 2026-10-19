---
id: TASK-045
feature: FEAT-001
title: Retry failed extractions in bulk after the MRZ fix
status: in-progress
repository: passport_extractor
app_path: /home/shahzad/bench/apps/passport_extractor
owners: []
depends_on:
  - TASK-043
  - TASK-044
expected_files:
  - passport_extractor/passport_extractor/extraction_queue.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction_list.js
  - passport_extractor/passport_extractor/tests/test_extraction_queue.py
created: 2026-10-19
updated: 2026-10-19
---

# TASK-045: Retry failed extractions in bulk

## Objective

Owner (2026-10-19): many uploads on live failed before the MRZ recovery
(TASK-043). They stay `Failed` after deploy, and retrying about 80 records one
by one is not practical. Add a bulk option.

## Required behaviour

`retry_failed_extractions(dry_run=1, error_codes=None, limit=None)` in
`extraction_queue.py`, System Manager only; list view menu **Queue → Retry
Failed Extractions** (dry run, then confirm) and `bench execute`.

- Selects `Failed` records whose `error_code` is `NO_MRZ_FOUND` or
  `OCR_ENGINE_ERROR` by default. `UNSUPPORTED_FILE_TYPE`, `FILE_TOO_LARGE`,
  `PASSWORD_PROTECTED_PDF` and `FILE_READ_ERROR` fail the same way again and
  are left out; `error_codes` overrides the list.
- Skips a record when a newer extraction exists for the same source (source
  doctype, document, field ID, row) or, without a source, the same file. So
  the action can be run again safely, and a record already retried by hand is
  not retried twice.
- Retries through `create_retry_extraction` (the Retry button path): a new
  `Queued` record with the file and source, on the extraction queue; the
  failed record is unchanged.
- One failing record (for example a source document that no longer exists)
  is rolled back to a savepoint, logged in Error Log, and does not stop the
  rest. `limit` caps one call, oldest first.

## Validation

- Pure tests (`test_extraction_queue.py`): dry run, apply through the retry
  path, chosen error codes, limit, one failure does not stop the rest, the
  newer-extraction match, System Manager. All pure tests: 116 OK.
- On-site suite on `visa-tracker-test.localhost`: 189 OK.
- Test site run (passport_extractor at `8be23d3`, two
  `passport_extraction` workers): a real failed upload (the cropped Russian
  passport) set to `Failed` / `NO_MRZ_FOUND` as the old pipeline left it.
  Dry run listed it with 70 test-fixture failures and 3 already retried;
  apply retried all 71 with 0 errors; a second dry run found nothing to retry.
  Its retry ended Needs Review / `MRZ_INCOMPLETE`, confidence 99.39; the
  original stayed `Failed`. The 70 fixtures (8×8 blank images) failed again as
  expected; no failed RQ jobs. The test records and file copy were deleted and
  the installed checkout switched back to `perf/passport-extraction-speed`.

## Definition of done

- Tests pass; shipped in tridz-dev/passport_extractor#5; owner runs it on live
  after deploy (runbook step 7).
