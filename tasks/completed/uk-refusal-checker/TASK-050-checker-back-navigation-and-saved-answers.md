---
id: TASK-050
feature: FEAT-005
title: Back navigation and saved answers in the checker
status: completed
repository: visa_refusal_checker
owners: []
depends_on:
  - TASK-030
expected_files:
  - src/components/refusal-checker/checker-session.ts
  - src/components/refusal-checker/checker-history.ts
  - src/components/refusal-checker/refusal-checker.tsx
  - src/components/refusal-checker/question-card.tsx
  - src/components/refusal-checker/refusal-letter-upload.tsx
created: 2026-11-03
updated: 2026-11-03
---

# TASK-050: Back navigation and saved answers in the checker

Tasklane: TASK-2026-01846.

## Objective

Applicants move back and forward between questions without losing answers, and
a reload keeps their progress within the tab.

## Required behaviour

- Each question after the first has a Back button that shows the previous
  question with the answer filled in (phone step keeps the country code).
- Answers and the current step are kept in `sessionStorage` under one key.
  Access is guarded and the stored shape is validated.
- Start over and Start a new check clear the stored check.
- The refusal letter step stores only the file name and shows it as attached.
- The browser's Back and Forward move between questions through the History
  API on one URL, not a page per question (owner, 2026-11-03).

## Decisions

- 2026-11-03 (owner): a reload during the processing screen opens the result.
  Processing is a 3 s animation and the score is computed instantly from the
  stored answers, so replaying it adds delay only.
- 2026-11-03 (owner): browser Back and Forward use History API entries
  (`{step, depth}`), not routes. Back from the result skips processing; Start
  over rewinds to the first entry; an entry past the answered steps opens the
  furthest answered step.
- Tasklane refused `decision add` for the user's role, so both decisions are
  recorded here and in the Tasklane session note.

## Validation

- Browser-checked: Back with text, phone and choice prefill; reload mid-flow
  and during processing; the upload step after Back; Start a new check;
  invalid stored data; browser Back and Forward, in-app Back then Forward,
  Back after a reload, Back from the result, Start over.
- `tsc -b`, `vite build` and `eslint` pass.

## Definition of done

- Fix in the application repository, deployed, and the swipe-back gesture
  checked on a real iPhone.

## Completion evidence

`visa_refusal_checker`, local commits on `main`, 2026-11-03: `e2a7025`
(sessionStorage and in-app Back) and `6277de0` (browser Back and Forward). Not
pushed or deployed.

## Deviations and limitations

- Marked completed at the owner's request on 2026-11-03, before push, deploy and the device checks below.

- iOS swipe-back was not tested separately; it uses the same `popstate` path.
- Not runtime-verified.
