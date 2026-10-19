---
id: TASK-043
feature: FEAT-001
title: Recover a cropped or out-of-order MRZ instead of failing with NO_MRZ_FOUND
status: in-progress
repository: passport_extractor
app_path: /home/shahzad/bench/apps/passport_extractor
owners: []
depends_on:
  - TASK-042
expected_files:
  - passport_extractor/passport_extractor/ocr/mrz_parser.py
  - passport_extractor/passport_extractor/services/extraction_service.py
  - passport_extractor/passport_extractor/utils.py
  - passport_extractor/passport_extractor/tests/test_mrz_recovery.py
created: 2026-10-19
updated: 2026-10-19
---

# TASK-043: Recover a cropped or out-of-order MRZ

## Objective

Owner (2026-10-19, pilot on the live site): about 80 extractions failed with
"No machine-readable zone was detected." Only a few were wrong uploads; most
were valid passports. Make these readable without auto-verifying anything
that was guessed.

## Evidence

Seven failed live uploads (Russian, Egyptian, Sudanese, Dutch, Indian and two
other passports) were run through real OCR on the test bench
(`visa-tracker-test.localhost`). All seven reproduced `NO_MRZ_FOUND`.
`detect_mrz_candidates` accepts only two consecutive OCR lines of exactly 44
characters with line 1 first. OCR returned:

| Cause | Files | What OCR returned |
|---|---|---|
| Line end cropped or covered by a scanner-app badge (CamScanner) | Russian, Sudanese, Egyptian | lines of 39–42 characters; number, birth date and expiry intact |
| One `<` dropped from a long filler run | Indian | both lines 43 characters, nothing else missing |
| Filler read as letters, small low-resolution MRZ | Dutch, one other | line 2 head intact, tail garbled; line 1 short |
| Lines returned in swapped order | one PDF | both lines 44 characters, line 2 first |

In every case the first 28 positions of line 2 (number, nationality, birth
date, sex, expiry, and their check digits) were read. Those fields carry
their own ICAO check digits, so they can be trusted without the rest.

## Required behaviour

1. `recover_mrz_candidates(text_lines)` in `mrz_parser.py`:
   - a line 2 is any OCR line whose first 28 positions have the TD3 shape
     (stray characters before it are allowed);
   - positions 29–44 are rebuilt three ways: as read and padded or cut at the
     right; with the longest filler run stretched or shortened so the last
     characters stay in the check-digit positions; pure filler;
   - it is paired with a line 1 starting with `P` within two OCR lines, before
     or after it; a short line 1 is padded with `<`;
   - a line 2 with no `P` line 1 nearby is not recovered (so a visa or ID card
     MRZ never becomes a passport);
   - each candidate says whether it was `reconstructed` (anything padded or
     changed). Two full 44-character lines in swapped order are not
     reconstructed.
2. `analyse_file` collects recovered candidates per OCR pass while no strict
   candidate exists. They are used only when the whole search found no strict
   candidate, so every file the strict detector reads keeps its result.
3. A recovered candidate is used only if at least two of the three field check
   digits (number, birth date, expiry) validate. Ranking: MRZ valid, then
   number of valid field checks, then a clean optional-data field, then not
   reconstructed, then confidence.
4. A reconstructed candidate always ends `Needs Review` with the new error
   code `MRZ_INCOMPLETE` ("Part of the machine-readable zone could not be
   read. Check the details against the passport."), with the fields filled
   in, even when every check digit passes. Operations verify it with the
   existing Verify action (TASK-033). A swapped full pair is classified as
   usual and may be `Extracted`.
5. `raw_extraction_result` records `recovered` and `reconstructed`.

## Constraints

- No change to the strict detector or to any file it already reads.
- `MRZ_INCOMPLETE` is a new value of the Data field `error_code`; no schema
  change. No other app reads the error codes.
- Built on TASK-042 (`perf/passport-extraction-speed`), the pipeline that
  was benchmarked.

## Validation

- Pure tests: `tests/test_mrz_recovery.py` (cropped, dropped filler, junk
  tail, stray prefix, swapped order, window, lone line 2, visa, subtype,
  pipeline status and error code, strict candidate wins, one check digit is
  not enough).
- Real OCR on the test bench: the 36 pilot passports must give the same
  status and fingerprint as the legacy run; the seven failed uploads must no
  longer fail. Results below.

## Results (2026-10-19)

Pure tests: 109 OK on the bench worktree (TASK-042 + TASK-043 + TASK-044).

Real OCR on `visa-tracker-test.localhost`, run from the branch:

| Upload | Before | After | Values match the printed page |
|---|---|---|---|
| chama.pdf | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE, all check digits valid | not compared |
| dani.pdf | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE | yes |
| egypt (re-run as .jpg; the .webp copy is rejected as unsupported) | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE, all check digits valid | yes |
| maria.pdf | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE | yes |
| pratham.pdf | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE | yes (number `AI840417`, confirmed by its check digit) |
| sudan.jpg | Failed NO_MRZ_FOUND | Needs Review MRZ_INCOMPLETE | yes |
| z.pdf (lines swapped) | Failed NO_MRZ_FOUND | Extracted | yes |

"Values match" compares a hash of passport number and birth date with the
values read from the page; no values were printed.

36 pilot passports: identical to `legacy` for all 37 files. Average 54.9 s.
The 4 pilot files that failed with NO_MRZ_FOUND still fail: no TD3 line 2 sits
next to a `P` line.

Not run: the on-site suite and a test-site migrate (switching the bench's
installed checkouts was refused; they are shared with `visaguy`).

PR: https://github.com/tridz-dev/passport_extractor/pull/5

## Definition of done

- Pure tests pass; real-data comparison recorded; PR open against `main`.
- Owner merges and deploys (with TASK-042 and TASK-044).
