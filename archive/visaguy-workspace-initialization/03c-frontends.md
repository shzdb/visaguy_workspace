# 03c — Frontend Architecture, API Contracts & Operating Procedures

## 1. Scope & Evidence

This report synthesises the accepted frontend reconnaissance (`01a-local-frontends.md`) and Phase-2 triage (`02-triage.md`) into reader-focused architecture material. It is built read-only from the three frontend repositories only:

| Repository | Owner | HEAD | Last commit |
|---|---|---|---|
| `visa_eligibility_checker` | `tvgglobal` | `2d46af4ebb4f5bcd26cc40b535b3233a643ff9fc` | 2026-06-25 |
| `visaguy_business_client` | `tridz-dev` | `6c3d365a48518008b2769fe4361278dbd0744b74` | 2026-03-27 |
| `visaguy-website-client` | `tvgglobal` | `3b066f6baa7291fa3f778e8d7c1d70e236f0db80` | 2025-08-10 |

All three working trees were confirmed clean before writing. No `.env` values, secrets, sample production data, build outputs or dependency trees are reproduced below; only environment variable **names** and public file/line citations are listed.

Legend used in this report:

- **Implemented** — code exists and is on the active path.
- **Configured** — behaviour depends on an environment variable or checked-in config file.
- **Inferred** — the code strongly implies the behaviour but the owning backend app is not visible from the frontend source.
- **Placeholder / simulated** — UI present but not wired to a real backend, or a dead route.

---

## 2. Product Surfaces & Actors

| Surface | Repository | Primary actors | Purpose |
|---|---|---|---|
| **Public eligibility checker** | `visa_eligibility_checker` | Anonymous consumer | Voice/chat visa eligibility assessment, score, AI recommendation, WhatsApp hand-off, CRM lead capture. |
| **B2B business portal** | `visaguy_business_client` | Business admin, standard business user | Login, dashboard, visa order creation/management, applicant documents, payment request, user management. |
| **Consumer website / e-commerce** | `visaguy-website-client` | Consumer applicant | Browse destinations, OTP login, create visa order, multi-applicant application form, payment, dashboard. |

Backend actors consumed by all three surfaces: Frappe/ERPNext site (`visaguy`) plus a small FastAPI/OpenAI companion backend only for the eligibility checker.

---

## 3. Frontend 1 — `visa_eligibility_checker`

### 3.1 Framework, entry points & build

- **Framework:** React 19 + Vite 7 (`package.json:17,37`).
- **Package manager:** Bun (`bun.lock`).
- **TypeScript:** 5.9 with project references (`tsconfig.json` → `tsconfig.app.json` + `tsconfig.node.json`).
- **Styling:** Tailwind CSS v4 via `@tailwindcss/vite` (`package.json:15,20`); theme tokens in `src/index.css:3-22`.
- **Linting:** ESLint 9 flat config (`eslint.config.js:8`).
- **Entry:** `index.html:22` → `src/main.tsx:8` → `src/App.tsx:4` → `<VisaChecker />`.
- **Path alias:** `@/*` → `./src/*` (`tsconfig.app.json:27`, `vite.config.ts:11`).
- **Scripts:** `dev` (vite), `build` (tsc -b && vite build), `lint`, `preview` (`package.json:6-10`).
- **Tests / CI / containerisation:** none evidenced.

### 3.2 Route / page map

No routing library is used. The UI is a single-page state machine driven by `mode` and `step`:

| Screen | Driver | File |
|---|---|---|
| Mode select (Voice / Chat) | `mode === null` | `src/components/visa-checker/mode-select.tsx` |
| Chat intro | `step` index | `src/components/visa-checker/visa-checker.tsx:245-261` |
| Text / tel / choice / country-select steps | `step` index + `CHAT_STEPS` | `visa-checker.tsx:264-371` |
| Voice pre-details modal | Voice mode start | `src/components/visa-checker/user-details-card.tsx` |
| Processing | `step` reaches processing | `src/components/visa-checker/processing-screen.tsx` |
| Result | `step` reaches result | `src/components/visa-checker/result-screen.tsx` |

### 3.3 State & data flow

- **State:** pure local React `useState`/`useRef`; no Redux/Zustand/Context (`visa-checker.tsx:17-23`, `voice-mode.tsx:15-29`).
- **HTTP client:** native `fetch` only.
- **Key state atoms:**
  - `mode`, `step`, `answers` — `visa-checker.tsx:17-19`.
  - `aiRecommendation` — populated by `fetchAIRecommendation` (`processing-screen.tsx:89`).
  - `rawLeadName` — Frappe `Raw Lead` document name used for incremental updates (`visa-checker.tsx:23`).
- **Chat flow:**
  1. User answers name + mobile → `createRawLead` fires (`visa-checker.tsx:56`).
  2. Subsequent answers → debounced `updateRawLead` (`visa-checker.tsx:68-94`).
  3. At processing step: `calcScore` → if `points >= MAX_SCORE_TO_SEND_LEAD` (55) and destination not in `NO_LEAD_COUNTRIES`, `createLead` is fire-and-forget (`processing-screen.tsx:74-85`).
  4. In parallel `fetchAIRecommendation` races a 10 s timeout (`processing-screen.tsx:89-101`).
  5. Result screen shows score ring, factor breakdown, verdict and WhatsApp CTA (`result-screen.tsx:14`).
