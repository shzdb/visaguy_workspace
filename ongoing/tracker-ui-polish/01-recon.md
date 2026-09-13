# 01 — Recon (orchestrator, direct)

Performed by reading source and running the app at http://localhost:5174.

## Current UI state

`/` (VerificationPage): a `max-w-md` card centred in a large white void. Header
logo bar + one-item nav. No hero, no trust signals, no use of the brand wash.
Brand gold appears exactly once in the whole app — on the submit button.

`/status` (StatusPage): `max-w-2xl` column. `StatusSummary` is a plain Card whose
`CardTitle` is the raw `current_status` string with no visual status semantics.
`StatusTimeline` is a flat `<ol>` where each `<li>` has a single 2px left border —
no rail continuity, no distinction between the current entry and older ones.

## Assets / tokens

- `src/styles/design-tokens.css` is complete and on-brand; most tokens unused.
- `--color-success-*`, `--color-destructive`, `--color-brand-background`,
  `--shadow-card`, `--shadow-input-focus` are defined and never referenced.
- `tw-animate-css` is a dependency and is never imported.
- `@custom-variant dark` is declared in `index.css` with no dark token block.
- `src/assets/hero.png` (343x361) is unreferenced and is a purple isometric
  abstract — clashes with the gold brand. Rejected.

## API contract facts that constrain the design

From `src/types/tracking.ts` and `src/test/contract/wireContract.ts`:

- `StatusResponse` has exactly 9 keys; optional values arrive as `""`, never null.
- `timeline: StatusTimelineItem[]` is newest-first history. Fields are
  `status`, `message`, `effective_on`, `icon` (hint string, may be `""`).
- There is no progress/percentage/stage-count field. Any "step 2 of 5" or
  greyed-out future step would be fabricated. Do not add one.
- `current_status` is free text from the backend. Any tone/colour mapping must
  fall back safely for unknown strings, and colour must never be the sole
  carrier of meaning (accessibility + existing project convention).

## Test constraints discovered (these WILL fail if violated)

`src/test/e2e/trackingFlow.test.tsx`:

- `document.querySelector("ol")` must resolve to the timeline list. The first
  `<ol>` in the rendered document has to be the timeline. (The header nav uses
  `<ul>`, which is why it works today.)
- The timeline `<ol>` must contain exactly one `<li>` per timeline item, in API
  order, each containing that item's `status` and `message` text.
- `getAllByText(current_status)` and `getAllByText(public_message)` must be
  non-empty on the status page.
- `applicant_name_masked` and `passport_number_masked` must render as text.
- The `/application status/i` heading must receive focus after load.
- Form must keep labels "Passport number" / "Date of birth" and a button
  matching `/track application/i`.
- Error/lockout copy must stay byte-identical ("Something went wrong",
  "Too many attempts", "about N minutes").
