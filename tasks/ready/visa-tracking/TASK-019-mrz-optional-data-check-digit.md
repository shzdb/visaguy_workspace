---
id: TASK-019
feature: FEAT-001
title: Accept ICAO filler check digit for unused MRZ optional data, and stop an optional field vetoing mrz_valid
status: ready
repository: passport_extractor
worktree: /home/shahzad/visa-tracker-worktrees/passport_extractor
owners: []
depends_on:
  - TASK-003
expected_files:
  - passport_extractor/passport_extractor/ocr/mrz_parser.py
  - passport_extractor/passport_extractor/services/extraction_service.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py
created: 2026-09-03
updated: 2026-09-03
---

# TASK-019: Accept ICAO filler check digit for unused MRZ optional data, and stop an optional field vetoing `mrz_valid`

## Objective

Fix a confirmed false-rejection defect in the TD3 MRZ validator. Passports
that leave the optional-data field (MRZ line 2, positions 29–42) blank are
currently classified `Needs Review` even when every mandatory check digit
passes and OCR confidence is high, because the validator rejects the ICAO
filler character in the optional-data check-digit position.

Two changes are required: make the check-digit comparison conformant for an
unused optional-data field (Part A), and remove the optional field's power to
veto `mrz_valid` and force review on its own (Part B). See risk 30 in
`docs/risks-and-open-questions.md`.

## Context

Observed 2026-09-03 on a real production extraction. A Ghanaian passport
produced an OCR confidence of roughly 95%, well above
`CONFIDENCE_OK_THRESHOLD` (75.0), with four of the five check digits valid —
passport number, date of birth, expiry date, and the composite check all
passed. Only `personal_number_check_valid` was false, and the record was
classified `Needs Review`.

Ghana leaves the optional-data field unused, so MRZ line 2 positions 29–42
are all `<` fillers and the check digit at position 43 is also `<`. ICAO 9303
Part 4 permits a filler in that check-digit position when the field itself is
unused; some issuers write `0` there instead. Both are conformant. The
validator computes the check digit over the filler string, obtains `0`,
compares it against the `<` it read, and returns false.

TASK-003 then converts that single false flag into a rejection twice over:

- §4.4 requires all five check digits valid for `mrz_valid`, so one optional
  field drops `mrz_valid` to false.
- §5.3 additionally lists `personal_number_check_valid` being false while
  other checks pass as its own explicit `Needs Review` trigger.

Both must change, or the fix is only half applied. TASK-003 has been amended
accordingly — see its "Amendment (2026-09-03)" section.

### Why the optional check may be dropped from `mrz_valid` safely

The composite check digit at MRZ line 2 position 44 is computed over
positions 1–10, 14–20, and **22–43**. Positions 29–43 — the optional-data
field and its own check digit — are inside that range. Corrupted or
misread optional data therefore still fails the composite check, which
remains mandatory. Removing `personal_number_check_valid` from `mrz_valid`
loses no tamper or misread detection; it removes a duplicate, weaker signal
that can fire on its own against a document whose identity fields are
provably intact.

The flag itself is still worth computing and storing as review evidence. It
is its promotion to a veto that is wrong.

## Inputs

- `passport_extractor/passport_extractor/ocr/mrz_parser.py` — the TD3 parser
  and `compute_icao_check_digit`; locate where the optional-data check digit
  is compared.
- `passport_extractor/passport_extractor/services/extraction_service.py` —
  the `mrz_valid` composition and the `Extracted` / `Needs Review` / `Failed`
  classification implementing TASK-003 §5.3.
- `tasks/completed/visa-tracking/TASK-003-passport-ocr-and-mrz-pipeline.md`
  §4.4, §5.3 and its "Amendment (2026-09-03)" section.
- ICAO 9303 Part 4, check-digit and filler rules for the optional-data field.

## Required behaviour

### Part A — conformant filler handling

A1. When the optional-data field (line 2, positions 29–42) consists entirely
of `<` fillers, treat the check digit at position 43 as valid if it is
either `<` or `0`. Both are conformant for an unused field and both are
issued in practice.

A2. Apply this rule **only** to the optional-data check digit. The four
mandatory check digits (passport number, date of birth, expiry date,
composite) keep strict numeric comparison. A filler in any mandatory
check-digit position remains a failure.

A3. When the optional-data field is populated, comparison stays strict and
unchanged.

A4. Do not change `compute_icao_check_digit` itself. It is correct — the
defect is in how its output is compared for the unused-field case, so the
special case belongs at the comparison site.

### Part B — `mrz_valid` scope

B1. Compose `mrz_valid` from the four mandatory checks only: passport
number, date of birth, expiry date, composite.

B2. Keep computing and storing `personal_number_check_valid` on the record
as review evidence. Do not remove the field.

B3. Remove the classification rule that routes a record to `Needs Review`
solely because `personal_number_check_valid` is false while other checks
pass. Leaving this rule in place makes Part B a no-op.

B4. All other `Needs Review` and `Failed` triggers in TASK-003 §5.3 are
unchanged: missing required fields, confidence below threshold, a false
mandatory check digit, no MRZ found, unreadable file, OCR engine failure.