- **Voice flow:**
  1. `UserDetailsCard` collects name/phone and calls `createRawLead` (`voice-mode.tsx:119-120` via callback).
  2. `VoiceRealtime.connect` fetches ephemeral client secret from FastAPI backend (`services/voice-realtime.ts:41`).
  3. OpenAI Realtime agent interviews user; `complete_assessment` tool returns the 11 required fields (`voice-realtime.ts:64-111`).
  4. `ProcessingScreen`/`ResultScreen` reuse the chat path.

### 3.4 Authentication

**None in the browser.** Frappe calls rely entirely on guest/public API permissions and site-level CORS (`docs/frappe-crm.md:98`, confirmed in code: only `Content-Type: application/json` header is sent).

### 3.5 API contracts

| # | Contract | Method / path | Caller | Implemented behaviour |
|---|---|---|---|---|
| 1 | FastAPI voice secret | `POST /api/voice/client-secret` | `src/services/voice-realtime.ts:41` | Sends `{ zone }`; receives `{ client_secret, instructions, success }`. |
| 2 | FastAI recommendation | `POST /api/recommendations` | `src/services/ai-recommendations.ts:43` | Sends score/percent/verdict/answers/questions; receives `{ recommendation, success, error? }`. |
| 3 | Create Raw Lead | `POST /api/resource/Raw Lead` | `src/components/visa-checker/utils.ts:418` | Creates lead with `full_name`, `mobile_number`, `source`, `zone`. |
| 4 | Update Raw Lead | `PUT /api/resource/Raw Lead/{name}` | `utils.ts:521` | Incremental update with destination/nationality/etc. |
| 5 | Create full Lead | `POST /api/resource/Lead` | `utils.ts:345` | Creates qualified Lead when score threshold met. |

### 3.6 Environment variables

- `VITE_PUBLIC_ZONE` — selects zone config/chat questions at **build time** (`src/config/zone-config.ts:79`).
- `VITE_PUBLIC_API_URL` — FastAPI backend base URL (`src/services/ai-recommendations.ts:40`, `src/services/voice-realtime.ts:24`); falls back to `http://localhost:8000`.
- `VITE_PUBLIC_FRAPPE_BASE_URL` — Frappe site base URL (`utils.ts:338,400,511`).
- `VITE_PUBLIC_WHATSAPP_NUMBER` — WhatsApp CTA number (`result-screen.tsx:34`); fallback to hard-coded `WHATSAPP_MOBILE_NUMBER` in `src/lib/data.ts:2`.
- `OPENAI_API_KEY` — backend only (`server/utils/openai_client.py:17`, `server/routers/voice.py:31`, `server/routers/recommendations.py:49`).

### 3.7 Build, test & deployment evidence

- Local dev: `bun install` → `bun dev` on `http://localhost:5173`; backend `cd server && uvicorn main:app --reload --port 8000` (`docs/getting-started.md:16-47`).
- Build: `bun run build` → `dist/`; `bun run preview` (`docs/getting-started.md:90-91`).
- Backend prod: `uvicorn main:app --host 0.0.0.0 --port 8000`.
- No test framework, no CI/CD, no Dockerfile/compose.

### 3.8 Notable real vs placeholder behaviour

- **Implemented:** dual modes, JSON-driven chat steps, OpenAI Realtime voice interview, frontend scoring, visa restriction handling, WhatsApp deep-link, Raw Lead + Lead capture.
- **Placeholder / dead / configured:** `VOICE_QUESTIONS` in `constants.ts:295` is dead code; transcript heuristics in `voice-mode.tsx:199-216` are not used for scoring; `COUNTRIES_MED` is empty (`constants.ts:93`); zone is build-time configured.

---

## 4. Frontend 2 — `visaguy_business_client`

### 4.1 Framework, entry points & build

- **Framework:** Next.js 15.2.8 App Router + React 19 (`package.json:15,17,50`).
- **Package manager:** both `bun.lock` and `pnpm-lock.yaml` exist; `Dockerfile` uses `pnpm`.
- **TypeScript:** ^5, path alias `@/*` → `./*` (`tsconfig.json`).
- **Styling:** Tailwind CSS v4 (`app/globals.css:1`); shadcn/ui + Radix primitives (`components.json:3-20`).
- **Entry:** `app/layout.tsx:35` wraps `AuthProvider` → `ErrorBoundary` → `ProtectedRoute` → `Layout`.
- **Scripts:** `dev`, `build`, `start`, `lint` (`package.json:6-9`).
- **Build config:** `next.config.mjs:4-8` disables ESLint and TypeScript errors during build and sets `images.unoptimized: true`.

### 4.2 Route / page map

| Route | File | Status |
|---|---|---|
| `/` dashboard | `app/page.tsx` | Implemented |
| `/login` | `app/login/page.tsx` | Implemented |
| `/signup` | `app/signup/page.tsx` | Implemented |
| `/oauth-callback` | `app/oauth-callback/page.tsx` | Placeholder / dead — redirects to `/login` |
| `/orders` | `app/orders/page.tsx` | Implemented |
| `/orders/[id]` | `app/orders/[id]/page.tsx` | Implemented |
| `/order-new` | `app/order-new/page.tsx` | Implemented |
| `/destinations` | `app/destinations/page.tsx` | Implemented |
| `/destinations/[name]` | `app/destinations/[name]/page.tsx` | Implemented |
| `/details` | `app/details/page.tsx` | Implemented; admin-only UI |
| `/users` | `app/users/page.tsx` | Implemented; admin-only UI |
| `/payment` | `app/payment/page.tsx` | Implemented; payment return / polling |

