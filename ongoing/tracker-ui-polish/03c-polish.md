# 03c polish pass

## Commit

`fix(ui): hoist brand wash to the page shell and prioritise the form on mobile`

SHA: `94513ed5ff977a848995abbb9c029863ff4d5222`

## Changes by task

### P1 — Hoist brand gradient wash to `PageShell`

- `src/components/layout/PageShell.tsx`
  - Added optional `accent?: boolean` prop (default `false`).
  - Outer wrapper now `relative overflow-hidden`.
  - Renders the gradient wash before `<Header/>` so it spans the full viewport including the transparent header bar.
  - Renders a soft radial accent when `accent={true}`.
- `src/pages/VerificationPage.tsx`
  - Uses `<PageShell accent>`.
  - Removed both local decorative divs.
  - Removed `relative overflow-hidden` from `<section>`.
- `src/pages/StatusPage.tsx`
  - Uses `<PageShell>` (no accent).
  - Removed the local wash div.
  - Removed `relative overflow-hidden` from `<section>`.

### P2 — Prioritise the form card on mobile

- `src/pages/VerificationPage.tsx`
  - Split the left-hand copy/trust column into two explicit grid items.
  - Grid layout now places:
    1. eyebrow + headline + lead (`order-1 lg:col-start-1 lg:row-start-1`)
    2. form card (`order-2 lg:order-none lg:col-start-2 lg:row-start-1 lg:row-span-2 lg:self-center`)
    3. trust bullets (`order-3 lg:order-none lg:col-start-1 lg:row-start-2`)
  - On mobile the form card now sits directly below the lead paragraph; desktop layout is preserved.
  - Trust list remains a `<ul>`.

### P3 — Stop exporting `badgeVariants`

- `src/components/ui/badge.tsx`
  - Confirmed nothing imports `badgeVariants`.
  - Changed `export { Badge, badgeVariants }` to `export { Badge }`, matching `button.tsx`.

### P4 — Add spacing below StatusPage heading

- `src/pages/StatusPage.tsx`
  - Added `mt-2` to the "Live progress for your application." subhead paragraph.

## Gate results

| Gate | Result |
|------|--------|
| `npm run lint` | 1 warning (pre-existing `SessionContext.tsx` fast-refresh warning) |
| `npx tsc --noEmit` | pass |
| `npm run test` | 41 passed, 0 failed |
| `npm run build` | pass |
