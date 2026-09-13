# STATE — visa_tracker parity with visaguy-website-client

## Ground facts (verified by orchestrator — do not re-derive)

- Tracker repo: `/Users/shzd/Projects/tridz/visa_tracker`, branch
  `feat/tracker-site-parity`, created from `feat/tracker-ui-polish` (4fef926).
- Reference repo (READ ONLY, never modify): `/Users/shzd/Projects/tridz/visaguy-website-client`
  — Next.js 15, Tailwind v4, theme in `app/globals.css`, hero in
  `components/home/Hero.tsx` + `HeroFeatures.tsx`, primitives in `components/ui/`.
- **The theme is already ported.** `visa_tracker/src/styles/design-tokens.css` is a
  verbatim copy of the site's `:root` block — identical hex values. Missing only
  `--border-200: #9393934D` and the `--chart-*` set (charts are irrelevant here).
  Do NOT "re-port" the palette; it is correct.
- Real divergence is components + composition, not colour.
- Site status vocabulary (from `components/application/VisaApplicationCard.tsx`):
  Draft, Payment Confirmed, Application Submitted, Application Processing,
  Pending Action.
- The site colours those statuses with raw Tailwind palette classes
  (`bg-yellow-100`, `bg-purple-100`, `bg-orange-100`…), off-token. This is the one
  place the site departs from its own design system. DO NOT copy that approach.
- `@fontsource-variable/geist` is ALREADY a dependency of visa_tracker and is
  currently unused. It provides family `Geist Variable`, weights 100–900, with
  `font-display: swap` already declared. Self-hosted; no CDN.
- Hero assets already copied into `visa_tracker/public/hero/` (curved.png,
  hero_1..4.webp, hero_left_bg.webp, visa.png) and `visa_tracker/public/images/`
  (heroAirplane.svg, heroCurvedLines.svg).
- Commands: `npm run lint`, `npx tsc --noEmit`, `npm run test`, `npm run build`,
  `npm run verify`.
- Executor: Kimi (`kimi -p`, WITHOUT `--auto` — that flag is blocked here).

## Design-standards baseline (driver run on `dist/`, before this branch)

    1 fail · 2 warn
    FAIL  Default type system — body Inter, headings Inter
    WARN  WCAG AA contrast — white on #c6992c = 2.63:1 (primary CTA);
                             #a17307 on #ffffff = 4.22:1 (Support link)
    WARN  Tap targets < 44x44 at 375px — 4 elements
    palette: #fef7e8 86% · #101828 4.6% · #a17307 4.6% · #f9fafb 2.6% · #c6992c 2.2%

## User decisions (asked and answered)

- **U1. Type**: Geist Variable for headings, Inter for body. Resolves the hard ban
  while keeping body copy identical to the marketing site. Uses the existing dep.
- **U2. CTA contrast**: darken the button background to the existing
  `--brand-800 #85610e` and keep white text → 5.71:1, passes AA. The resting gold
  `#c6992c` stays in use for borders, icons and the timeline marker.
- **U3. Hero fidelity**: adopt the site's *visual language* only — two-tone
  headline, feature-row trust points, curved/airplane decorations. The form card
  stays the dominant element. NO destination photo cards in the hero.
- **U4. Assets**: copy everything including the photos. Consequence accepted and
  recorded: the four `hero_*.webp` files land unused for now.

## Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 0 | recon + baseline audit (orchestrator) | this file | done |
| A | type system, contrast, button parity, tap targets (executor) | A-foundation.md | done (6d14272 + 81bb210 fix) |
| B | hero in the site's visual language (executor) | B-hero.md | done (9bef3e6) |
| C | statusTone aligned to real vocabulary (executor) | C-status.md | done (6f01fc8) |
| D | verify + design driver + screenshots (orchestrator) | D-report.md | done (41df7cd) |

## Decisions log

- D1. Do not port the site's nav: it depends on framer-motion, redux, and auth/
  config React contexts. The tracker's Header is already a correct simplified copy.
- D2. Do not port the site's `getStatusColor` raw-palette approach (see ground facts).
- D3. Keep the Base UI button primitive; port the site's button *API and styling*
  (loading spinner, loadingText, outlineSecondary), not its Radix Slot dependency.