### 4.3 State & data flow

- **State:** local React `useState`/`useEffect` plus `AuthContext`. No Redux/Zustand.
- **Auth state:** `contexts/auth-context.tsx` holds `user`, `isAuthenticated`, `login`, `logout`, `refreshToken`; stores tokens in `localStorage` keys `accessToken`/`refreshToken` (`:37-38`).
- **HTTP client:** `lib/api.ts` creates an Axios instance with:
  - Request interceptor injecting `Bearer` token from `localStorage` (`:23-31`).
  - Response interceptor that refreshes on 401 using a request queue and redirects to `/login` on failure (`:49-111`).
- **API service layer:** `services/api-service.ts` exports `businessService` and `visaService` (~1,100 lines).

### 4.4 Authentication

- **Flow:** OAuth2 password grant (`grant_type=password`) with `client_id`/`client_secret` (`lib/auth.ts:22-50`).
- **Token storage:** `localStorage` (`contexts/auth-context.tsx:37-38`).
- **Session validation:** `getLoggedInUser` tries `openid_profile`, then `frappe.auth.get_logged_user`, then `frappe.auth.get_user_info` (`lib/auth.ts:83-153`).
- **Route guard:** `ProtectedRoute` (`components/protected-route.tsx:13-47`).
- **Admin gating:** client-side only, reading `sessionStorage.getItem("businessDetails")` (`app/users/page.tsx:39-74`, `app/details/page.tsx:100-138`).

### 4.5 API contracts

| # | Contract | Method / path | Caller / evidence |
|---|---|---|---|
| 6 | OAuth token | `POST /api/method/frappe.integrations.oauth2.get_token` | `lib/auth.ts:31,61` |
| 7 | OpenID profile | `GET /api/method/frappe.integrations.oauth2.openid_profile` | `lib/auth.ts:89` |
| 8 | Logged user | `GET /api/method/frappe.auth.get_logged_user` | `lib/auth.ts:110` |
| 9 | User info | `GET /api/method/frappe.auth.get_user_info` | `lib/auth.ts:131` |
| 10 | Business Client CRUD | `POST/GET/PUT /api/resource/Business Client` | `services/api-service.ts:134,515,540` |
| 11 | Business Client User CRUD | `GET/POST/PUT/DELETE /api/resource/Business Client User` | `services/api-service.ts:189-310` |
| 12 | Destinations | `GET /api/resource/Destination` / `/{name}` | `services/api-service.ts:325,366` |
| 13 | Visa types | `POST /api/method/the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_visa_types` | `services/api-service.ts:383` |
| 14 | Visa price | `POST /api/method/the_visaguy.tvg_business.api.get_visa_price.get_visa_price` | `services/api-service.ts:406` |
| 15 | Invoice items | `POST /api/method/the_visaguy.tvg_business.api.get_invoice_items.get_invoice_items` | `services/api-service.ts:458` |
| 16 | Checklist | `GET /api/resource/Business Client Checklist/{name}` | `services/api-service.ts:490` |
| 17 | Business Client Visa Order CRUD | `GET/POST/PUT /api/resource/Business Client Visa Order` | `services/api-service.ts:595-916` |
| 18 | Generate preliminary docs | `POST /api/method/visaguy_business.functions.api.generate_preliminary_documents.generate_preliminary_documents` | `services/api-service.ts:924` |
| 19 | Create process file | `POST /api/method/visaguy_business.functions.api.create_process_file.create_process_file` | `services/api-service.ts:956` |
| 20 | Request payment | `POST /api/method/visaguy_business.functions.api.create_process_file.request_payment_for_visa_order` | `services/api-service.ts:976` |
| 21 | Applicant files | `POST /api/method/visaguy_business.functions.api.get_applicant_files.get_applicant_files` | `services/api-service.ts:1020` |
| 22 | Sales Invoice | `GET /api/resource/Sales Invoice/{invoiceId}` | `services/api-service.ts:1042` |
| 23 | Download invoice PDF | `GET /api/method/frappe.utils.print_format.download_pdf` | `services/api-service.ts:1073` |
| 24 | Workflow action | `POST /api/method/frappe.model.workflow.apply_workflow` | `services/api-service.ts:285` |
| 25 | File upload | `POST /api/method/upload_file` | `services/api-service.ts:569` |

### 4.6 Environment variables

From `env.example`:

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_CLIENT_ID`
- `NEXT_PUBLIC_CLIENT_SECRET`
- `NEXT_PUBLIC_ZONE`
- `NEXT_PUBLIC_CURRENCY`
- `NEXT_PUBLIC_CONTACT_URL`
- `NEXT_PUBLIC_INVOICE_PRINT_FORMAT`
- `NEXT_PUBLIC_INVOICE_LETTERHEAD`

Hard-coded fallback API URL exists at `app/orders/[id]/page.tsx:32`: `https://temp-visaguy.fstg.tridz.in`.

### 4.7 Build, test & deployment evidence

- Local: `pnpm install` (or `bun install`) → `pnpm dev`.
- Build: `pnpm build` → `pnpm start`.
- Docker: `Dockerfile:1-22` (Node 20.19.1, pnpm, build, expose 3000).
- Compose: `compose.yaml:1-39` — service `visaguy-business`, Traefik labels for `visa-business.fstage.tridz.in`, env file `/home/frappe/secrets/.env`.
- Jenkins: `Jenkinsfile:1-40` — copies workspace, `docker compose down | true`, `docker compose up -d --build`.
- GitHub Actions: `.github/workflows/build_and_push.yml:1-36` — builds/pushes Docker image on `dev` pushes using `secrets.DOCKERHUB_USER`/`secrets.DOCKERHUB_TOKEN`.
- No test script.

