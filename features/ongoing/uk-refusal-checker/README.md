---
id: FEAT-005
title: UK visa refusal risk checker
status: ongoing
priority: medium
repositories:
  - visa_refusal_checker
owners: []
depends_on: []
created: 2026-09-14
updated: 2026-09-14
---

# UK visa refusal risk checker

> Recorded retroactively on 2026-09-14. The work below was done in
> `visa_refusal_checker` between 2026-09-07 and 2026-09-14 without a workspace
> feature or task. This document and TASK-028 to TASK-030 reconcile the
> workspace with that implementation. They do not approve decisions that were
> not already made by the owner.
>
> Numbering: FEAT-002 to FEAT-004 are taken on the unmerged branch
> `chore/workspace-audit-remediation`, so this feature is FEAT-005.

## Summary

A public, single-page tool for applicants to a UK visit visa. It asks about
funds, ties to home, the trip's evidence, and declarations, and it tells the
applicant where the application is most exposed to refusal and what to fix.

It is a companion to `visa_eligibility_checker` (which scores whether an
applicant is likely to qualify) and shares the VisaGuy visual family with
`visa_tracker`, but it is a separate site with its own design.

## User value

- Applicants see which of the three common refusal grounds their file is
  exposed on before they submit, not after a refusal.
- Each risky answer explains why it matters and what usually fixes it.
- Moderate and high risk results lead to a WhatsApp consultation, named by the
  applicant's weakest ground.

## Scope

### Included

- Frontend only: React 19, Vite 8, TypeScript 6, Tailwind CSS v4, Phosphor
  icons, React Compiler.
- Single zone, The Visa Guy UAE. Brand and WhatsApp number live in
  `src/config/brand.ts`.
- Flow: landing screen → name and mobile → 8 scored or advisory questions →
  optional refusal letter upload → staged processing screen → result.
- Browser-side scoring from `src/components/refusal-checker/questions.json`.
- Result: risk band stamp, 0–100 risk score dial, hard and compound flags,
  per-ground breakdown, "What to fix" list, travel-timing note, consultation
  offer, WhatsApp hand-off.

### Excluded

- Any backend, AI call, or network request other than static assets and Google
  Fonts.
- Lead capture into Frappe (`Raw Lead` / `Lead`). Name and mobile are held in
  React state only.
- Real file upload. The refusal letter upload is simulated in the browser.
- Multi-zone support.
- An approval percentage or probability of refusal (owner decision,
  2026-09-07; see "Decisions already made").

## Requirements

- Score three pillars: funds (weight 0.40), return intent (0.35), purpose and
  consistency (0.25). The overall figure is `0.55 × worst pillar + 0.45 ×
  weighted average`, so one weak ground dominates.
- Bands: low under 25, moderate 25–54, high 55 and above.
- An undeclared refusal or undeclared conviction raises the overall figure to
  at least 80 and adds a named flag. Thin ties plus not working adds 6 points
  and the overstay flag.
- Flags render before the per-ground breakdown.
- Output stays qualitative. The score is labelled a risk score, never a
  probability.
- Accessible and responsive: WCAG AA text contrast, 44 px tap targets, focus
  moved to each new question, reduced-motion respected, no horizontal overflow
  at 375 px.

The model and its reference profiles are documented in the application
repository at `src/components/refusal-checker/SCORING.md`.

## Proposed design

Implemented as a "caseworker's file": the landing screen pairs the three
refusal grounds with CC0 London photo cards, an Elizabeth Tower illustration,
and an example report stamped "Example"; each question sits in a card with a
case file rail showing progress by section; the result is a summary card
stamped with the band. Tokens, type (Geist over Inter) and primitives follow
`visa_tracker`; the one-question flow, insight notes, dial and processing
stages follow `visa_eligibility_checker`. Image sources and licences are in
`public/uk/CREDITS.md` in the application repository.

## Tasks

| Task | Title | Status |
|---|---|---|
| TASK-028 | Initial build: design system port, question set, risk model, result screens | completed |
| TASK-029 | Caseworker's file redesign, landing and footer fixes | completed |
| TASK-030 | Question set revision and refusal letter upload | completed |

## Acceptance criteria

| Criterion | Evaluation |
|---|---|
| Applicant completes the flow and gets a band, score, flags, per-ground breakdown and fixes | Met. Browser-verified locally at 1440 px and 375 px (TASK-029, TASK-030). |
| Hard flags cannot be averaged away | Met. `SCORING.md` reference profile "Clean, but an undeclared conviction" scores 80 (TASK-030). |
| No approval percentage or probability language | Met. Score labelled "Refusal risk score, out of 100"; bands only. |
| Build, type check and lint pass | Met on every commit from `82a06ec` to `bbbcb4f`, checked per commit in a clean worktree. |
| Accessible and responsive | Met for the checks run: web-design-standards audit 0 fail; no overflow at 375 px. No screen reader test was run. |
| Answers reach VisaGuy as a lead | **Not met.** No lead capture exists. See open questions. |
| Refusal letter reaches a specialist | **Not met.** Upload is simulated. See open questions. |
| Deployed and reachable by the public | **Not evidenced.** No hosting or deployment record. |

## Dependencies

- None on the Frappe bench. The tool makes no API calls.
- WhatsApp deep links (`wa.me`) for the hand-off.
- Google Fonts for Geist, Inter and JetBrains Mono.

## Risks

See `docs/risks-and-open-questions.md` risks 42, 43 and 44.

## Open questions

1. **Lead capture.** Should name, mobile and answers be written to Frappe, and
   through which path (`Raw Lead`/`Lead` as the eligibility checker does, or a
   dedicated API)? The mobile step already says "We'll send your risk report
   here", which nothing currently does (risk 42).
2. **Refusal letter storage.** Where should uploaded letters go, who may read
   them, and how long are they kept? A refusal letter carries personal and
   immigration history data. This needs a privacy and architecture decision
   before a real upload is built (risk 43).
3. **Hosting and deployment.** Where does the tool run, and who deploys it?
4. **Calibration.** If refusal outcome data becomes available, recalibrate the
   risk values and revisit the approval-rate indicator (risk 44).

## Decisions already made

Owner decisions recorded in the application repository and session history;
not ADRs, because none changes platform architecture.

- 2026-09-07: no approval-percentage or success-rate indicator; no
  interruptive alerts for the overstay pattern or near travel dates. Alerts
  are inline notes and result cards only.
- 2026-09-14: merge the bank statement questions and the form and evidence
  questions; remove the length-of-stay question; offer the refusal letter
  upload to every applicant, not only to those who declare a refusal.
- 2026-09-14: remove the "UK Standard Visitor visa" pill from the landing
  screen; the footer shows only the copyright line.

## Completion notes

Not complete. The applicant-facing flow is built and verified locally, but
lead capture, real document upload and deployment are open (acceptance
criteria above). Implementation evidence:

- Repository: `visa_refusal_checker`, remote `tvgglobal/visa_refusal_checker`.
- Commits `d7f08e9` … `bbbcb4f` on `main`. The local remote-tracking ref
  `origin/main` was at `4e4648e` on 2026-09-14 (not re-fetched); `bbbcb4f` is
  local only and has no upstream configured.
- No automated test suite exists in the repository.
