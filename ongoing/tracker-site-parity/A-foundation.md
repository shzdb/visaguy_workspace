# Phase A — Foundation parity

## Commit

`6d14272 feat(ui): add display face, fix CTA contrast and port the site button API`

## Changes by task

### A1. Type system

- `src/main.tsx` — added `import "@fontsource-variable/geist"` above `import "./index.css"`.
- `src/styles/design-tokens.css` — updated `--font-family-heading` to `Geist Variable` (body `--font-family-sans` left as Inter).
- `src/index.css` — inside `@layer base`, applied the heading family to `h1, h2, h3` with `letter-spacing: -0.02em`.

### A2. CTA contrast

- `src/components/ui/button.tsx` — `default` variant now uses `bg-brand-800 text-primary-foreground shadow-xs hover:bg-tertiary`. White on `#85610e` is 5.71:1; hover on `#543f0d` is darker still. `--primary` gold remains available for borders, icons, and timeline markers.

### A3. Button API parity

- `src/components/ui/button.tsx` — kept Base UI `ButtonPrimitive`; ported the reference site's API:
  - Added `cursor-pointer` to the base class string.
  - Added `outlineSecondary` variant: `border bg-transparent border-brand-600 text-brand-600`.
  - Added `loading?: boolean` and `loadingText?: string` props.
  - When `loading` is true the button disables itself, sets `aria-busy`, renders an inline spinner before the label, and renders `loadingText` when provided.
  - Ported the reference spinner SVG with the per-variant `spinnerColorMap` and added the `outlineSecondary` entry. Spinner has `aria-hidden="true"` and `focusable="false"`.
- `src/index.css` — added `@media (prefers-reduced-motion: reduce) { .animate-spin { animation: none; } }` so the spinner is inert under reduced motion.

### A4. Loading API call sites

- `src/components/tracking/IdentityVerificationForm.tsx` — submit button now uses `loading={isPending} loadingText="Verifying…"` with children `Track application`. Rendered text is byte-identical to the previous implementation.
- `src/pages/StatusPage.tsx` — refresh button now uses `loading={loading} loadingText="Refreshing…"`, children `Refresh status`, and keeps its `RefreshCw` icon, `size="md"`, `variant="secondary"`, and equivalent `disabled={loading}` behaviour.

### A5. Tap targets and contrast

- `src/components/layout/Header.tsx` — hamburger button now has `min-h-11 min-w-11` with `items-center justify-center` so it is at least 44×44 at 375px. The three bars keep their original sizing and all aria wiring is unchanged.
- `src/components/layout/Footer.tsx` — logo link and Support link are now `inline-flex min-h-11 items-center`, giving both a 44px tap target.
- `src/components/layout/Footer.tsx` — Support link colour changed from `text-brand-700` to `text-brand-800` (5.71:1 on white); hover class preserved.

### A6. Missing token

- `src/styles/design-tokens.css` — added `--border-200: #9393934D;` alongside the other border tokens.
- `src/index.css` — mapped `--color-border-200: var(--border-200);` in the `@theme inline` block.

## Gate results

| Gate | Command | Result | Notes |
|------|---------|--------|-------|
| Lint | `npm run lint` | pass | 2 warnings (pre-existing pattern): `only-export-components` in `src/components/ui/button.tsx` (export of `buttonVariants`) and `src/context/SessionContext.tsx` |
| Type check | `npx tsc --noEmit` | pass | No errors |
| Tests | `npm run test` | pass | 41 passed / 0 failed |
| Build | `npm run build` | pass | Production build succeeded |