### 4.8 Notable real vs placeholder behaviour

- **Implemented:** login/signup, dashboard wallet/counts, order CRUD, applicant management, preliminary docs, process file, payment request, invoice download, user management.
- **Placeholder / dead:** `/oauth-callback` immediately redirects; `NationalitySelect.tsx` exported but unused; `category-filter.tsx`, `faq-accordion.tsx`, `loading-button.tsx`, `sidebar.tsx` unused.

---

## 5. Frontend 3 — `visaguy-website-client`

### 5.1 Framework, entry points & build

- **Framework:** Next.js 15.3.5 + React 19 + App Router (`package.json:39,41,45`).
- **Package manager:** Bun (`bun.lock`).
- **Build / dev:** `next dev --turbopack` (`package.json:6`).
- **TypeScript:** ^5 with strict mode (`tsconfig.json:7`).
- **Styling:** Tailwind CSS v4 + custom CSS variables (`app/globals.css:1-196`); shadcn/ui "new-york" style.
- **Entry:** `app/layout.tsx` is an async server layout that fetches `Visaguy Website Configuration` and wraps providers.
- **Scripts:** `dev`, `build`, `start`, `lint` (`package.json:5-9`).
- **ESLint:** many rules explicitly disabled (`eslint.config.mjs:30-47`).

### 5.2 Route / page map

| Route | File | Status |
|---|---|---|
| `/` | `app/page.tsx` | Server async page; destination list |
| `/login` | `app/login/page.tsx` | OTP login client page |
| `/dashboard` | `app/dashboard/page.tsx` | Protected; lists visa applications |
| `/dashboard/[slug]` | `app/dashboard/[slug]/page.tsx` | Protected; application detail |
| `/country` | `app/country/page.tsx` | Destination grid |
| `/country/[slug]` | `app/country/[slug]/page.tsx` | Country detail + lead form |
| `/country/[slug]/[formSlug]` | `app/country/[slug]/[formSlug]/page.tsx` | Application form (`application_form` or `process_form`) |
| `/contact` | `app/contact/page.tsx` | Placeholder only |
| `/payment/success` | `app/payment/success/page.tsx` | Static success page |
| `/careers` | — | Linked in nav (`components/nav.tsx:250-267`) but route does not exist |

### 5.3 State & data flow

- **Global client state:** Redux Toolkit for destination grid filters/pagination (`lib/store/index.ts:4-8`, `lib/store/destinationSlice.ts:10-104`).
- **Contexts:**
  - `AuthContext` — `localStorage`-backed `api_key`/`api_secret` session (`lib/context/auth-context.tsx:22-97`).
  - `ConfigContext` — server-fetched website config (`lib/context/config.tsx:8-20`).
  - `ReduxProvider` wraps the app (`lib/context/ReduxProvider.tsx:6`).
- **API client:** hand-rolled Axios in `lib/services/config.ts:3-29`; request interceptor adds `token {apiKey}:{apiSecret}` header.
- **Server data helpers:** `getDoc`, `getDocList`, `createDoc`, `updateDoc`, `deleteDoc` in `lib/services/doctype.ts:5-80`.
- **RPC helper:** `call.post` / `call.get` prefix methods with `/api/method/` (`lib/services/call.ts:3-19`).

### 5.4 Authentication

- **Flow:** email → OTP sent → OTP verified → backend returns `api_key`/`api_secret` → stored in `localStorage` and used as Frappe token (`app/login/useLogin.ts:22-60`, `lib/context/auth-context.tsx:53-71`).
- **Session check:** `checkAuth` calls `frappe.auth.get_logged_user`; clears invalid tokens (`lib/context/auth-context.tsx:26-51`).
- **Protected routes:** `RequireAuth` wraps `/dashboard` and `/dashboard/[slug]` (`components/auth/RequireAuth.tsx:56-74`).
- **Logout:** removes `api_key`/`api_secret` from `localStorage` (`lib/context/auth-context.tsx:73-77`).

### 5.5 API contracts

| # | Contract | Method / path | Caller / evidence |
|---|---|---|---|
| 26 | Send OTP | `POST /api/method/otp_authentication.otp_generation.user_check_otp_send` | `app/login/useLogin.ts:22` |
| 27 | Verify OTP | `POST /api/method/otp_authentication.otp_verification.otp_verification` | `app/login/useLogin.ts:48` |
| 28 | Logged user | `GET /api/method/frappe.auth.get_logged_user` | `lib/context/auth-context.tsx:37,60` |
| 29 | Website config | `GET /api/resource/Visaguy Website Configuration/{name}` | `app/layout.tsx:15,42` |
| 30 | Destinations | `GET /api/resource/Destination` / `/{name}` | `app/page.tsx:22`, `app/country/[slug]/page.tsx` |
| 31 | Applicant types | `GET /api/resource/Applicant Type` | `components/application/useApplicationForm.ts:198` |
| 32 | Website visa order | `GET /api/resource/Visaguy Website Visa Order/{slug}` | `app/dashboard/[slug]/page.tsx:60` |
| 33 | Create visa order | `POST /api/method/visaguy_website.api.create_visa_order.create_visa_order` | `components/country/form/LeadForm.tsx:76` |
| 34 | Destination items / price | `GET /api/method/visaguy_website.api.get_destination_items.get_destination_items` | `components/country/form/useTotalPrice.ts:21` |
| 35 | File template | `GET /api/method/visaguy_website.api.get_file_template.get_file_template` | `components/application/useApplicationForm.ts:185` |
| 36 | Submit application | `POST /api/method/visaguy_website.api.submit_application.submit_application` | `components/application/useApplicationForm.ts:430` |
| 37 | Applicant deliverables | `GET /api/method/visaguy_website.api.get_applicant_files.get_applicant_files` | `components/application/ProcessDelivarables.tsx:30` |
| 38 | FF File Collection | `GET /api/resource/FF File Collection/{name}` | `components/application/useProcessDetailsForm.ts:98` |
| 39 | Add form data | `POST /api/method/fileflo.data_collection.add_form_data` | `components/application/useProcessDetailsForm.ts:444` |
| 40 | File upload | `POST /api/method/upload_file` | `components/compound/FileUploader.tsx:77` |

