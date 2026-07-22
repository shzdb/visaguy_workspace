---
id: TASK-009
feature: FEAT-001
title: Frontend tracking flow
status: completed
repository: visa_tracker
worktree: /home/shzd/Projects/tridz/visa_tracker
owners: []
depends_on:
  - TASK-007
  - TASK-008
  - ADR-005
expected_files:
  - /home/shzd/Projects/tridz/visa_tracker/src/api/client.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/api/errors.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/types/tracking.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/mocks/tracking.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/mocks/handlers.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/context/SessionContext.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/hooks/useIdentityVerification.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/hooks/useTrackingStatus.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/IdentityVerificationForm.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/StatusSummary.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/StatusTimeline.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/LockoutState.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/ExpiredSessionState.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/pages/VerificationPage.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/pages/StatusPage.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/lib/validation/identitySchema.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/App.tsx
  - /home/shzd/Projects/tridz/visa_tracker/.env.example
  - /home/shzd/Projects/tridz/visa_tracker/src/api/client.test.ts
  - /home/shzd/Projects/tridz/visa_tracker/src/components/tracking/IdentityVerificationForm.test.tsx
  - /home/shzd/Projects/tridz/visa_tracker/src/context/SessionContext.test.tsx
  - ongoing/visa-tracking-implementation/05g-task-009-implementation.md
created: 2026-07-21
updated: 2026-07-21
---

# TASK-009: Frontend tracking flow

## Objective

Implement the public visa-tracking verification and status flow in the `visa_tracker` SPA: a typed API client that consumes the TASK-007 public APIs, a passport-and-DOB form powered by React Hook Form and Zod, strictly in-memory opaque session handling, masked status/timeline display, and complete handling for loading, generic error, rate-limit lockout, and expired-session states.

## Context

- FEAT-001 defines a public tracking boundary where passport number and date of birth are weak knowledge factors.
- ADR-005 requires the SPA to keep passport number, DOB, and the opaque session token out of `localStorage`, `sessionStorage`, cookies, analytics, URLs, and logs.
- TASK-001 source evidence shows `visa_tracker` already exists at `/home/shzd/Projects/tridz/visa_tracker` with a Vite + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui scaffold (scaffold commit `20b8c45`, lint/build passing, no Git remote).
- TASK-008 delivers the design system, shared layout, presentational components, typed API seams, and mock data in `src/api/client.ts`, `src/types/tracking.ts`, and `src/mocks/tracking.ts`.
- TASK-007 (public API and security controls) will provide the backend whitelisted methods consumed here. This task must not implement backend logic, but it must align the frontend contract with the API shapes defined in `features/ongoing/visa-tracking/01-architecture-and-data-model.md` and `decisions/ADR-005-public-tracking-security-and-privacy-model.md`.
- The SPA may call only purpose-built whitelisted methods in `the_visaguy`; direct `/api/resource/*` access to `Visa Tracking Application`, `Passport Extraction`, or related DocTypes is forbidden.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `tasks/ready/visa-tracking/TASK-007-public-api-and-security-controls.md`
- `tasks/ready/visa-tracking/TASK-008-frontend-scaffold-and-design-parity.md`
- Local frontend repository: `/home/shzd/Projects/tridz/visa_tracker`
- Read-only design reference: `/home/shzd/Projects/tridz/visaguy-website-client`

## Required behaviour

### 1. Preserve TASK-008 scaffold and design parity

1.1. Keep the existing Vite + React + TypeScript + Tailwind CSS + shadcn/ui scaffold and all TASK-008 design tokens, layout, and presentational components.

1.2. Do not introduce a new routing, styling, component, or state-management library unless it is required for testing and is installed as a dev dependency only.

1.3. Commit all TASK-009 changes locally in `visa_tracker`. No Git remote is required.

### 2. Typed API client and contracts

2.1. Update `src/types/tracking.ts` to define the exact public API contract:

- `VerifyRequest`
  - `passport_number`: string
  - `date_of_birth`: string (ISO date `YYYY-MM-DD`)
- `VerifyResponse`
  - `session_token`: opaque string
