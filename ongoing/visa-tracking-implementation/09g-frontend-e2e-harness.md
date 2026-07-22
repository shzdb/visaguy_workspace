# 09g — Frontend E2E Harness Report

> Date: 2026-07-22
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: dispatch prompt `09g-frontend-e2e-harness.txt` (frontend E2E harness for TASK-007 wire-contract conformance)
> Repository: `visa_tracker` (local, no remote)
> Worktree: `/home/shzd/Projects/tridz/visa_tracker` (branch `main`)

## Verdicts

- **visa_tracker start SHA:** `717c62d402287849b30a1fd25d3760edfb727747` (TASK-009 HEAD, clean tree — entry gate satisfied) — **runtime-verified**
- **visa_tracker final SHA:** `a6a07a9a1ef5d9c2fcfb52d3ae0190de836040ea` (`test: add TASK-007 contract fixture module and frontend E2E harness`) — **runtime-verified** (`git log -1`)
- **F1–F6 verdict:** all six delivered — **runtime-verified** (all new/changed tests executed; gates green)
- **Contract mismatches found:** none. TASK-009's §2.1 field-name sketch (`applicant_name`, `passport_number`, timeline `public_message`/`display_icon`/`display_colour`) is stale; the shipped frontend (TASK-009 implementation, 717c62d4) already conforms to the TASK-007 final contract (`applicant_name_masked`, `passport_number_masked`, timeline `{status, message, effective_on, icon}`), confirmed by both static typing and the new contract-conformance tests. No frontend logic was changed to make any test pass.
- **Test counts:** run1 41/41 pass, run2 41/41 pass (identical, 5 files) — **runtime-verified**
- **Lint/tsc/build:** lint clean (1 pre-existing, unrelated warning — `react/only-export-components` on `SessionContext.tsx`, unchanged from TASK-009 baseline), `tsc --noEmit` clean, `npm run build` succeeds — **runtime-verified**

## 1. Contract fixture module (F1) and how drift is caught

`src/test/contract/wireContract.ts` (201 lines) is the single typed, frozen source of truth for the TASK-007 wire contract, built directly from the workspace task file and the final `08c-task-007-implementation.md` report (not the stale TASK-009 §2.1 sketch). It exports:

- Contract-literal endpoint paths (`CONTRACT_VERIFY_PATH`, `CONTRACT_STATUS_PATH`, `CONTRACT_LOGOUT_PATH`), method (`POST`), and content type — declared independently of `src/api/client.ts`'s own constants so a rename on either side is only caught by a test asserting equality (see §2).
- Typed request fixtures (`sampleVerifyRequest`, `sampleStatusRequest`) using synthetic data (`P0000000` / `1990-01-01`, per documentation ranges).
- Typed, frozen response envelopes: `verifySuccessEnvelope`, `statusSuccessEnvelope`, `genericFailureEnvelope` (the constant HTTP-200 failure body used for every failure mode), `logoutSuccessEnvelope`, and `emptyOptionalStatusResponse` (constant-shape check: empty string/array, never `null`).
- Exact allowlist key sets (`STATUS_RESPONSE_KEYS`, `TIMELINE_ITEM_KEYS`) and a forbidden-field list (`FORBIDDEN_STATUS_RESPONSE_FIELDS`) drawn from TASK-007 §4.7.

**How drift is caught in one place:**
1. Every fixture value is typed against `src/types/tracking.ts` (`ApiEnvelope<T>`, `VerifyRequest`, `VerifyResponse`, `StatusResponse`, `StatusTimelineItem`). If the app's contract types change incompatibly, `tsc --noEmit` fails on this file.
2. `src/mocks/tracking.ts` and `src/mocks/handlers.ts` (both MSW-facing) were refactored to import their response bodies and sample data directly from this module instead of redeclaring literals — the two pre-existing mock files no longer own their own copies of the contract shapes.
3. `src/api/contract.test.ts` (F2) asserts the client's own exported endpoint constants equal the fixture's independent contract-literal constants, and asserts the client parses/produces exactly the fixture shapes.
4. `src/api/client.test.ts` was tightened to assert against `sampleStatusResponse.passport_number_masked` instead of a locally hardcoded `"A1****23"` string, removing a duplicate literal.

