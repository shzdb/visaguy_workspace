# D — Final report: site parity + design standards

## Outcome

Branch `feat/tracker-site-parity`, 6 local commits on top of
`feat/tracker-ui-polish`. Nothing pushed. Working tree clean.

Design-standards driver, run on the production build at 375/768/1024/1440:

| run | result |
|---|---|
| baseline (before this branch) | **1 fail · 2 warn** |
| after phases A–C | 0 fail · 1 warn |
| final | **0 fail · 0 warn** |

    palette: #fef7e8 86.5%  #85610e 6.6%  #101828 4.7%  #f9fafb 2.2%
    type:    Geist Variable over Inter

`npm run verify`: oxlint 1 pre-existing warning (`SessionContext.tsx`),
`tsc --noEmit` clean, **55/55 tests** across 6 files (was 41 — Phase C added 14),
build succeeds.

## What the audit forced that a code review would not have

1. **The brand's primary CTA failed WCAG AA.** White on `--primary` #c6992c is
   2.63:1. This is the reference site's own `--primary`/`--primary-foreground`
   pairing, so the defect exists on thevisaguy.com too. Fixed here by moving the
   button to the existing `--brand-800` #85610e (5.71:1) with `--tertiary`
   #543f0d on hover (9.6:1). The resting gold is retained for borders, icons and
   the timeline marker. **Worth reporting upstream to the site team.**
2. **The site's two-tone headline accent also fails contrast.** `text-brand-600`
   measures 2.42:1 on the brand wash and 2.63:1 on white — under even the 3:1
   large-text threshold. The tracker uses `brand-800` for the accent word
   instead. Same device, accessible tint.
3. **Inter over Inter tripped the ban on a default type system.** Resolved per
   the user's decision: `Geist Variable` (already a dependency, previously
   unused, self-hosted, `font-display: swap`) for h1–h3; body copy stays Inter,
   identical to the site.
4. **Four tap targets were under 44×44** at 375px: the header hamburger, the
   footer logo link and its image, and the "Support" link. All fixed.
5. The `Support` link at `--brand-700` was 4.22:1 — just under AA. Now
   `brand-800`.

## What the screenshots caught that the driver could not

- The two-tone headline initially used `text-tertiary` + `text-brand-800`, two
  browns close enough that the device read as mono-tone. Changed to
  `primary-900` + `brand-800` so it actually reads as two tones.
- The feature row wrapped 2 + 1 in a 6-column copy column. Widened the copy
  column to `lg:col-span-7`; all three sit on one line.
- A dead band above the footer at 1440px. `<main>` is now a column flex
  container and the hero is `flex flex-1 items-center`, so it occupies the
  viewport deliberately instead of collapsing to content height.

## Divergences from the reference site (deliberate, recorded)

- **Contrast**: see 1 and 2 above. The tracker is more accessible than the site.
- **`getStatusColor`**: the site colours statuses with raw Tailwind palette
  classes (`bg-yellow-100`, `bg-purple-100`, `bg-orange-100`), the one place it
  departs from its own tokens. `statusTone` stays token-driven instead.
- **Nav**: not ported. It depends on framer-motion, redux and auth/config
  contexts. The tracker's Header remains a simplified copy of the visual shell.
- **Hero**: visual language adopted, composition adapted. This is a utility page
  whose single job is the lookup, so the form card stays dominant and the
  destination photo cards are omitted.

## Imagery (added after the parity pass, commit 4ff9fcb)

The user reopened the earlier "no destination photo cards" decision. Now in use:

- `hero_3.webp` (Greece) and `hero_2.webp` (Vietnam) as tilted decorative cards
  in the hero's lower-left, reproducing the reference site's signature
  photo-tile treatment with its hover rotate/scale lift. `hidden lg:block`, so
  the mobile form-first order is untouched. Both `aria-hidden` with `alt=""`,
  `loading="lazy"`, and explicit width/height to avoid layout shift. Hover
  transforms are disabled under `motion-reduce`.
- `hero_left_bg.webp` as a faint airmail-postmark texture behind that photo
  cluster. It was first placed behind the headline, which read as a smudge under
  the type; moved so the stamp motif sits with the photos, where it belongs.

Below `lg` the photo cluster does not render, so mobile and tablet were left with
only `heroCurvedLines.svg`. Two decorations now carry across:
`heroAirplane.svg` (was `md:`-gated; now smaller and pinned to `right-0` on
mobile so it bleeds off the corner without widening the page), and the
`hero_left_bg.webp` postmark, placed bottom-right in the bare band under the
feature row where that row's second line leaves space. Checked by eye at 375 and
768 — the audit's contrast check skips raster backgrounds, so it could not have
caught text sitting over it.

**Declined, with reasons** — destination photography on the status page:

1. Mechanically impossible to do honestly. `destination` is free text, the
   status contract has nine fixed keys and no image URL, and only four photos
   exist (Russia, Vietnam, Greece, France — the fixture's destination is the
   UAE). Most users would get nothing, and a fallback risks showing the wrong
   country beside someone's visa status.
2. Tonally wrong. That page also renders "Visa Rejected" and "Pending Action".
   Aspirational travel photography beside a rejection reads as cruel. Decorative
   stamps would be acceptable there; destinations are not.

Still unreferenced (~110KB): `hero_1.webp` (Russia), `hero_4.webp` (France),
`visa.png`. Kept at the user's request; delete if they stay unused.

## Verification ladder

- **runtime-verified**: driver at four widths on the production build; 1440 and
  375 screenshots read by the orchestrator; status card + timeline rendered from
  the contract fixture through a temporary preview route, since removed.
- **runtime-verified**: `npm run verify` run directly by the orchestrator.
- **statically-verified**: branch diff adds no `localStorage`, `sessionStorage`,
  `document.cookie` or `analytics`; no file under `src/api/`, `src/hooks/`,
  `src/context/`, `src/types/` or `src/mocks/` modified. ADR-005 intact.
- **unverifiable**: pixel parity with the live thevisaguy.com deployment — only
  the local repo was available as reference.

## Executor notes

Phase A shipped a corrupted SVG arc (`a7 7 7 0` — an extra token in the
reference's path) and a prop-spread ordering bug where `{...props}` came after
`disabled`, both of which lint, types, tests and build passed cleanly. Caught by
orchestrator diff review and fixed directly in 81bb210.