- `StatusResponse`
  - `applicant_name`: masked string
  - `passport_number`: masked string
  - `destination`: string | null
  - `visa_type`: string | null
  - `current_status`: string
  - `public_message`: string
  - `last_updated`: ISO datetime string
  - `support_link`: generic URL string
  - `timeline`: `StatusTimelineItem[]`
- `StatusTimelineItem`
  - `status`: string
  - `public_message`: string
  - `effective_on`: ISO datetime string
  - `display_icon`: string | null
  - `display_colour`: string | null

2.2. Update `src/api/client.ts` to export:

- `verifyIdentity(request: VerifyRequest): Promise<VerifyResponse>`
- `fetchStatus(sessionToken: string): Promise<StatusResponse>`

These functions must call the TASK-007 whitelisted Frappe methods over HTTP using the Axios instance created in TASK-008. Base URL must continue to come from `import.meta.env.VITE_API_BASE_URL`.

2.3. Add `src/api/errors.ts` with an `ApiError` class that carries only safe, non-PII fields: a generic `message` string, an optional `code` string, and the HTTP `status`. Do not attach request bodies, response bodies, passport numbers, DOB, or tokens to the error object.

2.4. Request/response interceptors must:

- Set `Content-Type: application/json` for POST requests.
- Never log request bodies, query parameters, response bodies, or headers that could contain PII.
- Log only safe metadata: HTTP method, path, and status code.
- Strip or reject any attempt to echo the passport number, DOB, or session token in logs or console output.

2.5. On network or unexpected errors, the client must throw `ApiError` with a generic message such as "Something went wrong. Please try again." and never surface backend internals or PII.

### 3. Passport + DOB form with React Hook Form and Zod

3.1. Create `src/lib/validation/identitySchema.ts` with a Zod schema:

- `passport_number`
  - Required.
  - Normalized to uppercase and trimmed by the schema.
  - Matches alphanumeric characters only (`/^[A-Z0-9]+$/`).
  - Length between 6 and 9 characters inclusive (typical TD3 passport number range).
- `date_of_birth`
  - Required.
  - Valid ISO date (`YYYY-MM-DD`).
  - Not in the future.
  - On or after `1900-01-01`.

Use clear, accessible error messages (for example: "Enter a valid passport number", "Enter a valid date of birth", "Date of birth cannot be in the future").

3.2. Create `src/components/tracking/IdentityVerificationForm.tsx` using `react-hook-form` with `@hookform/resolvers/zod`.

- Two fields: Passport Number and Date of Birth.
- Each field has an associated `<label>` with `htmlFor` matching the input `id`.
- Inputs use the themed shadcn `Input` and `Label` components from TASK-008.
- Validation errors are displayed next to the relevant field and linked via `aria-describedby`.
- Submit button is disabled while submission is in flight and shows a loading state.
- On successful verification the form calls `verifyIdentity` and hands the resulting session token to the in-memory session layer (see Section 4). It must not store passport, DOB, or token in any persistent browser storage or URL.
- On failure the form surfaces only generic failure copy. If the failure maps to a lockout condition (HTTP 429 or a TASK-007 lockout response), render the `LockoutState` component. For all other failures render the generic `ErrorState` component from TASK-008.

3.3. The form must be responsive: full-width inputs on narrow viewports, constrained max-width on desktop, and usable at 320 px viewport width.

### 4. In-memory opaque session handling

4.1. Create `src/context/SessionContext.tsx` that holds the session token only in React state. The token must never be written to:

- `localStorage`
- `sessionStorage`
- `document.cookie`
- URL query parameters, hash, or path
- Analytics events or metadata
- Console logs, error trackers, or performance monitoring tools

4.2. Expose a minimal provider API:

- `sessionToken: string | null`
- `setSessionToken(token: string | null): void`
- `clearSession(): void`

4.3. `setSessionToken` must be called only from the verification success handler. `clearSession` must be called when the user chooses to start over, when the session is detected as expired, or when the status fetch returns an expired-session response.

4.4. A browser refresh must naturally discard the session. The `StatusPage` must detect the missing token and render `ExpiredSessionState` with a button to return to the verification form.

4.5. Programmatic navigation from the verification form to `/status` must use React Router `useNavigate`; do not pass the token via URL or state that persists in history.

### 5. Status fetch, masked summary, and timeline

