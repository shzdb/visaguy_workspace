# B-hero — adopt site hero language on VerificationPage

## Commit

`9bef3e6cfda96c70944d8708a4aed2b718858702`

Changed only `src/pages/VerificationPage.tsx`.

## Final structure

```
<section class="relative py-16 md:py-24 lg:py-28">
  <img mobile curved-lines decoration />
  <div class="container mx-auto grid max-w-6xl gap-10 px-4
              lg:grid-cols-12 lg:items-center lg:gap-8 lg:px-20">

    <!-- copy column -->
    <div class="relative order-1 lg:col-span-6 lg:row-start-1">
      <img airplane decoration />
      <Badge tone="brand">Secure application tracking</Badge>
      <h1>
        <span class="text-tertiary">Visa</span>
        <span class="text-brand-800">Tracking.</span>
      </h1>
      <p>Enter your passport number and date of birth...</p>
    </div>

    <!-- form column -->
    <div class="relative order-2 w-full max-w-md
                lg:order-none lg:col-span-5 lg:col-start-8 lg:row-span-2
                lg:justify-self-end lg:self-center">
      <img curved-blob decoration />
      <Card class="shadow-card">
        ...IdentityVerificationForm + fine-print Lock block...
      </Card>
    </div>

    <!-- feature row -->
    <ul class="order-3 flex flex-wrap items-center gap-x-6 gap-y-3
               lg:order-none lg:col-span-6 lg:col-start-1 lg:row-start-2">
      <li>ShieldCheck — Private by design</li>
      <li>Clock — Always current</li>
      <li>Lock — No account needed</li>
    </ul>
  </div>
</section>
```

## Decoration positioning

All decorative images are `aria-hidden="true"`, `pointer-events-none`, `alt=""`, and `-z-10`.

- `/images/heroCurvedLines.svg` — full-bleed behind the headline area on mobile only:  
  `absolute inset-x-0 top-24 -z-10 w-full opacity-60 md:hidden`
- `/hero/curved.png` — soft blob behind the form card on desktop only:  
  `hidden lg:block absolute -right-20 -top-20 -z-10 w-80 opacity-70`
- `/images/heroAirplane.svg` — small accent near the headline on tablet and up:  
  `hidden md:block absolute -right-4 -top-8 -z-10 w-16`

`PageShell` already carries `overflow-hidden`, so absolutely positioned decorations are clipped at the viewport edge. No horizontal scroll is introduced at 375 px; the only mobile decoration is `inset-x-0 w-full`.

## Contrast reasoning

- The reference site uses `text-brand-600` (#c6992c) for the accent word. That measures only ~2.42:1 against `--brand-background` and ~2.63:1 on white, failing WCAG AA even for large text (3:1).
- This implementation uses `text-brand-800` (#85610e), which gives 5.26:1 on the wash — comfortably passing WCAG AA. It is also consistent with the Phase A primary button.
- Feature-row icons use `text-brand-700` instead of `text-brand-600`; `brand-600` is below the 3:1 non-text minimum on the wash, while `brand-700` clears it.

## Gates

| Gate | Result |
|------|--------|
| `npm run lint` | 1 pre-existing warning in `src/context/SessionContext.tsx`; no new warnings added |
| `npx tsc --noEmit` | pass |
| `npm run test` | 41 passed / 0 failed |
| `npm run build` | pass |
| `grep -c '<ol' src/pages/VerificationPage.tsx` | 0 |