### 5.6 Environment variables

From `env.example`:

- `NEXT_PUBLIC_FRAPPE_BASE_URL`

No other public environment variables are evidenced. Hard-coded image hostnames exist in `next.config.ts:7-18`.

### 5.7 Build, test & deployment evidence

- Local: `bun dev` / `npm run dev` on `http://localhost:3000` (`package.json:6`, `README.md:7-15`).
- Build: `next build` → `next start`.
- Lint: `next lint`.
- No repo-level CI/CD, Dockerfile or compose file. README points to Vercel boilerplate (`README.md:32-34`).
- No test script.

### 5.8 Notable real vs placeholder behaviour

- **Implemented:** home/destinations, lead form, application form, file upload, payment redirect, dashboard, process details form submission.
- **Placeholder / simulated:** `/contact` is empty; `/careers` nav link has no route; `ProcessDetailsForm` **Save** button simulates a 1-second delay and does not call an API (`components/application/useProcessDetailsForm.ts:348`).

---

## 6. Frappe / Custom Method Dependency Mapping (FE2)

The table below maps frontend calls to the maintained backend apps where the frontend source gives a strong signal. Calls whose owning app cannot be determined from the frontend alone are flagged **unresolved**.

| Frontend | Method / Resource | Inferred backend app | Evidence / confidence |
|---|---|---|---|
| Eligibility checker | `POST /api/resource/Raw Lead` | **Unresolved** | Frontend only sees Frappe REST resource; owning DocType app not visible. Likely `visaguy_crm` or Frappe CRM, needs confirmation. |
| Eligibility checker | `PUT /api/resource/Raw Lead/{name}` | **Unresolved** | Same as above. |
| Eligibility checker | `POST /api/resource/Lead` | **Unresolved** | Same as above. |
| Business client | `frappe.integrations.oauth2.get_token` | Frappe framework | Module prefix `frappe`. |
| Business client | `frappe.integrations.oauth2.openid_profile` | Frappe framework | Module prefix `frappe`. |
| Business client | `frappe.auth.get_logged_user` / `get_user_info` | Frappe framework | Module prefix `frappe`. |
| Business client | `Business Client`, `Business Client User`, `Business Client Visa Order`, `Business Client Checklist` | `visaguy_business` | Naming strongly implies `visaguy_business`; not a module-path proof. |
| Business client | `the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_visa_types` | `the_visaguy` | Module prefix `the_visaguy.tvg_core`. |
| Business client | `the_visaguy.tvg_business.api.get_visa_price` | `the_visaguy` | Module prefix `the_visaguy.tvg_business`. |
| Business client | `the_visaguy.tvg_business.api.get_invoice_items` | `the_visaguy` | Module prefix `the_visaguy.tvg_business`. |
| Business client | `visaguy_business.functions.api.get_business_details` | `visaguy_business` | Module prefix `visaguy_business`. |
| Business client | `visaguy_business.functions.api.generate_preliminary_documents` | `visaguy_business` | Module prefix `visaguy_business`. |
| Business client | `visaguy_business.functions.api.create_process_file` | `visaguy_business` | Module prefix `visaguy_business`. |
| Business client | `visaguy_business.functions.api.create_process_file.request_payment_for_visa_order` | `visaguy_business` | Module prefix `visaguy_business`. |
| Business client | `visaguy_business.functions.api.get_applicant_files` | `visaguy_business` | Module prefix `visaguy_business`. |
| Business client | `Sales Invoice` | ERPNext (upstream) | Standard ERPNext DocType. |
| Business client | `frappe.model.workflow.apply_workflow` | Frappe framework | Module prefix `frappe`. |
| Business client | `frappe.utils.print_format.download_pdf` | Frappe framework | Module prefix `frappe`. |
| Business client | `upload_file` | Frappe framework | Standard Frappe file upload method. |
| Website client | `otp_authentication.otp_generation.user_check_otp_send` | `otp_authentication` | Module prefix `otp_authentication`. |
| Website client | `otp_authentication.otp_verification.otp_verification` | `otp_authentication` | Module prefix `otp_authentication`. |
| Website client | `frappe.auth.get_logged_user` | Frappe framework | Module prefix `frappe`. |
| Website client | `Visaguy Website Configuration`, `Visaguy Website Visa Order` | `visaguy_website` | Naming strongly implies `visaguy_website`; not module-path proof. |
| Website client | `Destination Mode`, `Destination Region`, `Destination` | `the_visaguy` / shared domain | `Destination` is referenced by both B2B and consumer frontends; exact owning app not visible from frontend. |
| Website client | `Applicant Type` | **Unresolved** | Referenced via generic `getDocList`; owning app not visible. |
| Website client | `visaguy_website.api.create_visa_order` | `visaguy_website` | Module prefix `visaguy_website`. |
| Website client | `visaguy_website.api.get_destination_items` | `visaguy_website` | Module prefix `visaguy_website`. |
| Website client | `visaguy_website.api.get_file_template` | `visaguy_website` | Module prefix `visaguy_website`. |
| Website client | `visaguy_website.api.submit_application` | `visaguy_website` | Module prefix `visaguy_website`. |
| Website client | `visaguy_website.api.get_applicant_files` | `visaguy_website` | Module prefix `visaguy_website`. |
| Website client | `FF File Collection` | `fileflo` / `processflo` | Used together with `fileflo.data_collection.add_form_data`; inferred to `fileflo`. |
| Website client | `fileflo.data_collection.add_form_data` | `fileflo` | Module prefix `fileflo`. |
| Website client | `upload_file` | Frappe framework | Standard Frappe file upload method. |

