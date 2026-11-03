---
id: TASK-049
feature: FEAT-005
title: Start the check button before the grounds list at every width
status: completed
repository: visa_refusal_checker
owners: []
depends_on:
  - TASK-029
expected_files:
  - src/components/refusal-checker/intro-screen.tsx
created: 2026-11-03
updated: 2026-11-03
---

# TASK-049: Start the check button before the grounds list at every width

Tasklane: TASK-2026-01845.

## Objective

The Start the check button is never covered or below the fold, on phones or on
laptop-height screens.

## Context

An iOS Safari screenshot showed the button under the three grounds, behind the
browser toolbar. The live site (built 2026-09-14) predates the phone fix
`0f581c8`, which explains that screenshot. Separately, from `lg` the button
still sat under the grounds list, so at 1280x800 it ended at 843px, below the
window.

## Required behaviour

- The button follows the intro text in the DOM and on screen at every width.
- No overlap with the hero visual; the button is clickable.

## Constraints

- No redesign of the hero or its copy.
- Only `intro-screen.tsx` changes.

## Validation

- Measured with no overlap and the button clickable: 375x548 ends at 425px,
  768x1024 at 427px, 1280x720 at 533px; no horizontal overflow.
- iPhone 17e and iPad simulators (Safari) checked by screenshot.
- `tsc -b`, `vite build` and `eslint` pass.

## Definition of done

- Fix in the application repository, deployed, and rechecked on a real iPhone
  and in desktop Safari.

## Completion evidence

`visa_refusal_checker`, local commits on `main`, 2026-11-03: `0f581c8` (phone
order, earlier) and `49aad7c` (button before the list at every width). Not
pushed or deployed.

## Deviations and limitations

- Marked completed at the owner's request on 2026-11-03, before push, deploy and the device checks below.

- Desktop macOS Safari was not checked directly (screen capture was not
  available). The reporter's Safari version and screen size were not supplied.
- Not runtime-verified: the live site still runs the 2026-09-14 build.
