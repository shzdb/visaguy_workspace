---
id: TASK-029
feature: FEAT-005
title: Caseworker's file redesign, landing and footer fixes
status: completed
repository: visa_refusal_checker
owners: []
depends_on:
  - TASK-028
expected_files:
  - index.html
  - src/index.css
  - src/components/ui/
  - src/components/refusal-checker/site-chrome.tsx
  - src/components/refusal-checker/intro-screen.tsx
  - src/components/refusal-checker/case-file-rail.tsx
  - src/components/refusal-checker/question-card.tsx
  - src/components/refusal-checker/uk-visuals.tsx
  - src/components/refusal-checker/result-screen.tsx
  - public/uk/
  - README.md
created: 2026-09-14
updated: 2026-10-05
---

# TASK-029: Caseworker's file redesign, landing and footer fixes

> Recorded retroactively on 2026-09-14 from implementation evidence.

## Objective

Replace the copied eligibility-checker look with a design of its own that
combines `visa_eligibility_checker`'s question flow with `visa_tracker`'s visual
language, and add UK imagery.

## Context

Owner request, 2026-09-14: the tool should not look like either sibling, but
should use their elements and the VisaGuy design patterns, with images similar
to the tracker's.

## Required behaviour

- Tokens, type (Geist over Inter, JetBrains Mono for labels) and primitives in
  `visa_tracker`'s language.
- Landing screen with the three refusal grounds, London photo cards, Elizabeth
  Tower illustration and a report preview stamped "Example".
- Question card with a case file rail on desktop and a progress bar on all
  widths.
- Result summary card with a band stamp, dial, key facts, flags, per-ground
  breakdown and a "What to fix" timeline.
- Band colours paired with band words; AA-contrast text tones.

## Constraints

- Images must be licensed for reuse. The three UK images are CC0 from Wikimedia
  Commons; the airmail artwork is copied from `visa_tracker`.
- No change to the scoring model beyond adding a verdict headline.

## Validation

- `tsc -b`, `vite build` and `eslint` pass on each commit, checked per commit in
  a clean worktree.
- Playwright walk of the full high-risk flow at 1440 px and 375 px: no
  horizontal overflow, no console errors.
- web-design-standards audit on the landing screen: 0 fail. Its reduced-motion
  warning is a false positive (the rule is inside Tailwind's base layer).
- Landing screen re-checked at 375, 640 and 1440 px after the fixes.

## Definition of done

- The redesign is committed, builds, and passes the checks above.

## Completion evidence

`visa_refusal_checker`, all 2026-09-14:

- `82a06ec` UK imagery and the tracker's airmail artwork.
- `f97b074` headline for each risk verdict.
- `fd81f25` the redesign.
- `b9ff83e` README design section.
- `270238e` phone layout for the landing visual; "UK Standard Visitor visa"
  pill removed (owner request).
- `4e4648e` footer reduced to the copyright line (owner request).
- `0f581c8` landing call to action lifted above the fold on phones (owner
  request, 2026-10-05): the button and the grounds list swap order below `lg`.

## Deviations and limitations

- "What to fix first" was renamed "What to fix": the list is in answer order, not
  priority order.
- The footer no longer links to visaguy.ae and no longer repeats the
  disclaimer; the disclaimer remains beside the questions and on the result.
- No screen reader test was run.