**Unresolved ownership** (must be confirmed against backend source): `Raw Lead` / `Lead` doctypes; `Applicant Type`; exact owner of `Destination` / `Destination Mode` / `Destination Region`; `FF File Collection` app boundary.

---

## 7. End-to-End Workflows (FE3)

### 7.1 Workflow A — Eligibility assessment & lead capture

**Actors:** anonymous consumer, eligibility checker frontend, FastAPI companion backend, OpenAI Realtime API, Frappe CRM.

1. Consumer opens `/` and selects **Chat** or **Voice** (`mode-select.tsx:14-48`).
2. **Chat path:**
   - User enters name and mobile; frontend validates mobile against zone config (`visa-checker.tsx:96-122`).
   - `createRawLead(name, mobile)` → `POST /api/resource/Raw Lead` (`utils.ts:396-444`).
   - User answers destination, nationality, travel history, residency, employment, bank statements, salary, visa rejection via JSON-driven steps (`visa-checker.tsx:264-371`, `constants.ts:437-468`).
   - After each additional answer, debounced `updateRawLead(rawLeadName, ...)` → `PUT /api/resource/Raw Lead/{name}` (`visa-checker.tsx:68-94`, `utils.ts:507-540`).
   - `ProcessingScreen` checks `getVisaRestriction`; if restricted, shows restriction card (`processing-screen.tsx:43-60`, `result-screen.tsx:45-92`).
   - Otherwise `calcScore` runs in browser (`utils.ts:66-161`).
   - If `points >= 55` and destination not in `NO_LEAD_COUNTRIES`, `createLead` fires fire-and-forget → `POST /api/resource/Lead` (`processing-screen.tsx:74-85`, `utils.ts:296-367`).
   - In parallel `fetchAIRecommendation` → FastAPI `/api/recommendations` with 10 s fallback (`processing-screen.tsx:89-101`).
   - `ResultScreen` displays score ring, factor analysis, verdict and WhatsApp CTA (`result-screen.tsx:14`).
3. **Voice path:**
   - `UserDetailsCard` collects name/phone and creates Raw Lead (`user-details-card.tsx:29`, `voice-mode.tsx:119-120`).
   - `VoiceRealtime.connect` fetches ephemeral client secret from FastAPI `/api/voice/client-secret` (`services/voice-realtime.ts:33-59`).
   - Browser connects to OpenAI Realtime API via WebRTC using the ephemeral secret.
   - Agent collects 11 fields and calls `complete_assessment` tool; tool result maps to `answers` (`voice-realtime.ts:64-111`, `voice-mode.tsx:255-278`).
   - Same processing/result path as chat.

### 7.2 Workflow B — B2B login, order & payment

**Actors:** business user, business portal frontend, Frappe OAuth/API, `visaguy_business`, `the_visaguy`.

1. Unauthenticated user hits any route; `ProtectedRoute` redirects to `/login` (`components/protected-route.tsx:25-26`).
2. Login submits email/password + `client_id`/`client_secret` to `frappe.integrations.oauth2.get_token` (`lib/auth.ts:22-50`).
3. Tokens stored in `localStorage`; `AuthContext` fetches user profile via `openid_profile` → fallback `get_logged_user` → fallback `get_user_info` (`contexts/auth-context.tsx:30-58`, `lib/auth.ts:83-153`).
4. Dashboard loads wallet and order counts via `businessService.getBusinessDetails` and `visaService.get*OrdersCount` (`app/page.tsx:303-375`).
5. User creates order via `/order-new`:
   - Select destination (`businessService.getDestinations`).
   - Select destination configuration/visa type (`getVisaTypes`, `getVisaPrice`, `getInvoiceItems`).
   - Add applicants and `POST /api/resource/Business Client Visa Order` (`app/order-new/page.tsx:151-161`).
6. Order detail (`/orders/[id]`):
   - Fetch order, checklist, price, invoice items, applicant files (`app/orders/[id]/page.tsx:145-226`).
   - Add/delete applicants while status is `Open` or `Applicants Submitted` (`app/orders/[id]/page.tsx:94`).
   - Generate preliminary documents (`generatePreliminaryDocuments`).
   - Select invoice items and `createProcessFile` → status advances.
   - Request payment → backend returns `payment_url`; frontend redirects (`requestPaymentForVisaOrder`, `app/orders/[id]/page.tsx:415`).