5.1. Create `src/hooks/useTrackingStatus.ts` that calls `fetchStatus(sessionToken)` when mounted and whenever the token changes.

- Expose `status`, `loading`, `error`, and `refresh`.
- Polling is not required for the first release; provide a manual refresh button only.
- On 401/403/410 responses or a TASK-007 expired-session indicator, clear the session and surface `ExpiredSessionState`.
- On 429 or lockout indicator, surface `LockoutState`.
- On any other failure, surface the generic `ErrorState`.

5.2. Create `src/components/tracking/StatusSummary.tsx` to render:

- Masked applicant name (as returned by the API; the SPA never receives the full value).
- Masked passport number.
- Destination and visa type, only when the API returns non-null values.
- Current public status.
- Public message.
- Last updated timestamp formatted for the user's locale.
- Generic support link.

5.3. Create `src/components/tracking/StatusTimeline.tsx` to render the `timeline` array:

- Each item shows the status name, public message, effective timestamp, and optional icon.
- Use the `display_colour` value as a semantic token (for example `text-success`, `text-warning`) mapped through the design system from TASK-008. Do not rely on colour alone; pair icons with status text.
- Order must match the order returned by the API (newest first).

5.4. The `StatusPage` must render a semantic `h1`, the `StatusSummary`, the `StatusTimeline`, a manual refresh button, and a "Check another application" button that clears the session and navigates to `/`.

### 6. Loading, generic error, lockout, and expired-session states

6.1. Reuse the `LoadingState` skeleton from TASK-008 while `verifyIdentity` or `fetchStatus` is pending.

6.2. Generic error state must:

- Use the themed `ErrorState` component.
- Display only non-revealing copy such as "We couldn't complete your request. Please try again later."
- Offer a retry action.
- Never display raw API messages, status codes, or response bodies to the user.

6.3. Lockout state (`src/components/tracking/LockoutState.tsx`) must:

- Display a clear lockout message such as "Too many attempts. Please try again later."
- If the response includes a safe retry-after value (for example a `Retry-After` header or a TASK-007 `retry_after_seconds` field), display it; otherwise omit the countdown.
- Not reveal whether the passport/DOB combination was valid.
- Provide a safe fallback action to return to the verification form.

6.4. Expired-session state (`src/components/tracking/ExpiredSessionState.tsx`) must:

- Display "Your session has expired. Please verify your details again."
- Provide a button that clears the session and returns to `/`.
- Explain, if helpful, that the user can re-enter passport and DOB without mentioning where the previous input was stored.

### 7. Accessibility and responsive behaviour

7.1. The verification form and status page must meet the accessibility requirements established in TASK-008, plus:

- Focus must move to the first field error after an invalid submission.
- Focus must move to the status summary heading after successful navigation to `/status`.
- `aria-live="polite"` regions must announce loading, error, lockout, and expired-session changes.
- The date input must use `type="date"` with a clear label and error association.

7.2. Responsive requirements from TASK-008 apply: no horizontal overflow at 320 px, consistent gutters, readable line lengths, and touch-friendly button/input heights.

### 8. Tests and mocks

8.1. Add a minimal test harness if the scaffold does not already include one: `vitest`, `@testing-library/react`, `@testing-library/jest-dom`, `@testing-library/user-event`, `jsdom`, and `msw` (or `axios-mock-adapter`).

8.2. Keep `src/mocks/tracking.ts` as the single source of sample response data. Extend it with realistic fake values (for example masked passport `A1****23`, masked name `J****e`).

8.3. Create `src/mocks/handlers.ts` with MSW handlers (or equivalent) that mock the TASK-007 endpoints:

- Successful verification returns a sample opaque token.
- Successful status fetch returns the sample `StatusResponse`.
- Lockout response returns 429 with a safe `Retry-After` value.
- Expired-session response returns 401.
- Generic failure returns 500.

8.4. Write `src/api/client.test.ts` covering:

- `verifyIdentity` returns a token for valid input.
- `verifyIdentity` throws `ApiError` with a generic message on failure.
- `fetchStatus` returns `StatusResponse` for a valid token.
- `fetchStatus` throws `ApiError` on expired session and lockout.
- No request or response body containing passport/DOB/token is logged.

8.5. Write `src/components/tracking/IdentityVerificationForm.test.tsx` covering:

