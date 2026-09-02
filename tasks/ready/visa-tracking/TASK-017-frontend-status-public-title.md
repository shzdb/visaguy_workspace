---
id: TASK-017
feature: FEAT-001
title: Render derived status public_title through the frontend wire contract
status: ready
repository: visa_tracker
owners: []
depends_on:
  - ADR-010
  - TASK-016
  - TASK-009
expected_files:
  - src/test/contract/wireContract.ts
  - src/types/tracking.ts
  - src/api/contract.test.ts
  - src/mocks/handlers.ts
created: 2026-09-01
updated: 2026-09-02
---

# TASK-017: Render derived status public_title through the frontend wire contract

## Objective

Consume the new `title` field that TASK-016 (backend, `the_visaguy`) adds to
the public status/timeline API response, threading it through
`visa_tracker`'s wire-contract fixture module, its MSW mocks, its contract
conformance tests, and the UI that renders the current status and timeline.

This task is **not started**. It is marked `ready` because it requires no new
product or architecture decision — ADR-010 already specifies the field name
(`public_title` on `Visa Tracking Status`, sent as `title` on the wire), the
six status values, and their exact `public_title` copy. It cannot begin
functionally until TASK-016 has shipped the backend field, but the frontend
contract-fixture and type changes described here can be drafted against the
documented contract in the meantime.

## Context

`expected_files` above lists `src/test/contract/wireContract.ts` and
`src/types/tracking.ts` as directly confirmed (both were read this session);
`src/api/contract.test.ts` and `src/mocks/handlers.ts` are inferred from the
frontend stack and TASK-009's established pattern and must be verified
against the actual repository tree at implementation time, not assumed.

Repository: `/Users/shzd/Projects/tridz/visa_tracker`. As of this session it
reports **41 tests green** (`npm run test`, i.e. `vitest run`). This is the
number to protect and grow from — do not let this task's changes reduce it
without an explicit, reported reason.

The single source of truth for every mock and fixture in this test suite is
`src/test/contract/wireContract.ts` — read directly this session. Its own
header comment states the rule this task must keep honoring: "Every
mock/fixture used anywhere in this test suite must import its shapes from
this module rather than redeclaring literals. If the contract drifts... that
drift must show up here first." Do not add the new `title` field to any
mock/fixture file other than this one and then let other files redeclare it
independently.

`src/types/tracking.ts` currently defines `StatusResponse` and
`StatusTimelineItem` without a `title` field:

```ts
export interface StatusResponse {
  applicant_name_masked: string
  passport_number_masked: string
  destination: string
  visa_type: string
  current_status: string
  public_message: string
  last_updated: string
  timeline: StatusTimelineItem[]
  support_link: string
}
```

`StatusTimelineItem` similarly has no `title` field today (`status`,
`message`, `effective_on`, `icon` only). ADR-010 requires `title` to arrive
per-status, so it is needed timeline-wide, not only on the current status —
confirm against TASK-016's actual implemented payload shape once it lands
(does `title` appear once at the top level for `current_status` only, or on
every `StatusTimelineItem` too?) and do not assume; this is exactly the kind
of silent-divergence risk `wireContract.ts`'s own header comment warns
about.

**TASK-016 has now shipped (backend, uncommitted, evidence in TASK-016's own
"Completion evidence (2026-09-02)" section and
`ongoing/visa-tracking-implementation/13-session-2026-09-02-task-016.md`) —
the question above is answered and recorded here so this task does not need
to re-derive it.** The exact shipped shape:

Top-level `data` object:

```
applicant_name_masked, passport_number_masked, destination, visa_type,
current_status, title, public_message, last_updated, timeline, support_link
```

`title` is new, positioned immediately after `current_status`. Each
`timeline` entry:

```
status, title, message, effective_on, icon
```

