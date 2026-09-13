# 03b — Verification page rebuild

## Commit

`210a742` — `feat(ui): rebuild verification page as a two-column hero with trust signals`

## What changed

Only `src/pages/VerificationPage.tsx` was modified.

### Final structure

```
<PageShell>
  <section class="relative overflow-hidden">
    {/* decorative full-bleed gradient wash */}
    <div aria-hidden="true" class="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,var(--brand-background)_0%,var(--background)_65%)]" />
    {/* soft top-right radial accent */}
    <div aria-hidden="true" class="pointer-events-none absolute -right-24 -top-24 -z-10 size-96 rounded-full bg-brand-500/10 blur-3xl" />

    <div class="container mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 md:py-16 lg:grid-cols-2 lg:gap-16 lg:px-20">
      {/* left: copy */}
      <div>
        <Badge tone="brand">
          <ShieldCheck aria-hidden="true" />
          Secure application tracking
        </Badge>
        <h1>Track your visa application</h1>
        <p class="lead">Enter your passport number...</p>
        <ul class="trust-list">
          <li>ShieldCheck — Private by design...</li>
          <li>Clock — Always current...</li>
          <li>Lock — No account needed...</li>
        </ul>
      </div>

      {/* right: form card */}
      <div class="w-full max-w-md lg:justify-self-end">
        <Card class="shadow-card">
          <CardHeader>
            <CardTitle>Verify your identity</CardTitle>
            <CardDescription>Enter the details...</CardDescription>
          </CardHeader>
          <CardContent>
            <IdentityVerificationForm />
            <div class="rounded-lg bg-bg-secondary p-3">
              <Lock aria-hidden="true" />
              <p>Your details are used only...</p>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  </section>
</PageShell>
```

### Classes used

- Section wrapper: `relative overflow-hidden`
- Gradient wash: `pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,var(--brand-background)_0%,var(--background)_65%)]`
- Radial accent: `pointer-events-none absolute -right-24 -top-24 -z-10 size-96 rounded-full bg-brand-500/10 blur-3xl`
- Container: `container mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 md:py-16 lg:grid-cols-2 lg:gap-16 lg:px-20`
- Left column: default grid placement
- Right column: `w-full max-w-md lg:justify-self-end`
- Eyebrow Badge: `Badge tone="brand"` with `ShieldCheck className="size-3.5" aria-hidden="true"`
- H1: `mt-4 text-4xl font-bold leading-tight tracking-tight text-primary-900 md:text-5xl`
- Lead: `mt-4 max-w-prose text-base text-tertiary-600 md:text-lg`
- Trust list: `mt-8 space-y-4`
- Trust item: `flex items-start gap-3`
- Icon tile: `flex size-9 shrink-0 items-center justify-center rounded-lg bg-brand-background`
- Icon: `size-4 text-brand-700` with `aria-hidden="true"`
- Item title: `text-sm font-semibold text-primary-900`
- Item body: `text-sm text-muted-foreground`
- Card: `shadow-card`
- Fine-print block: `mt-4 flex items-start gap-2 rounded-lg bg-bg-secondary p-3`
- Fine-print icon: `mt-0.5 size-4 shrink-0 text-muted-foreground` with `aria-hidden="true"`
- Fine-print text: `text-xs text-muted-foreground`

### Copy preserved byte-identically

- `<h1>`: `Track your visa application` (still the only `h1` on the page)
- `CardTitle`: `Verify your identity`
- `CardDescription`: `Enter the details you provided with your application.`
- Fine-print paragraph: `Your details are used only to look up your application and are never stored by this website.`

## Deviations from spec

None. The implementation follows Section E of `02-design-spec.md` exactly.

Notes:

- The spec calls for giving the Card `shadow-card`; the project's `Card` component already applies `shadow-card` by default, but the `className="shadow-card"` prop was passed explicitly to satisfy the instruction.
- The spec does not prescribe a layout utility for the fine-print icon + text pair; a `flex items-start gap-2` wrapper was added so the `Lock` icon sits inline with the paragraph while keeping the `rounded-lg bg-bg-secondary p-3` block styling exactly as specified.
- The badge icon size is `size-3.5`, which fits the `text-xs` badge text and `gap-1.5` base spacing. The spec did not mandate a size.

## Accessibility / test constraints

- The trust list is a `<ul>` with three `<li>` elements.
- `grep -c '<ol' src/pages/VerificationPage.tsx` returns `0`.
- All decorative icons have `aria-hidden="true"`.
- The wash and radial accent are `aria-hidden="true"`, `pointer-events-none`, and `-z-10`.
- No files were modified other than `src/pages/VerificationPage.tsx`.

## Gate results

| Gate | Result |
|------|--------|
| `npm run lint` | pass (2 pre-existing warnings only: `SessionContext.tsx` and `badge.tsx` `only-export-components`) |
| `npx tsc --noEmit` | pass |
| `npm run test` | 41 passed / 0 failed (5 test files) |
| `npm run build` | pass |
| `grep -c '<ol' src/pages/VerificationPage.tsx` | `0` |
| `git diff --name-only HEAD` (pre-commit) | `src/pages/VerificationPage.tsx` only |