- Empty submission shows validation errors for both fields.
- Invalid passport format shows a field error.
- Future DOB shows a field error.
- Submitting the form calls `verifyIdentity` with normalized uppercase passport and `YYYY-MM-DD` DOB.
- Successful submission stores the token only in the session context, not in `localStorage`/`sessionStorage`/cookies/URL.
- Lockout response renders the lockout message.

8.6. Write `src/context/SessionContext.test.tsx` covering:

- `sessionToken` is initially null.
- Setting and clearing the token updates consumers.
- The provider does not write to `localStorage`, `sessionStorage`, or cookies.

8.7. Tests must use only obviously fake passport/DOB data and must assert the privacy prohibitions directly.

### 9. Environment and configuration

9.1. Update `.env.example` to document `VITE_API_BASE_URL`. Do not commit real backend URLs, secrets, or HMAC keys.

9.2. Ensure `VITE_` prefixed variables remain the only runtime configuration surface used by the app.

### 10. Explicit prohibitions

10.1. Do not store the passport number, date of birth, or session token in `localStorage`, `sessionStorage`, cookies, analytics events, URL query strings, URL hash, browser history state, or any persistent browser storage.

10.2. Do not log the passport number, date of birth, or session token to the console, to an error tracker, or in any request/response logging.

10.3. Do not call Frappe `/api/resource/*` endpoints for `Visa Tracking Application`, `Passport Extraction`, Lead, Customer, or `PF Process File`.

10.4. Do not copy Next.js-specific routing, image optimization, server components, environment handling, authentication, or data-fetching code from `visaguy-website-client`.

10.5. Do not modify `visaguy-website-client`.

10.6. Do not push to any Git remote.

10.7. Do not run end-to-end tests, runtime API tests, migrations, or tests against the active `visaguy` site in this task. Runtime integration checks are deferred to TASK-010 or a dedicated test site.

## Constraints

- Work only in `/home/shzd/Projects/tridz/visa_tracker` and read-only inspection of `/home/shzd/Projects/tridz/visaguy-website-client`.
- Depend on TASK-001 completion evidence: the `visa_tracker` directory, Vite scaffold, and initial Git commit must exist.
- Depend on TASK-008 completion evidence: design tokens, layout, presentational components, typed API seams, and mocks must exist.
- Depend on TASK-007 for the public API endpoint signatures and behaviour; align contracts to the shapes documented in `01-architecture-and-data-model.md` and ADR-005.
- Preserve the approved frontend stack: React, Vite, TypeScript, React Router, Tailwind CSS, shadcn/ui, Axios, React Hook Form, Zod.
- Do not commit secrets, backend URLs, production data, passport samples, or PII.
- Do not push, deploy, or run migration/tests on `visaguy`.

## Exclusions

- Backend public API implementation, HMAC session store, rate limiting, and lockout logic (TASK-007).
- Scaffold, design tokens, shared layout, and presentational components (TASK-008).
- End-to-end verification, backend runtime checks, security gate, and rollout (TASK-010).
- Direct changes to `the_visaguy`, `fileflo`, `passport_extractor`, `processflo`, or `visaguy-website-client`.

## Expected changes

### New or updated files in `visa_tracker`

- `src/api/client.ts` — typed real API client and interceptors.
- `src/api/errors.ts` — safe `ApiError` class.
- `src/types/tracking.ts` — exact public API contract types.
- `src/mocks/tracking.ts` — sample response data.
- `src/mocks/handlers.ts` — MSW/axios-mock-adapter handlers for tests and local development.
- `src/context/SessionContext.tsx` — in-memory session provider.
- `src/hooks/useIdentityVerification.ts` — verification submission hook.
- `src/hooks/useTrackingStatus.ts` — status fetch hook.
- `src/components/tracking/IdentityVerificationForm.tsx` — form component.
- `src/components/tracking/StatusSummary.tsx` — masked summary card.
- `src/components/tracking/StatusTimeline.tsx` — status timeline component.
- `src/components/tracking/LockoutState.tsx` — lockout UI.
- `src/components/tracking/ExpiredSessionState.tsx` — expired-session UI.
- `src/pages/VerificationPage.tsx` — `/` route page.
- `src/pages/StatusPage.tsx` — `/status` route page.
- `src/lib/validation/identitySchema.ts` — Zod schema.
- `src/App.tsx` — route wiring and session provider integration.
- `.env.example` — non-secret configuration documentation.
- `src/api/client.test.ts`
- `src/components/tracking/IdentityVerificationForm.test.tsx`
- `src/context/SessionContext.test.tsx`
- `package.json` — test dependencies only if not already present.