7. Return from payment: `/payment` polls order/invoice status for up to 2 minutes (`app/payment/page.tsx`).
8. Admin-only pages (`/details`, `/users`) rely on role read from `sessionStorage` (`businessDetails` JSON) and CRUD `Business Client` / `Business Client User`.

### 7.3 Workflow C — Consumer OTP login, application & payment

**Actors:** consumer applicant, website frontend, `otp_authentication`, `visaguy_website`, `fileflo`.

1. Anonymous consumer browses `/` and `/country` (server-fetched destinations, `app/page.tsx:22`).
2. On `/country/[slug]`, consumer fills lead form (entry type, stay duration, travel date, travellers, phone, email) (`components/country/form/LeadForm.tsx:28-88`).
3. `create_visa_order` → backend returns `order_id`; frontend stores `lead_details` in `sessionStorage` (`LeadForm.tsx:76-80`).
4. Redirect to `/country/[slug]/application_form`.
5. Application form (`components/application/ApplicationForm.tsx` / `useApplicationForm.ts`):
   - Loads applicant types via `getDocList("Applicant Type")`.
   - For each applicant, selects applicant type and fetches dynamic file template via `get_file_template`.
   - Validates all applicants; at least one must be `Primary`.
   - `submit_application` → backend returns `payment_url`; frontend redirects (`useApplicationForm.ts:430-438`).
6. After payment, consumer lands on `/payment/success` (static page).
7. Authenticated dashboard (`/dashboard`):
   - Login via `/login`: email → `user_check_otp_send` → OTP → `otp_verification` → response contains `api_key`/`api_secret` (`useLogin.ts:22-60`).
   - Credentials stored in `localStorage`; every Axios request carries `token {apiKey}:{apiSecret}` (`lib/services/config.ts:13-29`).
   - `RequireAuth` guards `/dashboard` and `/dashboard/[slug]` (`components/auth/RequireAuth.tsx:56-74`).
   - Dashboard lists `Visaguy Website Visa Order` documents (`app/dashboard/page.tsx`).
   - Detail page (`/dashboard/[slug]`):
     - If status is `Draft`, shows `DraftApplication` to resume form.
     - Otherwise shows `ProcessDetailsForm`, which loads `FF File Collection` per applicant and submits via `fileflo.data_collection.add_form_data` (`useProcessDetailsForm.ts:98,444`).
     - Completed applicants can download deliverables via `get_applicant_files` (`ProcessDelivarables.tsx:30`).

---

## 8. Security & Trust Boundaries (FE5)

| # | Boundary / concern | Evidence | Risk level |
|---|---|---|---|
| 1 | **No frontend authentication for eligibility checker** — direct `Raw Lead`/`Lead` writes with only `Content-Type` header. | `src/components/visa-checker/utils.ts:349-354`, `docs/frappe-crm.md:98` | High |
| 2 | **Eligibility FastAPI CORS is `allow_origins=["*"]` with `allow_credentials=True`.** | `server/main.py:17-24` | High |
| 3 | **OAuth access/refresh tokens stored in `localStorage`.** | `visaguy_business_client/contexts/auth-context.tsx:37-38`, `lib/api.ts:25` | High |
| 4 | **OAuth `CLIENT_ID`/`CLIENT_SECRET` are public (browser env + login form).** | `visaguy_business_client/lib/auth.ts:4-5`, `:27-29` | Medium |
| 5 | **Website `api_key`/`api_secret` stored in `localStorage` and sent on every request.** | `visaguy-website-client/lib/services/config.ts:13-29`, `lib/context/auth-context.tsx:28-29,56-57` | High |
| 6 | **Website OTP returns long-lived API credentials with no evident rotation/refresh.** | `app/login/useLogin.ts:56-60` | Medium |
| 7 | **Business admin gating is client-side only (`sessionStorage`).** | `app/users/page.tsx:39-74`, `app/details/page.tsx:100-138` | High |
| 8 | **OpenAI API key stays server-side; browser receives only ephemeral client secret.** | `server/utils/openai_client.py:17`, `server/routers/voice.py:31-84` | Low / good boundary |
| 9 | **Voice prompt/instructions returned to browser alongside client secret** — potential prompt disclosure. | `server/routers/voice.py:84`, `services/voice-realtime.ts:55` | Low |
| 10 | **Hard-coded fallback API URL in business order detail page.** | `app/orders/[id]/page.tsx:32` | Medium |
| 11 | **Payment flow depends on backend `payment_url` redirect; no frontend failure page or webhook verification in either B2B or consumer surface.** | B2B: `services/api-service.ts:976-1002`; Consumer: `useApplicationForm.ts:430-438` | Medium |
| 12 | **PII/lead data (name, mobile, email, passport, salary, travel history) sent to Frappe; eligibility checker does so unauthenticated.** | `utils.ts` payloads, `LeadForm.tsx:67-80` | High |
| 13 | **Consumer `lead_details` carried in `sessionStorage` between lead form and application form.** | `components/country/form/LeadForm.tsx:77-80` | Low |
| 14 | **Business client build quality gates disabled** (`ignoreDuringBuilds`, `ignoreBuildErrors`). | `next.config.mjs:4-8` | Medium |
| 15 | **No runtime env validation** — missing `NEXT_PUBLIC_API_BASE_URL` or `NEXT_PUBLIC_FRAPPE_BASE_URL` causes runtime failures. | `lib/api.ts:4`, `lib/services/config.ts:4` | Medium |
| 16 | **No tests or CI for eligibility checker and website; Jenkins uses `docker compose down \| true` masking failures.** | `Jenkinsfile:30` | Low / process |

