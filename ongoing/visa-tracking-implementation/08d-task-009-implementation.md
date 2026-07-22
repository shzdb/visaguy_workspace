# TASK-009 Implementation Report — Frontend Tracking Flow

> Date: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-009 — Frontend tracking flow
> Repository: `visa_tracker` (local, no remote)
> Worktree: `/home/shzd/Projects/tridz/visa_tracker` (branch `main`)

## Verdicts

- **visa_tracker start SHA:** `a21bbd5083a4c2c9bf9b462697d0965e543423f0` (TASK-008 HEAD, clean tree — entry gate satisfied)
- **visa_tracker final SHA:** `717c62d402287849b30a1fd25d3760edfb727747` (`feat: add public visa tracking flow`)
- **Lint/type/test/build verdict:** pass — `npm run lint` 0 errors (1 pre-existing-pattern warning), `npx tsc --noEmit` pass, `npm test` 16/16 pass (3 files), `npm run build` pass.
- **Privacy verdict:** pass — passport/DOB/token live in React memory only; no storage, cookie, URL, log, or analytics writes in app source (static grep + direct test assertions + bundle scan).
- **TASK-009 verdict:** static-complete; runtime/E2E verification deferred to TASK-010.

## Entry gate evidence

- `git rev-parse HEAD` = `a21bbd5…`, branch `main`, `git status --short` empty before any edit. No unexpected work found; nothing preserved/reset.
- Single authorized commit only; no push, no remote operations, no Git identity changes (commit used the environment-default `VisaGuy Agent <agent@tridz.in>` identity, unmodified).
- `visaguy-website-client` not modified and not consulted for runtime architecture; backend apps untouched.

## API contract mapping (TASK-007 final contract, not the stale TASK-009 §2.1 sketch)

The prompt required TASK-007's final endpoint names and schemas. The TASK-007 report's wire contract differs from the draft types in TASK-009 §2.1; **the TASK-007 contract was implemented** and the differences are recorded as deviations below.

| Frontend (`src/api/client.ts`) | TASK-007 method | Wire behavior |
|---|---|---|
| `verifyIdentity(request)` → `POST` `{passport_number, date_of_birth}` (client trims + uppercases passport, trims DOB) | `/api/method/the_visaguy.visa_tracking.api.verification.verify_identity` | HTTP 200 envelope `{success, message, data:{session_token}}`; every failure = identical generic body; lockout adds `Retry-After` header |
| `fetchStatus(token)` → `POST` `{session_token}` | `/api/method/the_visaguy.visa_tracking.api.status.get_tracking_status` | HTTP 200 envelope; `data` = strict allowlist: `applicant_name_masked`, `passport_number_masked`, `destination`, `visa_type`, `current_status`, `public_message`, `last_updated`, `timeline[{status, message, effective_on, icon}]`, `support_link` (empty string/array, never null) |
| `logoutSession(token)` → `POST` `{session_token}` (best-effort, errors swallowed silently) | `/api/method/the_visaguy.visa_tracking.api.status.logout` | Constant non-enumerating success body |

Envelope unwrapping (`unwrapEnvelope`): `success === false` → generic `ApiError`; `Retry-After` header → `ApiError` code `LOCKOUT` with `retryAfterSeconds`. Defensive HTTP mappings for non-contract statuses (misconfigured proxy etc.): 429 → `LOCKOUT`; 401/403/410 → `EXPIRED_SESSION`; network failure → `NETWORK`; everything else → `GENERIC` with the fixed message "Something went wrong. Please try again."

`ApiError` (`src/api/errors.ts`) carries only `message`, `code`, `httpStatus`, `retryAfterSeconds` — never request/response bodies, passport, DOB, or tokens.

## Privacy controls

