---
id: TASK-030
feature: FEAT-005
title: Question set revision and refusal letter upload
status: completed
repository: visa_refusal_checker
owners: []
depends_on:
  - TASK-028
expected_files:
  - src/components/refusal-checker/questions.json
  - src/components/refusal-checker/scoring.ts
  - src/components/refusal-checker/SCORING.md
  - src/components/refusal-checker/steps.ts
  - src/components/refusal-checker/refusal-letter-upload.tsx
  - src/components/refusal-checker/question-card.tsx
  - src/components/refusal-checker/refusal-checker.tsx
  - src/components/refusal-checker/result-screen.tsx
created: 2026-09-14
updated: 2026-09-14
---

# TASK-030: Question set revision and refusal letter upload

> Recorded retroactively on 2026-09-14 from implementation evidence.

## Objective

Apply the owner's question changes and add a refusal letter upload, simulated
until a backend exists.

## Required behaviour

- Merge "unexplained deposits" and "income vs spending" into `bankStatements`,
  with the owner's four options.
- Merge "form consistency" and "purpose evidence" into `evidenceConsistency`,
  with the owner's four options.
- Remove the length-of-stay question.
- Add an optional refusal letter upload after the refusal history question,
  shown to every applicant (owner, 2026-09-14). PDF, JPG or PNG up to 10 MB;
  skippable; no API.

## Constraints

- Keep each pillar's weighting of each problem: a merged "both problems" option
  carries the sum of the two worst values it replaced (33 and 30).
- No network call for the upload.

## Validation

- Reference profiles recomputed through the real `calcRisk` (loaded with Vite's
  SSR loader) and written to `SCORING.md`.
- Playwright: upload step appears for all four refusal history answers; skip,
  invalid type and upload paths; the uploaded file name appears on the result;
  no overflow at 375 px after fixing a clipping defect; no console errors.
- `tsc -b`, `vite build` and `eslint` pass on each commit.

## Definition of done

- Ten questions, scoring and documentation consistent, upload step present for
  every applicant, all checks passing.

## Completion evidence

`visa_refusal_checker`, all 2026-09-14:

- `e9a5176` merge overlapping questions and drop length of stay.
- `7515291` add the refusal letter upload (first version, shown only after a
  declared refusal).
- `bbbcb4f` show the upload to every applicant.

## Deviations and limitations

- **Scoring shift.** With two questions left in return intent, one worst answer
  moves that pillar further: thin ties alone rose from 26 to 37 (still
  moderate).
- **Overstay flag changed.** It now fires on thin ties plus not working; a long
  stay no longer triggers it because the question is gone.
- **Upload is simulated.** A timer drives the progress bar; the file never leaves
  the browser; only its name is kept. The result and the WhatsApp message still
  say the letter was uploaded (risk 43).
- The upload does not count toward the question total or the case file rail.
