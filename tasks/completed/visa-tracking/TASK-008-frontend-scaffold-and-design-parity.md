---
id: TASK-008
feature: FEAT-001
title: Frontend scaffold and design parity
status: completed
repository:
  - visa_tracker
  - visaguy-website-client
worktree: /home/shzd/Projects/tridz/visa_tracker
reference_repository: /home/shzd/Projects/tridz/visaguy-website-client
owners: []
depends_on:
  - TASK-001
  - ADR-005
expected_files:
  - /home/shzd/Projects/tridz/visa_tracker/package.json
  - /home/shzd/Projects/tridz/visa_tracker/src/main.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/App.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/index.css
  - /home/shzd/Projects/tridz/visa_tracker/src/lib/utils.ts
  - /home/shzd/Projects/tridz/visa_tracker/components.json
  - /home/shzd/Projects/tridz/visa_tracker/src/components/ui/button.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/ui/input.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/ui/card.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/ui/alert.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/ui/label.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/layout/Header.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/layout/Footer.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/layout/PageShell.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/styles/design-tokens.css
  - /home/shzd/Projects/tridz/visa_tracker/src/types/tracking.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/api/client.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/mocks/tracking.ts
  - /home/shzd/Projects/tridz/visa_tracker/index.html
  - /home/shzd/Projects/tridz/visa_tracker/vite.config.ts
  - /home/shzd/Projects/tridz/visa_tracker/tsconfig.json
created: 2026-07-21
updated: 2026-07-21
---

# TASK-008: Frontend scaffold and design parity

## Objective

Bring the existing `/home/shzd/Projects/tridz/visa_tracker` Vite scaffold into visual and structural parity with the approved VisaGuy consumer website (`visaguy-website-client`), and prepare the component layer for the tracking flow implemented in TASK-009. This task is limited to design tokens, shared layout, presentational components, accessibility, responsive behavior, and typed API seams with mocks. No real API flow, verification logic, or session handling is implemented here.

## Context

FEAT-001 requires a standalone public visa-tracking SPA at `/home/shzd/Projects/tridz/visa_tracker` using React, Vite, TypeScript, React Router, Tailwind CSS, shadcn/ui, Axios, React Hook Form, and Zod. TASK-001 already initialized the repository with a Vite scaffold and an initial Git commit. The consumer website `visaguy-website-client` is the canonical read-only visual reference: its logo/header/footer composition, typography, color system, spacing, radius, shadows, and component treatment must be reused so the tracker feels like a native VisaGuy surface. Next.js-specific code must not be copied into the Vite app.