- Session token lives only in `useState` inside `SessionProvider` (`src/context/SessionContext.tsx`); refresh naturally drops it. `StatusPage` renders `ExpiredSessionState` when the token is absent.
- Token is set only in the verification success handler; cleared on "Check another application" (plus best-effort server `logout`), on expired-session detection, and via `ExpiredSessionState`.
- Navigation uses React Router `useNavigate`; no token in URL, query, hash, or history state.
- Interceptors log only method + constant endpoint path + status, and only in `import.meta.env.DEV`. No bodies, params, or headers logged anywhere.
- Status view renders only server-masked values; destination/visa type render only when non-empty; timeline order preserved from the API; icons paired with text (no colour-only semantics).
- Static grep (app source): no `localStorage.setItem`/`sessionStorage.setItem`/`document.cookie =`/`URLSearchParams`/history-state/IndexedDB/Cache API usage — hits exist only in test assertions/cleanup and comments. No `/api/resource/*` or internal DocType references.
- Direct test assertions: form success test asserts `localStorage`/`sessionStorage` empty, `document.cookie === ""`, and URL free of token/passport/DOB; session context test spies `Storage.prototype.setItem` (never called); client logging test captures all `console.*` output and asserts no passport/DOB/token/body content.
- `.env.example` unchanged from TASK-008: only `VITE_API_BASE_URL` with the reserved placeholder `https://visaguy.example.com`; no real URL/secrets. MSW mocks are test-only (`src/mocks/server.ts` imported only from `src/test/setup.ts`); the production bundle contains no mock data.

## Accessibility and responsive behavior

- `react-hook-form` + `zodResolver`; RHF default `shouldFocusError` moves focus to the first invalid field (asserted in tests). Errors use `role="alert"` next to the field and are linked via `aria-describedby`; inputs set `aria-invalid`.
- Date input is `type="date"` with an associated `Label`. Focus moves to the `/status` `h1` (`tabIndex={-1}`) after a successful load.
- `aria-live="polite"` on loading, error, lockout, and expired-session regions.
- TASK-008 design tokens, layout, and themed components preserved; form full-width on mobile within `max-w-md`, status page `max-w-2xl`; 44px+ touch targets (`h-11` inputs, `lg` buttons). No `tailwind.config.js` added (CSS-first v4 `@theme` kept).

## Changed files (commit `717c62d`)

New:

- `src/api/errors.ts` — safe `ApiError` + codes + generic message.
- `src/api/client.test.ts`, `src/components/tracking/IdentityVerificationForm.test.tsx`, `src/context/SessionContext.test.tsx`
- `src/context/SessionContext.tsx` — in-memory session provider.
- `src/hooks/useIdentityVerification.ts`, `src/hooks/useTrackingStatus.ts`
- `src/lib/validation/identitySchema.ts` — Zod schema (trim/uppercase normalization, `[A-Z0-9]{6,9}`, real-calendar ISO date, not future, ≥ 1900-01-01).
- `src/components/tracking/{IdentityVerificationForm,StatusSummary,StatusTimeline,LockoutState,ExpiredSessionState}.tsx`
- `src/mocks/handlers.ts` (MSW: success, constant-failure, lockout-with-`Retry-After`, defensive 401/500), `src/mocks/server.ts` (test-only), `src/test/setup.ts`
- `vitest.config.ts`

Modified:

- `src/api/client.ts` — real whitelisted-method client replacing TASK-008 mock functions; safe-metadata interceptors.
- `src/types/tracking.ts` — exact TASK-007 wire contract (incl. `ApiEnvelope`).
- `src/mocks/tracking.ts` — fake masked sample data updated to the TASK-007 shape (`A1****23`, `J****e`, fake token constant).
- `src/pages/VerificationPage.tsx`, `src/pages/StatusPage.tsx` — real flow wiring.
- `src/App.tsx` — `SessionProvider` around routes.
- `src/components/common/ErrorState.tsx` — optional `onRetry` retry button; text wrapped in a flex column (backward compatible).
- `package.json` / `package-lock.json` — dev-only test harness: `vitest@4.1.10`, `@testing-library/react@16.3.2`, `@testing-library/jest-dom@7.0.0`, `@testing-library/user-event@14.6.1`, `@testing-library/dom`, `jsdom@29.1.1`, `msw@2.15.0`; added `"test": "vitest run"`. No new runtime dependencies.
- `tsconfig.node.json` — include `vitest.config.ts`.

## Command results

