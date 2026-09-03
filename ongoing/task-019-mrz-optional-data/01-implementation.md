# TASK-019 implementation — 2026-09-03

Implemented over `ssh -p 2257 shahzad@erpcode.tridz.in`. Code is applied and
tested on the bench and left **uncommitted** by owner instruction.

## Environment correction

TASK-019 and TASK-003 both name the feature worktree
`/home/shahzad/visa-tracker-worktrees/passport_extractor`. **That path no
longer exists.** `passport_extractor` is now a bench app at
`/home/shahzad/bench/apps/passport_extractor`, on branch `feat/visa-tracker`,
HEAD `014a36e`, working tree clean before this change. The `worktree:` field
in both task files is stale and should be corrected.

## What the defect actually was

Narrower than TASK-019 assumed. Two of the three suspected sites were already
correct in the delivered code:

- `mrz_parser.py` already composed `mrz_valid` from the four mandatory checks
  only. The delivered code had **already diverged from TASK-003 §4.4** before
  this session; the amendment brings the spec in line with code that existed,
  and required no change of its own.
- The `_correct_field` path already no-ops for a `<` check digit, so nothing
  there needed guarding.

The single live rejection path was `extraction_service.py:204`:

```python
if best_parsed["personal_number_check_valid"] is False and _other_checks_pass(best_parsed):
	_mark_needs_review(doc, CHECK_DIGIT_FAILURE, "Optional field check failed.")
	return
```

That branch alone sent the Ghanaian passport to `Needs Review`.

## Changes

1. **`ocr/mrz_parser.py`** — added `_validate_optional_data_check()`. An
   all-filler optional-data field validates on `<` or `0`; a populated field
   keeps strict numeric comparison. `compute_icao_check_digit` untouched, and
   the four mandatory check digits are unaffected.
2. **`services/extraction_service.py`** — removed the branch above, and with
   it `_other_checks_pass()`, which that branch was the only caller of.
3. **`doctype/passport_extraction/test_passport_extraction.py`** — replaced
   `test_filler_optional_data_check_digit_does_not_raise`, which asserted
   `personal_number_check_valid` is `False` and so encoded the defect, with
   seven tests.

## Finding: the optional check is nearly unreachable as an isolated failure

While writing the tests, two of them contradicted each other and one failed.
The composite check digit covers line 2 positions 22–43, which includes the
optional-data check digit at position 43. So almost any corruption of that
digit also breaks the composite, and `mrz_valid` goes false regardless.

The one exception is substituting `<` for `0` (or the reverse): both carry
numeric value 0, so the composite payload is unchanged. That is the *only*
way `personal_number_check_valid` can be false while all four mandatory
checks pass — and the fixture `test_optional_data_failure_does_not_invalidate_mrz`
now uses it deliberately (optional data `EXTRA12`, whose padded check digit
is `0`).

This strengthens the case in the TASK-003 amendment: the optional check was
not merely redundant with the composite, it was almost entirely subsumed by
it. Its practical effect was to reject blank-optional-data passports and
little else.

## Validation

- `python -m py_compile` on all three files: OK (bench env).
- `git diff --check`: clean.
- Pure tests, bench env, worktree-first `PYTHONPATH`, no site:
  `TestMRZParser` + `TestPassportExtractionUtils` + `TestImagePreprocessor` —
  **31 tests, all pass**. One pre-existing test replaced, seven added.
- `TestPassportExtractionIntegration` still requires a site and remains
  deferred to TASK-010; it was not run.
- Real-MRZ verification was done locally only, against the production
  passport that exposed the defect: all five check digits now validate and
  `mrz_valid` is true. No real MRZ data was written to any repository, per
  TASK-003 §9.4.

## State

- Bench: `feat/visa-tracker` at `014a36e`, three files modified, **not
  committed**, not pushed, not deployed.
- Patch mirrored at `ongoing/task-019-mrz-optional-data/task019.patch`.
- `visaguy` site was not migrated, tested, or touched.

## Not done

- **Part C (backfill assessment)** — cancelled by owner decision on
  2026-09-03: `visaguy` is a development site and the affected records are
  test data from feature work, so there is no backlog to count and no
  backfill to run.
- Deployment. Risk 30 stays open until deployment evidence exists.