ADR-005 defines the public security boundary: the SPA must not store passport number, DOB, or session token in `localStorage`, analytics, or URLs. TASK-008 establishes the architectural seams that TASK-009 will wire to real API calls, while keeping all runtime API verification for TASK-010 or a dedicated test site.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `features/ongoing/visa-tracking/03-frontend-design-and-layout.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- Local frontend repository: `/home/shzd/Projects/tridz/visa_tracker`
- Read-only design reference: `/home/shzd/Projects/tridz/visaguy-website-client`

## Required behaviour

### 1. Preserve and clean the existing scaffold

1.1. Keep the existing Vite + React + TypeScript + Tailwind CSS + shadcn/ui scaffold created by TASK-001. Do not replace the build tooling or package manager.

1.2. Ensure `package.json` scripts include `dev`, `build`, `lint`, and `preview`. `build` must produce a production bundle without errors.

1.3. Keep `tsconfig.json`, `vite.config.ts`, `components.json`, and `tailwind.config.js` aligned with the existing shadcn/ui setup. Only extend them when required for design parity or path aliases.

1.4. Initialize Git if not already initialized by TASK-001 and commit all TASK-008 changes locally. No Git remote is required.

### 2. Design tokens and global styles

2.1. Audit `visaguy-website-client` for the consumer visual system and record the exact values used in `src/styles/design-tokens.css` as CSS custom properties. Cover at minimum:

- Brand primary, secondary, accent, background, foreground, muted, border, and error colors.
- Typography scale: font family, font weights, heading sizes, body sizes, line heights.
- Spacing scale: page gutters, section padding, card padding, component gaps.
- Radius scale: button radius, input radius, card radius.
- Shadow scale: card shadows, focus rings, hover shadows.
- Breakpoints used for responsive layout.

2.2. Map the design tokens into Tailwind `theme.extend` in `tailwind.config.js` so components can use semantic class names (for example `text-brand-primary`, `bg-surface`, `rounded-card`, `shadow-card`).

2.3. Update `src/index.css` to import the design tokens, apply the brand font, and set the base background/foreground colors. Do not copy Next.js global styles or CSS-in-JS runtime code.

2.4. Use the same logo asset treatment as the consumer website. Copy only logo/brand assets that are already approved for reuse; do not copy private images, marketing photography, or customer data.

### 3. Shared layout components

3.1. Create `src/components/layout/Header.tsx` that mirrors the consumer website header composition: logo placement, navigation container (empty or with a single "Track Application" active state), and mobile menu trigger. No Next.js `Link` or `Image` components; use plain `a` tags and standard `img` or SVG.

3.2. Create `src/components/layout/Footer.tsx` that mirrors the consumer website footer composition: copyright line, generic support link, and brand mark. Do not include internal addresses, employee names, or operational phone numbers.

3.3. Create `src/components/layout/PageShell.tsx` that composes `Header`, main content area with consistent vertical padding and max-width container, and `Footer`. It must set the correct min-height and footer-at-bottom behavior on all viewports.

3.4. All layout components must be responsive: the shell must not overflow horizontally on 320 px viewports and must use the same breakpoints as the reference site.

### 4. Presentational components

4.1. Ensure the following shadcn/ui base components are installed and themed:

- `Button`
- `Input`
- `Label`
- `Card`, `CardHeader`, `CardTitle`, `CardDescription`, `CardContent`, `CardFooter`
- `Alert`, `AlertTitle`, `AlertDescription`
- `Skeleton`

4.2. Override or extend the shadcn/ui component styles in each component file so they match the consumer website button, input, card, alert, loading, and error treatment. Do not edit `node_modules`; changes must live in `src/components/ui/`.

4.3. Create a small `src/components/common/LoadingState.tsx` that renders a branded skeleton/card placeholder for the status view.

4.4. Create `src/components/common/ErrorState.tsx` that renders a generic, non-revealing error alert suitable for public failures. It must accept a `supportHref` prop and never display raw API errors or PII.

### 5. Accessibility

5.1. Every form input must have an associated `<label>` with a correct `htmlFor` attribute.

5.2. Buttons must have explicit `type` attributes and visible focus indicators matching the design system.

5.3. Color contrast must meet WCAG 2.1 AA for normal text and interactive elements. Do not rely on color alone to communicate status.

5.4. Add `aria-live="polite"` regions for loading and error states.

5.5. The page shell must render a single `<main>` element and proper heading hierarchy (`h1` once per route view, `h2` for card titles).

### 6. Routing and page shells

6.1. Configure React Router in `src/App.tsx` with two route placeholders:

- `/` — verification form page shell.
- `/status` — status/timeline page shell.

6.2. Create `src/pages/VerificationPage.tsx` and `src/pages/StatusPage.tsx` that render the shared `PageShell` and route-appropriate placeholder content. Each page must have a semantic `h1`.

6.3. Navigation between `/` and `/status` must use React Router `useNavigate`/`Link`; do not use full-page reloads.

### 7. Typed API seams and mocks

7.1. Create `src/types/tracking.ts` containing TypeScript interfaces for the public API contract defined in `01-architecture-and-data-model.md` and `02-backend-workflows-and-api-contracts.md`:

- `VerifyRequest`: passport number, date of birth.
- `VerifyResponse`: opaque session token only.
- `StatusResponse`: masked applicant name, masked passport number, destination, visa type, current public status, public message, last-updated timestamp, public status timeline, generic support link.
- `StatusTimelineItem`: status name, public message, effective timestamp, optional display icon.

7.2. Create `src/api/client.ts` that exports an Axios instance with:

- Base URL read from `import.meta.env.VITE_API_BASE_URL`.
- Request/response interceptors that log nothing containing PII.
- Typed functions `verifyIdentity(request: VerifyRequest): Promise<VerifyResponse>` and `fetchStatus(sessionToken: string): Promise<StatusResponse>`.

7.3. Implement the functions in `src/api/client.ts` as mocks that return typed sample data with a short artificial delay. They must not call a real backend. The mock responses must use obviously fake values (for example, masked passport number `A1****23`, applicant name `J****e`).

7.4. Create `src/mocks/tracking.ts` with exported mock objects for `VerifyResponse`, `StatusResponse`, and a `StatusTimelineItem` array. These mocks are the single source of sample data for development and early UI tests.

7.5. Do not implement real verification logic, session storage, polling, error-code parsing, or abuse handling. Those belong to TASK-009.

### 8. Environment and configuration

8.1. Add a non-secret `.env.example` file documenting `VITE_API_BASE_URL`. Do not commit real values, backend secrets, or HMAC keys.

8.2. Ensure `VITE_` prefixed variables are the only runtime configuration surface used by the app.

### 9. Static verification and quality gates

9.1. `npm install` (or equivalent) must complete without errors and without modifying the lockfile in an unexpected way.

9.2. `npm run lint` must pass with no errors.

9.3. `npm run build` must pass and emit a production bundle.

9.4. TypeScript `tsc --noEmit` must pass.

9.5. A manual visual comparison against `visaguy-website-client` must confirm header/footer composition, color, typography, spacing, radius, shadows, and responsive behavior are materially consistent.

### 10. Explicit exclusions

10.1. Do not implement the verification form logic, form validation, or submission handling beyond the typed seams and mocks.

10.2. Do not implement status/timeline data fetching from a real API.

10.3. Do not store passport number, DOB, or session token in `localStorage`, `sessionStorage`, cookies, analytics, or URLs.

10.4. Do not copy Next.js-specific routing, image optimization, server components, environment handling, authentication, or data-fetching code from `visaguy-website-client`.

10.5. Do not modify `visaguy-website-client`.

10.6. Do not push to any Git remote.

10.7. Do not run end-to-end tests, runtime API tests, or tests against the live backend in this task. Runtime integration checks are deferred to TASK-010 or a dedicated test site.

## Constraints

- Work only in `/home/shzd/Projects/tridz/visa_tracker` and read-only inspection of `/home/shzd/Projects/tridz/visaguy-website-client`.
- Preserve the existing Vite, React, TypeScript, Tailwind CSS, and shadcn/ui scaffold.
- Depend on TASK-001 completion evidence: the scaffold directory and Git repository must exist.
- Do not introduce new runtime dependencies unless they are already used by the existing scaffold or required for shadcn/ui base components.
- Do not add API flow implementation beyond typed seams and mocks.
- Do not commit secrets, backend URLs, production data, or PII.
- Do not push, deploy, or run migration/tests on `visaguy`.

## Expected changes

### New or updated files in `visa_tracker`

- `src/main.tsx` — mount the app with React Router.
- `src/App.tsx` — route configuration.
- `src/index.css` — global styles and token imports.
- `src/styles/design-tokens.css` — CSS custom properties.
- `src/index.css` — Tailwind CSS v4 CSS-first `@theme` integration.
- `src/lib/utils.ts` — existing shadcn utility; keep unless changes are required.
- `src/components/layout/Header.tsx`
- `src/components/layout/Footer.tsx`
- `src/components/layout/PageShell.tsx`
- `src/components/ui/button.tsx` — themed shadcn Button.
- `src/components/ui/input.tsx` — themed shadcn Input.
- `src/components/ui/label.tsx` — themed shadcn Label.
- `src/components/ui/card.tsx` — themed shadcn Card family.
- `src/components/ui/alert.tsx` — themed shadcn Alert family.
- `src/components/ui/skeleton.tsx` — themed shadcn Skeleton.
- `src/components/common/LoadingState.tsx`
- `src/components/common/ErrorState.tsx`
- `src/pages/VerificationPage.tsx`
- `src/pages/StatusPage.tsx`
- `src/types/tracking.ts`
- `src/api/client.ts`
- `src/mocks/tracking.ts`
- `.env.example`
- `index.html` — update title and favicon if brand assets are available.

### Read-only reference

- `/home/shzd/Projects/tridz/visaguy-website-client` — inspect only; no modifications.

## Validation

- [ ] `visa_tracker` repository exists at `/home/shzd/Projects/tridz/visa_tracker` and has an initial Git commit from TASK-001.
- [ ] `npm install` completes without errors.
- [ ] `npm run lint` passes with no errors.
- [ ] `npm run build` passes and emits a production bundle.
- [ ] `npx tsc --noEmit` passes.
- [x] Design tokens are recorded in `src/styles/design-tokens.css` and integrated through Tailwind CSS v4 CSS-first `@theme` declarations in `src/index.css`.
- [ ] Header, footer, and page shell are present and responsive.
- [ ] shadcn/ui base components (`Button`, `Input`, `Label`, `Card`, `Alert`, `Skeleton`) are installed and themed.
- [ ] `src/types/tracking.ts` defines `VerifyRequest`, `VerifyResponse`, `StatusResponse`, and `StatusTimelineItem`.
- [ ] `src/api/client.ts` exports typed `verifyIdentity` and `fetchStatus` functions implemented as mocks with fake data.
- [ ] `src/mocks/tracking.ts` exports sample responses used by the client mocks.
- [ ] No Next.js-specific code is copied into the Vite app.
- [ ] No passport number, DOB, or session token is stored in `localStorage`, `sessionStorage`, cookies, analytics, or URLs.
- [ ] Manual visual comparison against `visaguy-website-client` confirms design parity on desktop and mobile.
- [ ] All changes are committed locally in `visa_tracker`; no push is performed.

## Definition of done

- The `visa_tracker` repository builds successfully and presents a branded, responsive page shell with consumer-website design parity.
- Shared layout and presentational components are available for TASK-009.
- Typed API seams and mocks are in place so TASK-009 can replace mocks with real calls without changing component prop shapes.
- Static validation (lint, TypeScript, build) passes.
- Design parity is confirmed by manual comparison against `visaguy-website-client`.
- All TASK-008 changes are committed locally; no push, deploy, or backend runtime test is performed.
- TASK-008 is ready for TASK-009 to implement the verification form and status flow.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Scaffold missing or incompatible**: the Vite scaffold created by TASK-001 is missing or uses a stack incompatible with the required React/Vite/TypeScript/Tailwind/shadcn setup.
2. **Design reference unavailable**: `visaguy-website-client` cannot be inspected or its visual system contradicts the approved design language described in FEAT-001 documents.
3. **Dependency conflict**: adding required shadcn/ui components or design-token support forces a dependency that breaks the existing scaffold build.
4. **Missing architecture decision**: an implementation question arises that is not answered by FEAT-001, ADR-003, ADR-005, or `03-frontend-design-and-layout.md`.
5. **Permission denial**: any required repository or file operation is denied by host policy or user approval.
6. **Build regression**: `npm run build` or `npx tsc --noEmit` fails in a way that cannot be fixed within the scope of design parity and typed seams.

## Completion notes

- This task covers design parity and scaffold hardening only.
- Runtime API integration and session handling are intentionally excluded and belong to TASK-009.
- End-to-end verification, backend runtime checks, and rollout evidence are deferred to TASK-010 or a dedicated test site.

## Completion evidence

- Implemented and committed locally at `a21bbd5083a4c2c9bf9b462697d0965e543423f0`.
- `npm run lint`, `npx tsc --noEmit`, and `npm run build` passed; no test harness existed in this task's starting scaffold.
- The reference repository remained read-only and clean. No sensitive browser persistence or legacy Tailwind configuration was added.
- Evidence: `ongoing/visa-tracking-implementation/07c-task-008-implementation.md`.
