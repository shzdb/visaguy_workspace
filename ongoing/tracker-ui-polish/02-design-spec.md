# 02 — Design spec (orchestrator triage)

Authoritative spec for phases 3a and 3b. The executor implements exactly this.
Anything not listed here is OUT OF SCOPE.

## Global rules

- Use ONLY existing design tokens via their Tailwind theme names, already mapped
  in `src/index.css`: `brand-500/600/700/800`, `brand-background`, `primary-900`,
  `tertiary-600`, `quaterary-500`, `muted-foreground`, `foreground-quinary`,
  `bg-secondary`, `border-secondary`, `secondary-border`, `success-25/200/500/900`,
  `destructive`, `red-dark`, `shadow-card`, `shadow-button`, `radius-*`.
- Do NOT add dependencies. Do NOT add new colours or hex literals in components.
- Do NOT add persistence, analytics, or any network call. Do NOT touch
  `src/api/`, `src/hooks/`, `src/context/`, `src/lib/validation/`, `src/types/`,
  `src/mocks/`, or any `*.test.*` file.
- Do NOT alter user-facing copy that tests assert on (see 01-recon.md).
- Keep every existing `aria-*`, `role`, `aria-live`, `tabIndex`, `htmlFor`/`id`
  wiring exactly as it is. Status must never be conveyed by colour or icon alone —
  a text label always accompanies it.
- All icons are decorative unless they are the only content: `aria-hidden="true"`.

## A. New file: `src/components/ui/badge.tsx`

A presentational `Badge` following the local shadcn-style conventions (`cva` +
`cn`, `data-slot="badge"`, `React.ComponentProps<"span">`).

Base classes: `inline-flex items-center gap-1.5 rounded-full border px-2.5 py-1
text-xs font-semibold`.

Variants (`tone`):

- `neutral`  — `border-secondary-border bg-bg-secondary text-secondary-foreground`
- `brand`    — `border-brand-500/40 bg-brand-background text-brand-800`
- `success`  — `border-success-200 bg-success-25 text-success-900`
- `critical` — `border-destructive/20 bg-destructive/10 text-red-dark`

Default tone: `neutral`. Export `Badge` and `badgeVariants`.

## B. New file: `src/lib/statusTone.ts`

```ts
export type StatusTone = "neutral" | "brand" | "success" | "critical"
export function statusTone(status: string): StatusTone
```

Case-insensitive substring match on the trimmed status, evaluated in this order
(first match wins), with documented reasoning that the backend status string is
free text so unknown values must degrade safely:

1. `critical` if it contains any of: `reject`, `refus`, `declin`, `cancel`, `withdraw`, `fail`
2. `success`  if it contains any of: `approv`, `issued`, `grant`, `complet`, `deliver`, `collect`, `ready`
3. `brand`    if it contains any of: `progress`, `working`, `process`, `review`, `submit`, `lodg`, `receiv`, `pending`
4. `neutral`  otherwise

