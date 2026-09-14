---
id: TASK-028
feature: FEAT-005
title: "Initial build: design system port, question set, risk model, result screens"
status: completed
repository: visa_refusal_checker
owners: []
depends_on: []
expected_files:
  - src/config/brand.ts
  - src/components/ui/
  - src/components/refusal-checker/questions.json
  - src/components/refusal-checker/scoring.ts
  - src/components/refusal-checker/SCORING.md
  - src/components/refusal-checker/steps.ts
  - src/components/refusal-checker/result-screen.tsx
  - src/components/refusal-checker/processing-screen.tsx
  - src/components/refusal-checker/consult-modal.tsx
created: 2026-09-14
updated: 2026-09-14
---

# TASK-028: Initial build

> Recorded retroactively on 2026-09-14 from implementation evidence. No task
> document existed when the work was done.

## Objective

Stand up a public UK visa refusal risk checker as a frontend-only single-page
app, with a question set, a refusal risk model, and processing and result
screens.

## Context

Companion to `visa_eligibility_checker`. At this stage it deliberately reused
that tool's design system: theme tokens, UI primitives, layout chrome and
typography.

## Inputs

- `visa_eligibility_checker` design system and `PulseRing` dial.
- Owner direction on refusal grounds and alert scope (2026-09-07).

## Required behaviour

- Step machine: intro, name, mobile, scored choice questions, processing,
  result.
- Three pillars (funds, return intent, purpose and consistency), each normalised
  against its own worst case; overall score blends the worst pillar with the
  weighted average.
- Hard flags for undeclared refusal and undeclared conviction (floor 80), and an
  overstay compound flag.
- Inline "Worth knowing" note after a risky answer, not a modal.
- Result screen leads with flags, then the dial, band, per-ground breakdown and
  fixes. Consultation offer for moderate and high only, after a delay.

## Constraints

- No backend, no AI, no network calls, no lead integration.
- No approval percentage or probability language (owner, 2026-09-07).

## Expected changes

See `expected_files`.

## Validation

- Browser end-to-end on a moderate profile (39) and a high-risk profile (81), and
  at 375 px with no horizontal overflow — reported in commit `078a996`.
- Scoring checked against nine reference profiles listed in `SCORING.md` at
  `ba7b0ba`.

## Definition of done

- The flow runs end to end in the browser and produces a scored result.
- The model is documented in `SCORING.md`.

## Completion evidence

- `visa_refusal_checker` commits `d7f08e9` (design system port), `ba7b0ba`
  (question set and risk model), `078a996` (processing and result screens), all
  2026-09-07.
- Validation is as reported in those commit messages; it was not re-run for this
  record. No automated tests exist.

## Deviations and limitations

- The visual design was later replaced (TASK-029) and the question set revised
  (TASK-030). The reference profile scores in this task are superseded by
  TASK-030's.