### Part C — backfill assessment (assess and report; do not execute)

C1. Identify existing `Passport Extraction` records affected by the defect:
`extraction_status = 'Needs Review'` with `personal_number_check_valid = 0`
and all four mandatory check flags = 1. Report the count and, per record,
the five flags and the extraction status — no MRZ text, passport numbers, or
other PII in the report.

C2. Establish whether re-validation can run from the stored `mrz_line_1` /
`mrz_line_2` values without re-running PaddleOCR. It should: the lines are
already persisted, and both Part A and Part B are pure functions of them.
Confirm this rather than assuming it.

C3. **Determine and record whether flipping a record from `Needs Review` to
`Extracted` cascades into client-visible state** before any backfill is
proposed. The transition clears `requires_review`, and TASK-006 lifecycle
sync plus TASK-016's derivation of client status from the process file may
react to it. Trace the actual trigger path and write down what it does.

C4. Do not run the backfill as part of this task. Record the findings, the
proposed backfill procedure, and the cascade analysis, and stop for owner
decision.

### Part D — tests

D1. Pure-function tests, no Frappe site and no OCR, using synthetic fake MRZ
strings only. Cover:

- Optional data all fillers, check digit `<` → valid, `Extracted`.
- Optional data all fillers, check digit `0` → valid, `Extracted`.
- Optional data populated with a correct check digit → valid, `Extracted`.
- Optional data populated with a wrong check digit, composite still valid →
  `Extracted`, with `personal_number_check_valid` stored false.
- Optional data corrupted such that the composite check fails →
  `Needs Review` (proves composite still covers positions 29–43).
- A filler character in a **mandatory** check-digit position →
  `Needs Review` (guards against Part A being applied too broadly).
- A wrong expiry-date check digit → `Needs Review` (regression guard on the
  mandatory path).

D2. Fixtures must use obviously fake MRZ data in the style already
established by TASK-003 §9.1. TASK-003 §9.4 stands: no real passport images,
no MRZ strings from real documents, no production PII in the repository or
in this task file.

## Constraints

- Work only in `/home/shahzad/visa-tracker-worktrees/passport_extractor`.
  Do not modify original repository checkouts.
- **Do not commit the code changes in the bench.** Leave the working tree
  dirty for owner review. Committing, pushing, and deploying are owner
  actions on this feature.
- Do not push to any Git remote and do not deploy.
- Do not run the Part C backfill, and do not modify any existing
  `Passport Extraction` record as part of this task.
- Do not run migrations or tests against the `visaguy` site.
- Do not weaken any mandatory check digit, and do not change
  `compute_icao_check_digit`.
- Do not touch `the_visaguy`, `fileflo`, `processflo`, or any other
  repository; TASK-003's forbidden-dependency rule for `passport_extractor`
  still applies in full.

## Validation

### Static validation (required now)

- [ ] Changed `.py` files compile (`python -m py_compile <file>`).
- [ ] The Part D pure tests run with the worktree-first `PYTHONPATH` and
      pass without a Frappe site.
- [ ] The existing TASK-003 pure test suite still passes; report before and
      after counts.
- [ ] Forbidden-dependency scan still passes.
- [ ] No real MRZ string, passport number, or passport image is added to the
      repository or to this task file.
- [ ] `git diff --check` passes.
- [ ] `git status` shows the change uncommitted, per the constraint above.

### Runtime validation (deferred, consistent with TASK-003/TASK-010)

- [ ] Integration tests on the dedicated test site once TASK-010 unblocks it.
- [ ] A production record exhibiting the defect re-validates to `Extracted`
      after the fix is deployed — deployment evidence, not implementation
      evidence.

## Definition of done

- Part A and Part B implemented in the feature worktree, uncommitted.
- Part D tests written and passing as pure functions.
- Part C findings recorded in this task file: affected record count, whether
  re-validation from stored MRZ lines is sufficient, and the client-visible
  cascade analysis. No backfill executed.
- TASK-003's amendment and the implementation agree; if implementation
  reveals the amendment is wrong, correct the amendment rather than
  diverging from it silently.
- Risk 30 in `docs/risks-and-open-questions.md` updated on deployment
  evidence only, per this workspace's standing rule — not on implementation.
- Session record written under `ongoing/visa-tracking-implementation/`.

## Stop conditions

Stop and record a decision request if any of the following occur:

1. **Cascade is client-visible and non-trivial**: Part C shows that flipping
   `Needs Review` → `Extracted` changes what a client sees on the public
   tracker in a way that needs an owner decision before any backfill.
2. **`mrz_valid` has other consumers**: the flag is read outside
   `passport_extractor` (for example by TASK-006 lifecycle sync or the public
   API) in a way that makes narrowing its definition a cross-repository
   behaviour change.
3. **The stored MRZ lines are insufficient** for re-validation, making the
   backfill an OCR re-run rather than a pure re-check.
4. **The defect is not where this task says it is** — for example the
   comparison is already conformant and `personal_number_check_valid` is
   false for a different reason. Record the real cause and stop.
5. **Permission denial** on any required worktree or bench operation.