Note in a comment that ordering matters (e.g. "Visa Rejected — application
complete" must resolve to `critical`, not `success`).

## C. Rewrite: `src/components/tracking/StatusSummary.tsx`

Same props, same data, same masked-only rule. New composition:

1. Card with `overflow-hidden p-0`-style header band: a `CardHeader` on a
   `bg-brand-background` wash separated by `border-b border-border-secondary`.
   Inside it, stacked:
   - `<Badge tone={statusTone(status.current_status)}>` containing a small
     lucide icon (`aria-hidden`) plus the literal `status.current_status` text.
     The badge icon: `CheckCircle2` for success, `AlertCircle` for critical,
     `Loader`/`RefreshCw` (static, no spin) for brand, `CircleDot` for neutral.
   - `CardTitle` = `status.current_status` rendered at `text-xl md:text-2xl`.
   - `CardDescription` = `status.public_message`.
   (Both the badge and the title carry `current_status`; that is intentional and
   keeps `getAllByText` passing.)
2. `CardContent` keeps the `<dl>` grid but restyled: `sm:grid-cols-2 gap-3`,
   each cell `rounded-xl border border-border-secondary bg-white p-4`, `dt` as
   `text-xs font-semibold uppercase tracking-wide text-quaterary-500`, `dd` as
   `text-sm font-semibold text-primary-900`. Prefix each `dt` with a small
   lucide icon inside a `flex items-center gap-2` wrapper: `User` (Applicant),
   `BookUser`/`IdCard` (Passport), `MapPin` (Destination), `Stamp`/`FileBadge`
   (Visa type). Use icon names that actually exist in the installed
   `lucide-react` — verify by import, and fall back to `Circle` if unsure.
   Keep the two conditional cells (`destination`, `visa_type`) conditional.
3. Footer row: keep "Last updated: …" and the conditional support link, but move
   them into a `CardFooter`-style block with `border-t border-border-secondary
   pt-4 mt-2`, "Last updated" prefixed by a `Clock` icon.

## D. Rewrite: `src/components/tracking/StatusTimeline.tsx`

Same props, same ICON_MAP behaviour and fallback, same API order (newest first),
same `return null` on empty.

Visual: a connected vertical rail.

- Wrapper keeps the `<h2>` "Timeline" (restyle to
  `text-lg font-semibold text-primary-900`), then the `<ol>`.
- The `<ol>` is `relative space-y-0`. Each `<li>` is `relative flex gap-4 pb-6
  last:pb-0` and contains, in order:
  - a marker column: `relative flex w-9 shrink-0 justify-center`, containing
    - the rail segment: an absolutely positioned `span` (`aria-hidden`)
      `absolute left-1/2 top-9 -ml-px h-[calc(100%-1.5rem)] w-0.5`, coloured
      `bg-border-secondary`. Render it for every item EXCEPT the last one, so
      the rail does not overhang past the final marker.
    - the marker itself: a `size-9 rounded-full flex items-center justify-center
      border` holding the mapped icon at `size-4`.
  - the content column: `flex-1 pt-1` with the existing `<p>` status, `<p>`
    message and `<time>`, restyled as `text-sm font-semibold text-primary-900`,
    `text-sm text-muted-foreground`, `text-xs text-foreground-quinary` and given
    `mt-*` spacing.
- Current vs. past. `items[0]` is the newest/current entry:
  - current marker: `border-brand-600 bg-brand-600 text-white shadow-button`
    plus a soft halo `ring-4 ring-brand-background`.
  - past markers: `border-border-secondary bg-white text-quaterary-500`.
  - The current `<li>`'s status `<p>` additionally renders a visually-hidden
    span `<span className="sr-only">Current status: </span>` BEFORE the status
    text so the state is not colour-only. Add an `.sr-only` utility only if
    Tailwind does not already provide it (Tailwind v4 does — just use it).
  - Do NOT render any node for a step that has not happened.
- The `<li>` key stays `item.status + item.effective_on`.

## E. Rewrite: `src/pages/VerificationPage.tsx`

Two-column hero. Structure:

```
<PageShell>
  <section class="relative overflow-hidden">
    {/* decorative wash — aria-hidden, pointer-events-none, absolute inset-0 */}
    <div class="pointer-events-none absolute inset-0 -z-10 bg-[linear-gradient(180deg,var(--brand-background)_0%,var(--background)_65%)]" aria-hidden="true" />
    {/* soft radial accent, top-right, aria-hidden */}
    <div class="pointer-events-none absolute -right-24 -top-24 -z-10 size-96 rounded-full bg-brand-500/10 blur-3xl" aria-hidden="true" />

    <div class="container mx-auto grid max-w-6xl items-center gap-10 px-4 py-12 md:py-16 lg:grid-cols-2 lg:gap-16 lg:px-20">
      <div>  {/* left: copy */}
        eyebrow chip, h1, lead paragraph, trust list
      </div>
      <div class="lg:justify-self-end w-full max-w-md"> {/* right: form card */}
        <Card class="shadow-card"> ... existing content ... </Card>
      </div>
    </div>
  </section>
</PageShell>
```

Left column contents:

- Eyebrow: a `Badge tone="brand"` with a `ShieldCheck` icon and the text
  `Secure application tracking`.
- `<h1 className="mt-4 text-4xl font-bold leading-tight tracking-tight text-primary-900 md:text-5xl">`
  with the text `Track your visa application` — keep this exact string, and keep
  it as the page's only `h1`.
- Lead `<p className="mt-4 max-w-prose text-base text-tertiary-600 md:text-lg">`:
  `Enter your passport number and date of birth to see exactly where your
  application stands — updated straight from our case team.`
- A trust list. MUST be a `<ul>` (never an `<ol>` — the e2e test takes the first
  `<ol>` in the document as the timeline; on this page there must be none).
  `<ul className="mt-8 space-y-4">`, three `<li className="flex items-start gap-3">`
  each with a `size-9 shrink-0 rounded-lg bg-brand-background` icon tile
  (icon `size-4 text-brand-700`, `aria-hidden`) and a two-line text block
  (`text-sm font-semibold text-primary-900` + `text-sm text-muted-foreground`):
  1. `ShieldCheck` — "Private by design" / "Your details are never stored on this website."
  2. `Clock` — "Always current" / "Status and timeline come live from your case file."
  3. `Lock` — "No account needed" / "Passport number and date of birth are all it takes."

Right column: the existing `Card` unchanged in content — `CardHeader` with
"Verify your identity" + "Enter the details you provided with your application.",
`CardContent` with `<IdentityVerificationForm />` and the existing fine-print
`<p>`. Restyle the fine print to sit in a `rounded-lg bg-bg-secondary p-3` block
with a `Lock` icon, keeping its text unchanged.

On mobile the grid stacks: copy first, then the form card, then nothing else —
this is the natural DOM order, so no order utilities are needed.

## F. Edit: `src/pages/StatusPage.tsx`

Minimal changes only:

- Wrap the section in the same decorative wash pattern as E (top gradient only,
  no radial blob), `aria-hidden` + `pointer-events-none` + `-z-10`.
- Keep the `<h1>` element, its `ref`, `tabIndex={-1}`, and its exact text
  `Application status`; add `md:text-4xl`-consistent styling as it already has,
  plus a short subhead `<p className="mt-2 text-sm text-tertiary-600">` reading
  `Live progress for your application.` rendered ONLY when `status` is truthy.
- Widen the column from `max-w-2xl` to `max-w-3xl`.
- Action buttons: keep both buttons, their exact labels, handlers, and disabled
  logic. Only restyle the wrapper to `flex flex-col gap-3 sm:flex-row` (already
  is) and give the primary "Refresh status" button `size="md"` and a `RefreshCw`
  icon (`aria-hidden`), the secondary an `ArrowLeft` icon.
- Do not change the branching logic, the focus effect, or `startOver`.

## Out of scope (do not touch)

- Header / Footer components (nav trim is a later tier).
- Animations / `tw-animate-css` wiring.
- Dark mode tokens or the `dark` custom variant.
- `LoadingState`, `ErrorState`, `LockoutState`, `ExpiredSessionState` — leave
  them byte-identical; their copy is asserted by tests.
- `src/assets/hero.png` — leave it unused.