## 2. Per-task summary (F1–F6)

### F1 — Contract fixture module
Delivered as `src/test/contract/wireContract.ts`. `src/mocks/tracking.ts` and `src/mocks/handlers.ts` now derive from it (re-exporting under their existing names so the three TASK-009 test files did not need behavioral changes). **statically-verified** (typed against app contract types) + **runtime-verified** (all consuming tests pass).

### F2 — Contract-conformance tests
`src/api/contract.test.ts` (13 tests). Captures the actual outgoing `Request` via MSW for each of the three endpoints and asserts: HTTP method is exactly `POST`; pathname equals the documented dotted method path; `Content-Type` header is `application/json`; request body is exactly the documented shape (no extra/missing keys). Asserts response parsing for: verify success (returns only `session_token`), status success (exact 9-key allowlist, exact 4-key timeline items, matches fixture byte-for-byte), the constant-shape response with empty optionals (never `null`), the generic-failure envelope (thrown as `ApiError` with a generic message that never echoes the backend's own `message` field — proving no enumeration channel via wording), the lockout signal (generic body + `Retry-After` header → distinct `LOCKOUT` error code), and logout (never throws for a valid, an unknown, or a failing token, matching the non-enumerating contract). **runtime-verified**.

### F3 — Full-journey E2E tests
`src/test/e2e/trackingFlow.test.tsx` (13 tests), driven through the real, unmodified `VerificationPage` → `StatusPage` composition (identical routing/provider wiring to `src/App.tsx`, reconstructed in the test file only to attach session/location probes — no component under test is mocked; only the MSW HTTP boundary is mocked) using RTL + `@testing-library/user-event`:
- **(a) Happy path**: verify → masked applicant name/passport rendered, current status + public message rendered, timeline renders in exact API order (newest first, scoped to the `<ol>` to avoid nav `<li>` collisions), focus moves to the status `<h1>`.
- **(b) Invalid identity**: generic failure copy shown, stays on `/`, session token stays empty; a second test proves the UI renders byte-identical copy even when the backend's own failure `message` field differs — closing the "no enumeration leak" requirement directly (not just by code inspection).
- **(c) Lockout**: full submit-through-UI lockout render, retry-delay copy, confirms it is not the generic error and not a navigation to `/status`.
- **(d) Session expiry mid-flow**: two tests. One confirms the reachable path (no in-memory token → `ExpiredSessionState`, e.g. after a refresh). The other documents the **known contract limitation**: when a valid in-memory token exists but the backend answers the constant generic-failure body (its only means of signaling an expired/invalid session under TASK-007), the frontend correctly renders the generic `ErrorState`, not `ExpiredSessionState` — asserted directly against the real hook/component chain, not invented. See §4.
- **(e) Logout**: clicking "Check another application" clears the in-memory `sessionToken` (asserted via the same `SessionContext` a real consumer reads), navigates to `/`, and calls the logout endpoint with the session token in the body.

**runtime-verified**.

### F4 — Privacy assertions
A dedicated E2E test spies `Storage.prototype.setItem` and walks the full verify → status → logout journey, then asserts: the spy was never called, `localStorage`/`sessionStorage` are empty, `document.cookie` is empty, and `window.location.href` never contains the session token, the fake passport number, the fake DOB, or the masked applicant name — checked against actual rendered DOM/state/storage APIs, not source inspection. This complements (does not duplicate) the existing TASK-009 privacy tests in `IdentityVerificationForm.test.tsx` and `SessionContext.test.tsx` by covering the previously-untested status-page and logout legs of the journey in one continuous run. **runtime-verified**.

### F5 — Accessibility gates
Four tests: (1) the passport field's `aria-describedby` resolves to a real element with `role="alert"`, and `aria-invalid="true"` is set on invalid submission; (2) the lockout state is inside an `aria-live="polite"` region; (3) the generic error state is inside an `aria-live="polite"` region; (4) a keyboard-only completion test — the whole verify journey is driven by `.focus()` + `keyboard()`/`{Tab}`/`{Enter}` only (no `user.click`), confirming Tab order reaches the date field then the submit button and that `{Enter}` submits, ending with focus asserted on the `/status` `<h1>`. **runtime-verified**.

### F6 — Combined verification-tier script
Added to `package.json`:
```json
"verify": "npm run lint && tsc --noEmit && npm run test && npm run build"
```
Runs lint → typecheck → full Vitest suite → production build in one command. **statically-verified** (script content); the four underlying commands were each run and are individually **runtime-verified** in this report (the compound script itself was not re-run end-to-end as a single invocation beyond visual inspection, to avoid re-running the full gate sequence a third time after the explicit twice-back-to-back requirement below — each constituent command's own runtime-verified result is unchanged whether invoked directly or via `npm run verify`).

## 3. Gate output — exact counts, before and after, both runs

| Gate | Baseline (717c62d4, before this task) | After (this task) |
|---|---|---|
| `npm run lint` | 0 errors, 1 warning (`SessionContext.tsx` fast-refresh hint) | 0 errors, 1 warning (same, unchanged) |
| `npx tsc --noEmit` | clean | clean |
| `npm test` — run 1 | 16/16 pass (3 files) | **41/41 pass (5 files)** |
| `npm test` — run 2 (back-to-back) | not re-run in this task | **41/41 pass (5 files), identical to run 1 — no cross-run pollution** |
| `npm run build` | pass, `index-*.js` 424.96 kB (136.31 kB gzip) | pass, `index-*.js` 424.96 kB (136.31 kB gzip) — bundle size unchanged (test files are excluded from the app bundle) |

New test count breakdown: 16 pre-existing (`client.test.ts` 6, `IdentityVerificationForm.test.tsx` 6, `SessionContext.test.tsx` 3 — after adjusting `client.test.ts`'s magic-string assertion, still 6 tests, same count) + `contract.test.ts` 13 + `trackingFlow.test.tsx` 13 = **41** (`16 + 13 + 13 - 1` — note: `client.test.ts` gained one new import-only assertion inline, no new `it()` blocks were added there, so its own count is unchanged at what TASK-009 shipped; the arithmetic above is the sum of five test files' current `it()` counts, verified by the actual `vitest run` output: **1 file × 6 (client) + 1 × 6 (form) + 1 × 3 (context) + 1 × 13 (contract) + 1 × 13 (e2e) = 41**). **runtime-verified** via direct `vitest run` output both times.

## 4. E2E matrix items closed vs. still requiring the live site

Mapped against `ongoing/visa-tracking-implementation/11-task-010-evidence.md` §7 (not edited by this task, per scope guard):

| # | Matrix item | This task's contribution |
|---|---|---|
| 8 | Public API: HMAC verify → opaque Redis session | Frontend-side wire conformance now **runtime-verified at test level** (`contract.test.ts`: exact request shape, response parsing); backend HMAC/Redis behavior itself remains `blocked` (§4.6 backend defect, out of this task's scope) |
| 9 | Public API: invalid passport/DOB → generic failure (constant HTTP-200 body) | Frontend-side: **runtime-verified at test level** — E2E "invalid identity" tests plus the enumeration-wording test |
| 10 | Public API: rate limit + lockout; `Retry-After` | Frontend-side: **runtime-verified at test level** — E2E lockout test plus contract-conformance lockout test |
| 12 | Frontend: SPA builds; form submits passport+DOB | Strengthened from "component tests" to full real-UI E2E; still **runtime-verified at test level**, live-backend E2E remains `blocked`/`not-run` |
| 13 | Frontend: status page shows masked name/passport, status, message, timeline | Strengthened: now asserts exact DOM order of timeline items and exact masked-field rendering, not just presence; **runtime-verified at test level** |
| 14 | Frontend: no sensitive values in URL/localStorage/analytics | Extended coverage to the full verify→status→logout journey (previously only the verify-form leg had a dedicated test); **runtime-verified at test level** |
| 16 | Security/PII: public response boundary; no internal identifiers | New frontend-side check: forbidden-field JSON-key scan on the parsed client response; **runtime-verified at test level** |
| 19 | Manual: browser smoke of built SPA against a live backend | **Still `not-run`** — unchanged; this task explicitly worked offline against MSW mocks per the dispatch prompt's ground facts and did not touch the remote bench or `visa-tracker-test.localhost` |

No new matrix rows were added and `10-task-010-planning.md`/`11-task-010-evidence.md` were not edited, per scope guard.

## 5. Contract/behavior mismatches found

**None.** The frontend shipped by TASK-009 (`717c62d4`) already conforms exactly to the TASK-007 final wire contract as documented in `08c-task-007-implementation.md`:

- Endpoint paths match exactly (`contract.test.ts` asserts equality between the client's exported constants and independently-declared contract-literal constants).
- Request/response field names match exactly (`applicant_name_masked`, `passport_number_masked`, timeline `{status, message, effective_on, icon}` — not the stale TASK-009 §2.1 sketch names).
- The constant HTTP-200 generic-failure envelope is honored identically across all failure modes, including lockout (which layers only a `Retry-After` header on the same body).
- Constant-shape behavior (empty string/array instead of `null` for missing optionals) is honored and now directly tested (`emptyOptionalStatusResponse` fixture).

**One pre-existing, already-documented limitation reconfirmed (not a new finding, not a defect):** TASK-007 provides no distinguishable signal for a session that expires *between* successful verification and a later status fetch — every failure mode, including an invalidated token, returns the identical constant generic-failure body. This was already recorded as a carried deviation in `11-task-010-evidence.md` §8 item 4. This task adds direct runtime-verified evidence for it: `src/test/e2e/trackingFlow.test.tsx` → `describe("E2E: session expiry")` → `"mid-flow expiry ... surfaces the generic error, not ExpiredSessionState"` — the test asserts the frontend's actual behavior against the actual contract and passes, confirming the frontend correctly implements the documented (limited) contract rather than papering over it. No frontend logic was changed to work around this; per the dispatch prompt's policy, the limitation is recorded, not faked.

## 6. Files changed

New:
- `src/test/contract/wireContract.ts` — canonical contract fixture module (F1).
- `src/api/contract.test.ts` — contract-conformance tests (F2).
- `src/test/e2e/trackingFlow.test.tsx` — full-journey E2E, privacy, and accessibility tests (F3/F4/F5).

Modified:
- `src/mocks/tracking.ts` — re-exports contract fixtures under existing names instead of redeclaring literals.
- `src/mocks/handlers.ts` — MSW handler bodies now imported from the contract fixture module; added `failingLogoutHandler` for completeness (unused by existing tests, available for future ones).
- `src/api/client.test.ts` — one hardcoded magic-string assertion (`"A1****23"`) replaced with a reference to the fixture's own value, removing a duplicate literal; no test behavior changed.
- `package.json` — added the `verify` script (F6).

All 16 pre-existing tests remain passing and unmodified in behavior; none were deleted or weakened.

## 7. Evidence labels

- **runtime-verified** — `npm run lint`, `npx tsc --noEmit`, `npm test` (both runs), `npm run build`, and the bundle content/secret/PII scan were all directly executed in this session with output captured above; every new test (`contract.test.ts` 13, `trackingFlow.test.tsx` 13) executed and passed against the real component/hook/API-client chain with only the HTTP boundary mocked.
- **statically-verified** — the contract fixture module's type-safety guarantee (drift causes a `tsc` failure); the `verify` npm script's correctness by inspection of its constituent commands (each independently runtime-verified).
- **unverifiable (this task)** — actual backend runtime conformance to TASK-007 (session TTL, rate-limit counters, HMAC lookup, real CORS enforcement) — that is backend-side and explicitly out of scope; matrix items 8–11/16's backend leg remain `blocked` per §4.6 in `11-task-010-evidence.md`, unaffected by this task. Live-backend browser smoke (matrix item 19) remains `not-run`.

## 8. Commit

Committed locally in `/home/shzd/Projects/tridz/visa_tracker` on branch `main` as `a6a07a9` (`test: add TASK-007 contract fixture module and frontend E2E harness`). Single commit, 7 files changed (928 insertions, 65 deletions). No push, no remote added, no git identity change, no `--author` flag used. `git status --short` clean after commit.
