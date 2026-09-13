# STATE — visa_tracker UI beautification (Tier 1)

## Ground facts (verified by orchestrator — do not re-derive)

- Repo under change: `/Users/shzd/Projects/tridz/visa_tracker` (macOS path; the
  workspace task docs say `/home/shzd/...` — that path is stale/Linux, ignore it).
- Branch: `feat/tracker-ui-polish`, created from `main` at `a6a07a9`. Checkout was clean.
- Stack: Vite 8 + React 19 + TypeScript + Tailwind CSS v4 + shadcn-style local UI
  primitives + Base UI button + react-router-dom 7 + react-hook-form + zod + lucide-react.
- Scripts: `npm run lint` (oxlint), `npm run test` (vitest), `npm run build`,
  `npm run verify` (lint + tsc --noEmit + test + build).
- Design tokens already exist and are correct: `src/styles/design-tokens.css`
  (brand gold `--brand-600 #c6992c`, wash `--brand-background #fef7e8`,
  `--primary-900 #101828`, success/destructive ramps, radius + shadow scales).
  Tailwind theme mapping lives in `src/index.css` under `@theme inline`.
- Only two routes: `/` (VerificationPage) and `/status` (StatusPage).
- Dev server runs at http://localhost:5174 (5173 was taken).
- `src/assets/hero.png` is unused AND off-brand (purple isometric). DECISION: do not use it.
- Executor: Kimi Code CLI (`kimi -p`), run with `--auto`.

### Hard product constraints

- ADR-005: passport number, DOB and the session token must stay in React state
  only — never localStorage/sessionStorage/cookies/URL/logs/analytics. No new
  persistence or telemetry may be introduced by UI work.
- The status API returns ONLY history, newest-first. There is no notion of
  future/pending steps in the contract. The UI must NOT invent upcoming steps.
- The server returns masked PII only. Never render or derive unmasked values.

## Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 1 | recon (orchestrator, already done) | 01-recon.md | done |
| 2 | design spec / triage (orchestrator) | 02-design-spec.md | done |
| 3a | status page: badge + summary + timeline (executor) | 03a-status-page.md | done (ca39d19) |
| 3a-fix | corrective pass on 7 review defects (executor) | 03a-status-page.md | done (b58bd86) |
| 3b | verification page hero (executor) | 03b-verification-page.md | done (210a742) |
| 3c | browser-review polish: wash + mobile order (executor) | 03c-polish.md | done (94513ed) |
| 4 | badge label fix + full verify (executor) | 04-verify.md | done (4fef926) |
| 5 | visual check + final report (orchestrator) | 05-report.md | done |

## Decisions log

- D1. Scope = Tier 1 only (verification hero, status stepper, status badge).
  Tier 2 (header/footer trim, motion, shadow polish) and Tier 3 (dark mode)
  deferred — they are listed in 02-design-spec.md as out of scope.
- D2. `hero.png` rejected as off-brand; use token-driven CSS decoration instead.
- D3. Branch in place rather than a separate git worktree: the checkout was
  clean and the running dev server must observe the changes for visual review.
- D4. Timeline renders history only: newest item = "current" (brand, filled),
  older items = "completed" (muted). No fabricated future nodes.

- D5. Two executor phases needed orchestrator-authored corrective passes: the
  timeline rail was rendered on the wrong end of the list (3a-fix F1), and the
  brand wash was clipped to the centred container leaving a seam under the
  header (3c P1). Both were caught by orchestrator diff review and in-browser
  review respectively, not by the executor's own gates — the gates (lint/tsc/
  test/build) are blind to layout.
- D6. Kimi was dispatched WITHOUT `--auto`; that flag is blocked by this
  session's permission classifier. Plain `kimi -p` reads, writes, and runs
  commands fine, so the pattern works unchanged.