### Workspace evidence

- `ongoing/visa-tracking-implementation/05g-task-009-implementation.md` — implementation notes, validation evidence, and privacy audit results.

## Validation

### Static validation

- [ ] `npm install` completes without errors.
- [ ] `npm run lint` passes with no errors.
- [ ] `npx tsc --noEmit` passes.
- [ ] `npm run build` emits a production bundle without errors.
- [ ] `npm test` passes all new and existing tests.
- [ ] `git status --short` in `/home/shzd/Projects/tridz/visa_tracker` is clean after all changes are committed locally.

### Privacy and security audit

- [ ] Static grep confirms no `localStorage.setItem`, `sessionStorage.setItem`, `document.cookie =`, or `URLSearchParams` usage for `passport`, `dob`, `date_of_birth`, `session`, or `token`.
- [ ] Static grep confirms no `console.log` of request bodies, response bodies, or the session token.
- [ ] `src/api/client.ts` interceptors log only method, path, and status code.
- [ ] The session token is held only in React state/context; refresh drops it.
- [ ] The form and status page never display full passport numbers, full DOB, internal identifiers, or backend internals.

### Functional validation

- [ ] Manual smoke test with mocked handlers: valid passport + DOB yields an opaque token and navigates to `/status`.
- [ ] `/status` displays the masked summary and timeline from the mocked `StatusResponse`.
- [ ] Simulated 429 response renders `LockoutState`.
- [ ] Simulated 401/403/410 response renders `ExpiredSessionState` and clears the in-memory session.
- [ ] Simulated 500 response renders the generic `ErrorState`.
- [ ] Refreshing `/status` with no in-memory token renders `ExpiredSessionState`.

### Backend boundary validation

- [ ] The client calls only the TASK-007 whitelisted methods, not `/api/resource/*`.
- [ ] No import or reference to Frappe DocTypes (`Visa Tracking Application`, `Passport Extraction`, `Lead`, `Customer`, `PF Process File`) appears in frontend source.

## Definition of done

- The `visa_tracker` SPA implements the verification form, in-memory session handling, status fetch, masked summary, and timeline using the approved stack.
- Typed API client/contracts align with TASK-007 and the FEAT-001 public response boundary.
- All loading, generic error, lockout, and expired-session states are implemented and reachable.
- Accessibility and responsive behaviour meet the requirements and match the consumer website design language from TASK-008.
- Tests and mocks cover form validation, API client behaviour, session handling, and privacy prohibitions.
- Static validation (lint, TypeScript, build, unit tests) passes.
- Privacy audit confirms passport number, DOB, and session token are never stored in `localStorage`, `sessionStorage`, cookies, analytics, URLs, logs, or error trackers.
- All changes are committed locally in `/home/shzd/Projects/tridz/visa_tracker`; no push, deploy, or backend runtime test is performed.
- Implementation evidence is recorded in `ongoing/visa-tracking-implementation/05g-task-009-implementation.md`.
- TASK-009 is ready for TASK-010 to perform end-to-end verification and rollout.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Scaffold or TASK-008 dependency missing**: the Vite scaffold or TASK-008 components/types/mocks are missing or incompatible with the required form/session flow.
2. **API contract mismatch**: TASK-007 endpoint signatures or response shapes contradict the types in `01-architecture-and-data-model.md` and ADR-005.
3. **Privacy constraint conflict**: implementing the required behaviour appears to require storing the session token or user input in persistent browser storage or URLs.
4. **Dependency conflict**: adding the test harness breaks the existing scaffold build or lint.
5. **Missing architecture decision**: an implementation question arises that is not answered by FEAT-001, ADR-005, TASK-007, or TASK-008.
6. **Permission denial**: any required repository or file operation is denied by host policy or user approval.
7. **Backend runtime required**: the task cannot be validated without running migrations or tests on the active `visaguy` site.