---

## 9. Cross-Frontend Duplication, Coupling & Open Questions (FE6)

### 9.1 Duplication & coupling

| Concern | Observation |
|---|---|
| **No shared component library / monorepo** | Each repo ships its own component set, theme tokens, button styles and API service layer. |
| **Duplicate destination data** | Both B2B and consumer frontends read `Destination` but via different fields/filters (`custom_enabled_for_business` vs `custom_enabled_for_website`). |
| **Duplicate payment pattern** | Both B2B and consumer rely on backend-generated `payment_url` with no shared frontend payment component. |
| **Duplicate Frappe REST boilerplate** | All three repos hand-roll fetch/axios against Frappe instead of using a generated client. |
| **Duplicate UI primitives** | Tailwind v4 + shadcn/ui is used by both Next.js apps, but themes/variables differ. |
| **Duplicate mobile validation logic** | Eligibility checker and website both implement phone-number normalisation independently. |

### 9.2 Missing shared contracts

- No shared OpenAPI/TypeScript contract for Frappe methods; types are duplicated/inlined (`types/index.ts`, `lib/types/`, `src/components/visa-checker/constants.ts`).
- No shared auth/session strategy; three separate patterns (none, OAuth tokens, API-key tokens).
- No shared error-handling contract across frontends.

### 9.3 Open questions

1. Which backend app owns the `Raw Lead` and `Lead` DocTypes consumed by the eligibility checker?
2. Which app owns `Destination`, `Destination Mode`, `Destination Region`? Is it `the_visaguy`, `visaguy_website`, or shared?
3. Which app owns `Applicant Type` and `FF File Collection`?
4. What Frappe permission model enables unauthenticated eligibility-checker writes, and is it intentional for production?
5. Why does the business client contain both `bun.lock` and `pnpm-lock.yaml`, and which is authoritative?
6. Is the hard-coded fallback API URL (`https://temp-visaguy.fstg.tridz.in`) still valid?
7. What is the intended payment-provider surface? The frontends never integrate a provider SDK directly.
8. Are the consumer `/contact` and `/careers` pages intentionally omitted or pending?
9. Why does `ProcessDetailsForm` Save simulate a delay instead of persisting?
10. Are the disabled ESLint/TypeScript build gates in the business client a temporary workaround or permanent?

---

## 10. Local Development, Build, Lint & Deployment Checklists (FE4)

These checklists are derived from checked-in scripts, docs and config only. No install/build commands were executed.

### 10.1 `visa_eligibility_checker`

```text
□ Install Bun (project uses bun.lock)
□ Run bun install at repo root
□ Create .env or .env.local with:
    VITE_PUBLIC_ZONE
    VITE_PUBLIC_API_URL
    VITE_PUBLIC_FRAPPE_BASE_URL
    VITE_PUBLIC_WHATSAPP_NUMBER
□ Backend:
    cd server
    python -m venv venv && source venv/bin/activate
    pip install -r requirements.txt
    cp .env.example .env  # set OPENAI_API_KEY
    uvicorn main:app --reload --port 8000
□ Frontend: bun dev  → http://localhost:5173
□ Lint: bun run lint
□ Build: bun run build  → dist/
□ Preview: bun run preview
□ Verify voice mode requires backend + mic permission
```

### 10.2 `visaguy_business_client`

```text
□ Choose package manager: pnpm is used by Dockerfile; bun.lock also exists
□ Install: pnpm install  (or bun install)
□ Create .env.local with:
    NEXT_PUBLIC_API_BASE_URL
    NEXT_PUBLIC_CLIENT_ID
    NEXT_PUBLIC_CLIENT_SECRET
    NEXT_PUBLIC_ZONE
    NEXT_PUBLIC_CURRENCY
    NEXT_PUBLIC_CONTACT_URL
    NEXT_PUBLIC_INVOICE_PRINT_FORMAT
    NEXT_PUBLIC_INVOICE_LETTERHEAD
□ Dev: pnpm dev  → http://localhost:3000
□ Lint: pnpm lint
□ Build: pnpm build
□ Start: pnpm start
□ Docker (optional): docker build -f Dockerfile .  /  docker compose -f compose.yaml up -d --build
□ Jenkins deployment copies workspace to /home/frappe/visaguy-business/ then docker compose up -d --build
□ GitHub Actions builds/pushes image on pushes to dev branch
```

### 10.3 `visaguy-website-client`

```text
□ Install: bun install (or npm/pnpm/yarn)
□ Create .env.local with:
    NEXT_PUBLIC_FRAPPE_BASE_URL
□ Dev: bun dev  → http://localhost:3000 (Turbopack)
□ Build: bun run build
□ Start: bun run start
□ Lint: bun run lint
□ No repo-level Docker/CI; README points to Vercel
□ Verify image hostnames in next.config.ts if changing Frappe domain
```

---

## 11. Summary Metrics

| Metric | Value |
|---|---|
| Frontends covered | 3 / 3 |
| End-to-end workflow maps | 3 |
| Distinct API contracts documented | 40 |
| Security / trust-boundary risks listed | 16 |
| Repository git status | clean (all three) |

## 12. Verdict

All three frontends are covered, the three required workflow maps are present, API/auth/security and operating-procedure sections are complete, and the source repositories remain read-only and clean. The report is ready for use in the canonical workspace initialisation phase.