| Gate | Result |
|------|--------|
| `npm install` (dev deps) | pass, 0 vulnerabilities |
| `npm run lint` (oxlint) | **0 errors**, 1 warning: `react(only-export-components)` on the standard context-file pattern in `SessionContext.tsx` (fast-refresh hint, non-blocking) |
| `npx tsc --noEmit` | pass |
| `npm test` | **16/16 pass** (3 files): client success/normalization/generic/lockout/expired/500/no-PII-logging; form empty-submit errors + focus, invalid passport, future DOB, normalized submit + memory-only token + navigation, lockout render; context initial/set/clear/no-storage-writes |
| `npm run build` | pass — `dist/assets/index-*.js` 424.96 kB (136.31 kB gzip), CSS 28.07 kB |
| `git status --short` after commit | clean |

## Build scan

- No masked fixtures (`A1****23`, `J****e`) and no fake token in the production bundle — mocks are fully excluded.
- Only the three whitelisted `/api/method/the_visaguy.visa_tracking.api.*` paths appear; no `/api/resource`.
- No `localStorage` in the bundle. `sessionStorage` occurrences are React Router scroll-restoration internals (scroll offsets keyed by router history keys — no user data). `document.cookie` occurrences are Axios's built-in XSRF helper, dead code unless `xsrfCookieName`/`withXSRFToken` is configured (it is not); we never write cookies.
- No sourcemap secrets; no backend URLs or keys anywhere (only the `.env.example` placeholder).

## Functional validation status

All reachable via unit/component tests with MSW: valid verify → token + `/status` navigation; masked summary + timeline render; 429-equivalent (HTTP 200 + `Retry-After`) → `LockoutState` with retry guidance; defensive 401 → `ExpiredSessionState` + session cleared; 500 → generic `ErrorState` with retry; refresh of `/status` without token → `ExpiredSessionState`. Manual browser smoke and any runtime check against a real backend are deferred (no live site may be touched per stop condition 7 / §10.7).

## Deviations

- **Report filename**: written to `ongoing/visa-tracking-implementation/08d-task-009-implementation.md` per the dispatch prompt; the task file's `expected_files` lists `05g-task-009-implementation.md`. Lifecycle files not moved (coordinator's responsibility).
- **Contract aligned to TASK-007, not TASK-009 §2.1**: field names `applicant_name_masked`/`passport_number_masked` (not `applicant_name`/`passport_number`); timeline items `{status, message, effective_on, icon}` (no `public_message`/`display_icon`/`display_colour`); optionals are empty strings, never null. §5.3's `display_colour` semantic mapping is therefore inapplicable — icons are paired with status text instead.
- **No 401/410/429 semantics on the wire**: TASK-007 returns the constant HTTP 200 generic body for every failure; lockout is signaled only by the `Retry-After` header. The client implements those as the primary detection path and keeps 401/403/410/429 mappings as defensive fallbacks. Consequently an expired session mid-flow cannot be distinguished from a generic failure by the current backend contract (status fetch failure → generic `ErrorState` with retry); `ExpiredSessionState` remains reachable via refresh/no-token and the defensive mappings. Flagging for TASK-010 runtime verification.
- **MSW failure handlers**: §8.3 asked for 429/401 mock statuses; handlers are faithful to TASK-007 (HTTP 200 generic + `Retry-After`), with additional defensive 401/500 handlers to exercise the client's fallback mappings.
- **oxlint disable comments**: client interceptors carry `// eslint-disable-next-line no-console` comments; oxlint's default ruleset does not flag `console`, so these are inert documentation-only safeguards.
- **Test-only additions** beyond `expected_files`: `src/mocks/server.ts`, `src/test/setup.ts`, `vitest.config.ts` (§8.1 requires the harness; these are its minimal wiring).

## Evidence labels

- **source-wired** — client→endpoint mapping, envelope unwrap, error mapping, session lifecycle, form validation, state routing (all test-covered).
- **present** — `.env.example` surface, dev-only interceptor logging, TASK-008 components reused.
- **configured-unverified** — `VITE_API_BASE_URL` value against a real backend; CORS origin pairing with `Visa Tracker Settings.frontend_base_url`.
- **runtime-verified** — lint/type/test/build gates, bundle content scan, static privacy greps. No live HTTP traffic to any Frappe site (deferred to TASK-010).