`title` is new here too, positioned immediately after `status` — **it does
appear on every `StatusTimelineItem`, not only at the top level.** In both
places `title` is always a string, never null: every resolvable status
(all six, per ADR-010) has a non-empty `public_title`, so the
"constant-shape" empty-string convention documented on
`emptyOptionalStatusResponse` does not need a special case for `title` —
it should simply always be populated on any `success: true` response, same
as `public_message`/`message`.

**Before starting UI work, reconcile with `ongoing/tracker-ui-polish/`** (an
untracked, in-flight workstream as of 2026-09-02) — it touches the same
frontend components this task needs to change (the status/timeline
rendering). Two uncoordinated changes to the same components risk a merge
collision or, worse, one silently reverting the other's work. Check its
current state before writing any component code here.

## Required behaviour

1. Add `title: string` (naming exactly as it arrives on the wire — verify
   against TASK-016's shipped payload rather than assuming `title` survives
   unchanged from ADR-010's wording) to the relevant type(s) in
   `src/types/tracking.ts`.
2. Update `wireContract.ts`'s fixtures (`sampleStatusResponse`,
   `emptyOptionalStatusResponse`, `sampleTimelineItem`,
   `sampleTimelineItemSecond`, and the envelopes built from them) to include
   realistic `title` values — use ADR-010's actual copy (e.g. "Wheels up!",
   "Final checks before takeoff.") for at least one fixture so a reviewer can
   see the intended tone, not a placeholder string.
3. Update the contract-conformance test (`src/api/contract.test.ts` or
   wherever TASK-009 established it — confirm exact path/name at
   implementation time) to assert the new field's presence and type.
4. Update the MSW mock handlers so mocked responses match the new contract
   shape exactly — no handler should hand-roll a response literal that
   diverges from `wireContract.ts`.
5. Update the UI component(s) that render current status and the timeline to
   display `title` as the primary heading, with the existing
   `public_message`/`message` copy as supporting text beneath it — matching
   ADR-010's stated reason for adding a separate field (the internal
   `status_name`/`current_status` label must not be shown as the client's
   heading, and marketing copy must not appear in place of the plain
   operational label anywhere it currently does the ops-facing job). This
   feature's frontend is public/client-facing only (`visa_tracker` has no ops
   UI), so this is primarily about not regressing to showing
   `current_status`'s raw value as a heading if that is what today's
   component does — check current behaviour before changing it.
6. Preserve the "constant-shape" rule already documented on
   `emptyOptionalStatusResponse` (TASK-007 §4.8): missing/empty values are
   empty strings, never null. If `title` can legitimately be absent for any
   payload shape TASK-016 ships, confirm whether it follows the same
   empty-string convention or is always populated (ADR-010's mapping always
   resolves to one of six known statuses, each with a non-empty
   `public_title`, so `title` should likely always be non-empty on any
   `success: true` status response — verify, don't assume).

## Constraints

- Do not modify backend code (`the_visaguy` or any other Frappe app) as part
  of this task — this is a `visa_tracker`-only change.
- Do not redeclare the new field's sample values anywhere outside
  `wireContract.ts`; every other test file must import from it, per its own
  documented rule.
- Do not reduce the current 41-test baseline. Report the new total.
- Do not invent the exact wire field name or payload placement (top-level vs.
  per-timeline-item) — verify against TASK-016's actual shipped response
  before writing the fixture, since this task file's author has not seen that
  implementation.

## Validation

- `npm run test` (vitest) — report before/after counts.
- `npm run lint` and `tsc --noEmit` — part of this repository's own `verify`
  script; run at least those two, and ideally the full `npm run verify`.
- `npm run build` — confirm the SPA still builds.
- Visual check (manual or via the project's own preview tooling) that the
  new `title` renders as the heading with `public_message`/`message` as
  supporting copy for at least one status.

## Definition of done

- Types, contract fixtures, contract-conformance test, MSW mocks, and the
  rendering component all updated consistently from the single
  `wireContract.ts` source.
- Full test suite green, count reported and not regressed from 41.
- Lint, typecheck, and build all pass.
- Evidence recorded in this task file or a linked report before moving to
  `completed`.
