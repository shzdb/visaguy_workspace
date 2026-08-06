# 01a — Local Frontend Reconnaissance

## Scope & Methodology

- Repositories inspected read-only:
  1. `/home/shzd/Projects/tridz/visa_eligibility_checker` — `tvgglobal/visa_eligibility_checker`
  2. `/home/shzd/Projects/tridz/visaguy_business_client` — `tridz-dev/visaguy_business_client`
  3. `/home/shzd/Projects/tridz/visaguy-website-client` — `tvgglobal/visaguy-website-client`
- Evidence sources: `package.json`, lockfiles, `README.md`, source tree, checked-in config/docs, and source-level greps.
- No application code was modified. No secrets or values from `.env`/`.env.local` were read or recorded; only environment variable **names** are listed.
- Git status remained clean for all three repositories throughout the phase.

## Implementation Evidence (HEAD / branch / date)

| Repository | Origin | Branch | HEAD SHA | Last Commit Date | Files Inspected |
|---|---|---|---|---|---|
| `visa_eligibility_checker` | `tvgglobal/visa_eligibility_checker` | `main` | `2d46af4ebb4f5bcd26cc40b535b3233a643ff9fc` | 2026-06-25 13:24:23 +0530 | ~162 |
| `visaguy_business_client` | `tridz-dev/visaguy_business_client` | `main` | `6c3d365a48518008b2769fe4361278dbd0744b74` | 2026-03-27 01:18:20 +0400 | ~133 |
| `visaguy-website-client` | `tvgglobal/visaguy-website-client` | `main` | `3b066f6baa7291fa3f778e8d7c1d70e236f0db80` | 2025-08-10 20:02:23 +0000 | ~173 |

---

# 1. `visa_eligibility_checker` (`tvgglobal/visa_eligibility_checker`)

## LF1 — Framework, Toolchain, Entry Points, Routes, State, Build

### Framework & toolchain
- **Framework:** React 19 (`package.json:17-18`).
- **Build tool:** Vite 7 (`package.json:37`), with `@vitejs/plugin-react` (`package.json:28`).
- **Package manager:** Bun — `bun.lock` present at repository root.
- **TypeScript:** TypeScript 5.9 (`package.json:35`), project references via `tsconfig.json` → `tsconfig.app.json` + `tsconfig.node.json`.
- **CSS:** Tailwind CSS v4 (`tailwindcss@4.1.18`, `@tailwindcss/vite@4.1.18` in `package.json:15,20`), configured in `vite.config.ts:8`. Theme tokens are declared via `@theme` in `src/index.css:3-22`; `tailwind.config.ts` is a minimal leftover.
- **Linting:** ESLint 9 flat config (`eslint.config.js:8`) with `typescript-eslint`, `eslint-plugin-react-hooks`, `eslint-plugin-react-refresh`.
- **Entry points:** `index.html:22` → `<script type="module" src="/src/main.tsx">`; `src/main.tsx:8` mounts `<App />`; `src/App.tsx:4` renders only `<VisaChecker />`.
- **Path alias:** `@/*` → `./src/*` in `tsconfig.app.json:27` and `vite.config.ts:11`.

### Route / page structure
- **No routing library** is used. No `react-router`, no route table, no URL-based navigation.
- The UI is a single-page component tree rooted at `VisaChecker` (`src/App.tsx:4`).
- Screens are rendered conditionally inside `visa-checker.tsx` and `voice-mode.tsx` based on local `mode`/`step` state:
  - Mode selection: `src/components/visa-checker/mode-select.tsx` (triggered when `mode === null`, `visa-checker.tsx:227`).
  - Chat intro / text / tel / choice / country-select steps: inline in `visa-checker.tsx:245-341`.
  - Voice pre-details modal: `src/components/visa-checker/user-details-card.tsx`.
  - Processing screen: `src/components/visa-checker/processing-screen.tsx`.
  - Result screen: `src/components/visa-checker/result-screen.tsx`.

### State & data layer
- **State management:** Pure local React `useState`/`useRef`. No Redux, Zustand, Context, or stores (`visa-checker.tsx:17-23`, `voice-mode.tsx:15-29`).
- **Data fetching:** Native `fetch` only. No axios/TanStack Query/SWR.
  - `src/services/ai-recommendations.ts` — `fetchAIRecommendation`.
  - `src/services/voice-realtime.ts` — `VoiceRealtime` class.
  - `src/components/visa-checker/utils.ts` — CRM helpers calling Frappe directly.
- **Types:** Inline in `*.ts` files. Notable: `src/config/zone-config.ts:6`, `src/components/visa-checker/constants.ts:328`, `src/components/visa-checker/utils.ts:282`, `src/services/ai-recommendations.ts:3`.

### Build / deployment / quality
- `package.json:6-10` scripts:
  - `dev`: `vite`
  - `build`: `tsc -b && vite build`
  - `lint`: `eslint .`
  - `preview`: `vite preview`
- **No test script**, no test framework.
- **No CI/CD configs**, no `Dockerfile`, no `compose.yaml`.
- Build output: `dist/` (gitignored generated artifact, not inspected).

## LF2 — User-Facing Capabilities

Implemented, evidenced by source:

1. **Dual input modes** — Voice vs Chat (`src/components/visa-checker/mode-select.tsx`).
2. **Chat step machine** — JSON-driven screens for 11 fields (`visa-checker.tsx`, `constants.ts`, `chat-questions.*.json`).
3. **Voice AI interview** — OpenAI Realtime WebRTC with mic permission handling, transcript UI, animated orb (`voice-mode.tsx`, `voice-realtime.ts`, `voice-orb.tsx`).
4. **Frontend scoring** — `calcScore` in `utils.ts:66`; dependency bonuses/penalties; residency soft cap.
5. **Verdict & factor breakdown** — `getVerdict` + `ResultScreen` with score ring, factors, badge.
6. **AI next-step recommendation** — `fetchAIRecommendation` calls backend `/api/recommendations` with 10 s fallback (`processing-screen.tsx:89-101`).
7. **Visa restriction handling** — `getVisaRestriction` checks nationality × destination against zone JSON, shows restriction card instead of score (`result-screen.tsx:45`).
8. **WhatsApp CTA** — `openWhatsApp` uses `VITE_PUBLIC_WHATSAPP_NUMBER` or fallback from `src/lib/data.ts:2` (`result-screen.tsx:33-43`).
9. **Multi-zone support** — UAE (`tvg`) and Qatar (`tvg-qatar`) with currency/labels/country codes (`zone-config.ts`, `chat-questions.*.json`, `visa-restrictions.*.json`).
10. **CRM lead capture** — Raw Lead creation/update and qualified Lead creation (`utils.ts:337-539`).

**Distinguishing real vs placeholder/dead:**
- `VOICE_QUESTIONS` in `constants.ts:295` is dead code (legacy, not referenced).
- Transcript heuristics in `voice-mode.tsx:199-216` are not used for scoring; authoritative data comes from the `complete_assessment` tool.
- `COUNTRIES_MED` is empty (`constants.ts:93`) and effectively unused.

## LF3 — Backend/API, Auth, Third-Party, Environment Variables

### FastAPI backend (in-repo `server/` directory)
- `server/main.py:26-27` mounts routers.
- `server/routers/voice.py:18` calls OpenAI `/v1/realtime/client_secrets`.
- `server/routers/recommendations.py:12` calls OpenAI Chat Completions (`gpt-4o-mini`).
- Prompt loader: `server/utils/prompt_loader.py:27`.

### Frontend → backend endpoints
| Endpoint | Caller | Purpose |
|---|---|---|
| `POST /api/voice/client-secret` | `src/services/voice-realtime.ts:41` | OpenAI Realtime ephemeral secret |
| `POST /api/recommendations` | `src/services/ai-recommendations.ts:43` | AI next-step recommendation |

### Frappe / Frappe CRM direct calls
The frontend calls Frappe **directly**, not through the FastAPI backend.

| Operation | Endpoint | Caller |
|---|---|---|
| Create Raw Lead | `POST /api/resource/Raw Lead` | `utils.ts:418` |
| Update Raw Lead | `PUT /api/resource/Raw Lead/{name}` | `utils.ts:521` |
| Create Lead | `POST /api/resource/Lead` | `utils.ts:345` |

- Base URL: `VITE_PUBLIC_FRAPPE_BASE_URL` (`utils.ts:338,400,511`).
- No Authorization headers sent (`docs/frappe-crm.md:98`, confirmed in code).

### Authentication / session
- **None** in the frontend. No login/logout, tokens, or protected routes.
- Frappe calls rely on site-level guest/public permissions and CORS.
- OpenAI access is gated by backend-held `OPENAI_API_KEY`; browser receives only an ephemeral client secret.

### Third-party SDKs / integrations (active)
| Integration | Evidence |
|---|---|
| OpenAI Agents SDK | `@openai/agents` dep (`package.json:13`); imported in `voice-realtime.ts:7,9` |
| OpenAI Realtime API | `VoiceRealtime.connect()` (`voice-realtime.ts:33-157`) |
| OpenAI Chat Completions | `server/routers/recommendations.py:52` |
| Phosphor Icons | `@phosphor-icons/react` (`package.json:14`) |
| WhatsApp (wa.me deep-link) | `result-screen.tsx:37` |
| Frappe REST API | Direct `fetch` to `/api/resource/Raw Lead` and `/api/resource/Lead` |
| Google Fonts | `index.html:17` loads DM Sans + JetBrains Mono |

**Not found:** payment SDKs, analytics SDKs, maps SDKs, communications SDKs beyond WhatsApp deep-linking.

### Environment variable names
- `VITE_PUBLIC_ZONE`
- `VITE_PUBLIC_API_URL`
- `VITE_PUBLIC_FRAPPE_BASE_URL`
- `VITE_PUBLIC_WHATSAPP_NUMBER`
- `OPENAI_API_KEY` (backend)

## LF4 — Customizations, Shared Patterns, Frappe Coupling

- Custom UI component library under `src/components/ui/` with barrel export (`src/components/ui/index.ts`).
- `cn()` utility combining `clsx` + `tailwind-merge` (`src/lib/utils.ts:4`).
- Zone config abstraction (`src/config/zone-config.ts`) supporting multiple markets.
- JSON-driven question/scoring config per zone; CRM payload mapping via `payloadField` in JSON → Lead custom fields.
- Direct Frappe REST coupling; no generated API client.

## LF5 — Operational Procedures

From `docs/getting-started.md` and `README.md`:

```bash
# Frontend
bun install
# create root .env / .env.local with VITE_PUBLIC_* vars
bun dev              # http://localhost:5173

# Backend
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

Build:

```bash
bun run build        # tsc -b && vite build; output to dist/
bun run preview      # serve dist/ locally
```

- No generated clients, no migrations, no database schema scripts.
- Prompt files are read from disk per request; backend restart picks up changes.

## LF6 — Repository Origin & HEAD

- **Origin:** `tvgglobal/visa_eligibility_checker`
- **Branch:** `main`
- **HEAD SHA:** `2d46af4ebb4f5bcd26cc40b535b3233a643ff9fc`
- **Last commit:** 2026-06-25 13:24:23 +0530 — "fix: update restricted-country visa messaging copy"
- **Working tree:** clean

## LF7 — Risks / Unresolved Questions

1. No authentication on Frappe calls; relies on guest/CORS.
2. Qatar salary strings misaligned in voice tool schema (`voice-realtime.ts:79` hardcodes AED options for Qatar).
3. No test coverage or CI/CD.
4. No containerization; deployment process undocumented in repo.
5. `VITE_PUBLIC_ZONE` selects chat questions at build time; zone changes require rebuild.
6. Recommendations API is zone-unaware.
7. Legacy dead code (`VOICE_QUESTIONS`, old transcript heuristics).
8. `server/main.py:20` sets `allow_origins=["*"]` with no environment override.

---

# 2. `visaguy_business_client` (`tridz-dev/visaguy_business_client`)

## LF1 — Framework, Toolchain, Entry Points, Routes, State, Build

### Framework & toolchain
- **Framework:** Next.js 15.2.8 App Router (`app/` directory) with React 19 (`package.json:15,17`).
- **Build tool:** Next.js built-in (`next build`, `next dev`, `next start`).
- **Package manager:** Both `bun.lock` and `pnpm-lock.yaml` exist; `Dockerfile` uses `pnpm`.
- **TypeScript:** `typescript` ^5, `tsconfig.json` with `"jsx": "preserve"`, path alias `"@/*": ["./*"]`.
- **Styling:** Tailwind CSS v4 via `app/globals.css:1` (`@import 'tailwindcss'`); no `tailwind.config.ts` file exists despite `components.json` referencing it.
- **UI system:** shadcn/ui with Radix primitives (`components.json:3-20`).
- **Main entry:** `app/layout.tsx:35` → `AuthProvider` → `ErrorBoundary` → `ProtectedRoute` → `Layout`.

### Route / page structure
Implemented App Router routes:

| Route | File | Status |
|---|---|---|
| `/` (dashboard) | `app/page.tsx` | Implemented |
| `/login` | `app/login/page.tsx` | Implemented |
| `/signup` | `app/signup/page.tsx` | Implemented |
| `/oauth-callback` | `app/oauth-callback/page.tsx` | Dead code — only redirects to `/login` |
| `/orders` | `app/orders/page.tsx` | Implemented |
| `/orders/[id]` | `app/orders/[id]/page.tsx` | Implemented |
| `/order-new` | `app/order-new/page.tsx` | Implemented |
| `/destinations` | `app/destinations/page.tsx` | Implemented |
| `/destinations/[name]` | `app/destinations/[name]/page.tsx` | Implemented |
| `/details` | `app/details/page.tsx` | Implemented (admin-only) |
| `/users` | `app/users/page.tsx` | Implemented (admin-only) |
| `/payment` | `app/payment/page.tsx` | Implemented (payment return/verification) |

Navigation: primary nav in `components/layout.tsx:99-133`; mobile bottom nav at `:227-276`; user menu at `:154-220`.

### State & data layer
- **State:** Local React `useState`/`useEffect` plus `AuthContext`. No Redux/Zustand/Jotai.
- **Auth state:** `contexts/auth-context.tsx` holds `user`, `isAuthenticated`, `login`, `logout`, `refreshToken`.
- **HTTP client:** `lib/api.ts` creates an Axios instance with:
  - Request interceptor injecting `Bearer` token from `localStorage` (`lib/api.ts:23-31`).
  - Response interceptor for 401 token refresh with a request queue (`lib/api.ts:49-111`).
- **API service layer:** `services/api-service.ts` exports `businessService` and `visaService` (~1,100 lines).
- **Types:** `types/index.ts` defines `BusinessClientDetails`, `BusinessClientUser`, `Destination`, `VisaType`, `VisaOrder`, etc.

### Build / deployment / quality
- `package.json:6-9` scripts: `dev`, `build`, `start`, `lint`. No test script.
- `next.config.mjs:2-12`:
  - `eslint.ignoreDuringBuilds: true`
  - `typescript.ignoreBuildErrors: true`
  - `images.unoptimized: true`
- `Dockerfile:1-22` — Node 20.19.1, `pnpm` global, `pnpm install`, `pnpm run build`, exposes 3000, `pnpm start`.
- `compose.yaml:1-39` — service `visaguy-business`, Traefik labels for `visa-business.fstage.tridz.in`, env file `/home/frappe/secrets/.env`.
- `Jenkinsfile:1-40` — copies workspace, `docker compose down | true`, `docker compose up -d --build`.
- `.github/workflows/build_and_push.yml:1-36` — builds/pushes Docker image to Docker Hub on pushes to `dev`.

## LF2 — User-Facing Capabilities

Implemented, evidenced by source:

1. **Authentication:** Login (`app/login/page.tsx:36-76`) and signup (`app/signup/page.tsx:90-162`) with email/password and optional base64 logo upload.
2. **Dashboard** (`app/page.tsx`): wallet balance, order counts, recent active/in-progress orders.
3. **Visa orders list** (`app/orders/page.tsx`): status filter, search, pagination with URL query persistence.
4. **Visa order detail** (`app/orders/[id]/page.tsx`):
   - Add/delete applicants while status is `Open` or `Applicants Submitted`.
   - Generate preliminary document links.
   - Download applicant files.
   - Document checklist validation.
   - Appointment dates (mandatory for Schengen via `config/show_willing_to_travel_via_other_country.json`).
   - Service/invoice selection.
   - Submit order (`createProcessFile`).
   - Request payment (redirects to backend `payment_url`).
   - Download invoice PDF.
5. **New order** (`app/order-new/page.tsx`): two-step wizard (destination + applicants, summary).
6. **Destinations** (`app/destinations/page.tsx`, `app/destinations/[name]/page.tsx`): grid listing, detail with visa types, business/customer prices, document checklist.
7. **Business admin:** Edit business details (`app/details/page.tsx`), user management (`app/users/page.tsx`).
8. **Payment return** (`app/payment/page.tsx`): polls for up to 2 minutes verifying invoice/order status.

**Dead / placeholder / unused:**
- `oauth-callback` route immediately redirects to `/login`.
- `NationalitySelect.tsx` exported but never imported.
- `category-filter.tsx`, `faq-accordion.tsx`, `loading-button.tsx` exist but are not imported.
- `components/ui/sidebar.tsx` is shadcn boilerplate with no app imports.
- Several loading components return `null`.

## LF3 — Backend/API, Auth, Third-Party, Environment Variables

### Authentication / session
- **OAuth2 password flow** with client credentials (`lib/auth.ts:22-50`).
- Tokens stored in `localStorage` keys `accessToken` and `refreshToken` (`contexts/auth-context.tsx:37-38`).
- Session validation on app load: `getLoggedInUser` → fallback refresh → logout (`contexts/auth-context.tsx:94-140`).
- Axios interceptor refreshes access tokens on 401 and redirects to `/login` if refresh fails (`lib/api.ts:49-111`).
- `ProtectedRoute` guards every route (`components/protected-route.tsx:13-47`).
- Role-based UI checks for admin pages rely on `sessionStorage.getItem("businessDetails")` (`app/users/page.tsx:39-74`, `app/details/page.tsx:100-138`).

### Backend / API integrations
Backend is Frappe / ERPNext with custom apps (`visaguy_business`, `the_visaguy.tvg_business`, `the_visaguy.tvg_core`).

**Auth endpoints** (`lib/auth.ts`):
- `POST /api/method/frappe.integrations.oauth2.get_token`
- `GET /api/method/frappe.integrations.oauth2.openid_profile`
- `GET /api/method/frappe.auth.get_logged_user`
- `GET /api/method/frappe.auth.get_user_info`

**Frappe REST resource endpoints** (`services/api-service.ts`):
- `Business Client`, `Business Client User`, `Destination`, `Business Client Checklist`, `Business Client Visa Order`, `Sales Invoice`

**Custom business API methods** (selection):
- `visaguy_business.functions.api.get_business_details.get_business_details`
- `visaguy_business.functions.api.generate_preliminary_documents.generate_preliminary_documents`
- `visaguy_business.functions.api.create_process_file.create_process_file`
- `visaguy_business.functions.api.create_process_file.request_payment_for_visa_order`
- `visaguy_business.functions.api.get_applicant_files.get_applicant_files`
- `the_visaguy.tvg_business.api.get_visa_price.get_visa_price`
- `the_visaguy.tvg_business.api.get_invoice_items.get_invoice_items`
- `the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_visa_types`

**Other Frappe utilities:**
- `POST /api/method/upload_file` (`services/api-service.ts:569`)
- `POST /api/method/frappe.model.workflow.apply_workflow` (`services/api-service.ts:285`)
- `GET /api/method/frappe.utils.print_format.download_pdf` (`services/api-service.ts:1073`)

**API base URL:** `NEXT_PUBLIC_API_BASE_URL`. Hardcoded fallback in `app/orders/[id]/page.tsx:32`: `https://temp-visaguy.fstg.tridz.in`.

### Third-party SDKs / integrations (active)
| Category | Integration | Evidence |
|---|---|---|
| Icons | `lucide-react`, `@phosphor-icons/react` | `package.json` |
| UI primitives | shadcn/ui + Radix UI packages | `package.json`, `components/ui/` |
| Payments | Indirect only — backend generates `payment_url`; frontend redirects | `app/orders/[id]/page.tsx:415` |

**Not found:** analytics, maps, communications SDKs beyond a contact link using `NEXT_PUBLIC_CONTACT_URL`.

### Environment variable names (from `env.example`)
- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_CLIENT_ID`
- `NEXT_PUBLIC_CLIENT_SECRET`
- `NEXT_PUBLIC_ZONE`
- `NEXT_PUBLIC_CURRENCY`
- `NEXT_PUBLIC_CONTACT_URL`
- `NEXT_PUBLIC_INVOICE_PRINT_FORMAT`
- `NEXT_PUBLIC_INVOICE_LETTERHEAD`

## LF4 — Customizations, Shared Patterns, Frappe Coupling

- Tailwind v4 theme variables in `app/globals.css:18-167`; brand palette (`brand-200`, `brand-500`, `brand-600`, etc.).
- Font Inter loaded via `next/font/google` (`app/layout.tsx:12-17`).
- shadcn/ui components under `components/ui/` (~58 files).
- Shared: `components/layout.tsx`, `components/protected-route.tsx`, `components/error-boundary.tsx`, `components/error-display.tsx`, `components/status-badge.tsx`.
- Direct Frappe REST/RPC coupling; no generated client.

## LF5 — Operational Procedures

- Local setup: `pnpm install` (or `bun install`), then `pnpm dev`.
- Build: `pnpm build` → `pnpm start`.
- Docker: `Dockerfile` → `compose.yaml` + Jenkins; GitHub Actions pushes base image on `dev` pushes.
- No migrations / seeding / generated-client scripts in this repo.
- No README or project-specific docs.

## LF6 — Repository Origin & HEAD

- **Origin:** `tridz-dev/visaguy_business_client`
- **Branch:** `main`
- **HEAD SHA:** `6c3d365a48518008b2769fe4361278dbd0744b74`
- **Last commit:** 2026-03-27 01:18:20 +0400
- **Working tree:** clean

## LF7 — Risks / Unresolved Questions

1. Build quality gates disabled (`next.config.mjs:4-8` ignores ESLint/TypeScript errors).
2. Mixed lockfiles / package manager ambiguity (`bun.lock` + `pnpm-lock.yaml`; Dockerfile uses `pnpm`).
3. No automated tests.
4. Dead/unused code (`oauth-callback`, `NationalitySelect`, `category-filter`, `faq-accordion`, `loading-button`, `sidebar`, commented logo blocks).
5. Hardcoded fallback API URL in `app/orders/[id]/page.tsx:32`.
6. Tokens in `localStorage` increase XSS risk.
7. `BusinessClientUser.can_view_all_orders` defined but unused.
8. Admin role checks are client-side only (`sessionStorage`).
9. No runtime env validation; missing `NEXT_PUBLIC_API_BASE_URL` causes runtime failures.

---

# 3. `visaguy-website-client` (`tvgglobal/visaguy-website-client`)

## LF1 — Framework, Toolchain, Entry Points, Routes, State, Build

### Framework & toolchain
- **Framework:** Next.js 15.3.5 with React 19 and App Router (`app/` directory) (`package.json:39,41,45`).
- **Build tool / dev server:** Next.js CLI with Turbopack (`package.json:6`: `"dev": "next dev --turbopack"`).
- **Package manager:** `bun.lock` present.
- **TypeScript:** TS 5 with strict mode (`tsconfig.json:7`).
- **Styling:** Tailwind CSS v4 via `@tailwindcss/postcss` (`package.json:59-60`), custom CSS variables in `app/globals.css:1-196`.
- **UI system:** shadcn/ui "new-york" style (`components.json:3-20`).
- **Linting:** ESLint flat config; many rules explicitly disabled (`eslint.config.mjs:30-47`).
- **Main entry points:** `app/layout.tsx` (root async layout + metadata), `app/page.tsx` (home).

### Route / page structure
Implemented App Router routes:

| Route | File | Notes |
|---|---|---|
| `/` | `app/page.tsx:21` | Async server page; fetches destinations |
| `/login` | `app/login/page.tsx:13` | Email/OTP client page |
| `/dashboard` | `app/dashboard/page.tsx:29` | Protected; lists visa applications |
| `/dashboard/[slug]` | `app/dashboard/[slug]/page.tsx:55` | Protected; application detail |
| `/country` | `app/country/page.tsx:35` | Destination grid |
| `/country/[slug]` | `app/country/[slug]/page.tsx:37` | Country detail + lead form |
| `/country/[slug]/[formSlug]` | `app/country/[slug]/[formSlug]/page.tsx:13` | Application form (`application_form` or `process_form`) |
| `/contact` | `app/contact/page.tsx:8` | Placeholder only |
| `/payment/success` | `app/payment/success/page.tsx:5` | Static success page |

- Nav labels in `components/nav.tsx:250-267`: Home, Countries, Careers, Contact.
- `/careers` is linked but no `app/careers/` route exists.

### State & data layer
- **Global client state:** Redux Toolkit for destination filtering/grid (`lib/store/index.ts:4-8`, `lib/store/destinationSlice.ts:10-104`).
- **React Context:**
  - `AuthContext` — `localStorage`-backed API key/secret session (`lib/context/auth-context.tsx:22-97`).
  - `ConfigContext` — server-fetched website config (`lib/context/config.tsx:8-20`).
  - `ReduxProvider` wraps the app (`lib/context/ReduxProvider.tsx:6`).
- **API client:** Hand-rolled Axios instance in `lib/services/config.ts:3-29` with request interceptor adding `token {apiKey}:{apiSecret}`.
- **Server data helpers:** `getDoc`, `getDocList`, `createDoc`, `updateDoc`, `deleteDoc` in `lib/services/doctype.ts:5-80` call Frappe REST.
- **RPC helper:** `call.post` / `call.get` in `lib/services/call.ts:3-19` prefix methods with `/api/method/`.
- **Types:** `lib/types/index.ts`, `lib/types/destination.ts`, `lib/types/forms.ts`.

### Build / deployment / quality
- `package.json:5-9` scripts: `dev` (Turbopack), `build`, `start`, `lint`. No test script.
- `next.config.ts:3-21` only configures `images.remotePatterns` for:
  - `visaguy.erpcode.tridz.in`
  - `thevisaguy.com`
  - `tvg.fdev.tridz.in`
- **No CI/CD, Dockerfile, or compose file** in this repo.
- ESLint disables `no-unused-vars`, `no-explicit-any`, `react/jsx-key`, `react-hooks/exhaustive-deps`, etc.

## LF2 — User-Facing Capabilities

Implemented, evidenced by source:

1. **Home page (`/`):** Hero search, featured carousel, destination grid with mode/region filters, FAQ, WhatsApp CTA (`components/home/index.tsx:10-27`, `app/page.tsx:21-28`).
2. **Destination browsing (`/country`):** Async list, filters, "View More" pagination via Redux (`app/country/page.tsx:35-69`, `components/country/Destinations.tsx:9-31`).
3. **Country detail (`/country/[slug]`):** Gallery, documents accordion, how-to-apply accordion, FAQ, lead form, WhatsApp support (`app/country/[slug]/page.tsx:37-94`).
4. **Lead capture:** `LeadForm` creates a visa order via Frappe, stores `lead_details` in `sessionStorage`, redirects to application form (`components/country/form/LeadForm.tsx:64-88`).
5. **Application form (`/country/[slug]/application_form`):** Multi-applicant tabs, applicant-type selection, dynamic fields per template, file uploads, validation, submission redirects to `payment_url` (`components/application/ApplicationForm.tsx:11`, `components/application/useApplicationForm.ts:321-444`).
6. **Payment success page (`/payment/success`):** Static congratulations + dashboard link (`app/payment/success/page.tsx:5-34`).
7. **User dashboard (`/dashboard`):** Paginated visa-order grid with search/status/date filters (`components/application/VisaApplicationsGrid.tsx:31-183`).
8. **Application detail (`/dashboard/[slug]`):** Flight ticket summary; `Draft` status resumes form; otherwise shows `ProcessDetailsForm` (`app/dashboard/[slug]/page.tsx:55-121`).
9. **Process details form:** Loads `FF File Collection` per applicant, dynamic fields/files, Save/Submit, deliverables for `Completed` (`components/application/ProcessDetailsForm.tsx:20-125`, `components/application/ProcessDelivarables.tsx:20-149`).
10. **Auth:** OTP login/logout (`app/login/page.tsx:13`, `app/login/useLogin.ts:7-104`).

**Not real implementation / placeholders:**
- `/contact` is a placeholder with no form.
- `/careers` route does not exist despite nav label.
- `ProcessDetailsForm` **Save** button is simulated (1-second delay, no API call) (`components/application/useProcessDetailsForm.ts:348`).
- Footer links point to `#` (`components/footer/FooterLinks.tsx:93-117`).

## LF3 — Backend/API, Auth, Third-Party, Environment Variables

### Authentication / session
- **Flow:** Email → OTP sent → OTP verified → backend returns `api_key`/`api_secret` → stored in `localStorage` → used as Frappe token (`app/login/useLogin.ts:22-60`, `lib/context/auth-context.tsx:53-71`).
- **Session check:** On mount `checkAuth` calls `frappe.auth.get_logged_user`; clears invalid tokens (`lib/context/auth-context.tsx:26-51`).
- **Protected routes:** `RequireAuth` wraps `/dashboard` and `/dashboard/[slug]`; redirects unauthenticated users to `/login` (`components/auth/RequireAuth.tsx:56-74`).
- **Logout:** Removes `api_key`/`api_secret` from `localStorage` (`lib/context/auth-context.tsx:73-77`).

### Backend / API integrations
- **Base URL:** `NEXT_PUBLIC_FRAPPE_BASE_URL` (`env.example:1`, `lib/services/config.ts:4`).
- **Frappe REST patterns:**
  - Resource API: `/api/resource/{doctype}` and `/api/resource/{doctype}/{name}` (`lib/services/doctype.ts:7,42,54,64,74`).
  - Method API: `/api/method/{method}` (`lib/services/call.ts:3`).
- **Doctypes referenced:** `Visaguy Website Configuration`, `Destination Mode`, `Destination Region`, `Destination`, `Visaguy Website Visa Order`, `Applicant Type`, `FF File Collection` (`lib/data/doctypes.ts:1-5`).
- **Frappe/RPC methods called:**
  - `otp_authentication.otp_generation.user_check_otp_send` (`app/login/useLogin.ts:22`)
  - `otp_authentication.otp_verification.otp_verification` (`app/login/useLogin.ts:48`)
  - `frappe.auth.get_logged_user` (`lib/context/auth-context.tsx:37,60`)
  - `visaguy_website.api.create_visa_order.create_visa_order` (`components/country/form/LeadForm.tsx:76`)
  - `visaguy_website.api.get_destination_items.get_destination_items` (`components/country/form/useTotalPrice.ts:21`)
  - `visaguy_website.api.get_file_template.get_file_template` (`components/application/useApplicationForm.ts:185`)
  - `visaguy_website.api.submit_application.submit_application` (`components/application/useApplicationForm.ts:430`)
  - `visaguy_website.api.get_applicant_files.get_applicant_files` (`components/application/ProcessDelivarables.tsx:30`)
  - `fileflo.data_collection.add_form_data` (`components/application/useProcessDetailsForm.ts:444`)
  - `upload_file` (`components/compound/FileUploader.tsx:77`)
- **Coupling:** Tightly coupled to a Frappe/ErpCode backend; no generated client.

### Third-party SDKs / integrations (active)
| Category | Integration | Evidence |
|---|---|---|
| Icons | `@phosphor-icons/react`, `lucide-react` | `package.json` |
| Phone input | `react-phone-number-input` | `components/ui/phone-input.tsx:3` |
| File dropzone | `react-dropzone` | `components/compound/FileUploader.tsx:3` |
| Carousel | `embla-carousel-react` + autoplay | `components/home/FeaturedCarousel.tsx:15` |
| Animations | `framer-motion` | `components/nav.tsx:6` |
| Forms/validation | `react-hook-form`, `@hookform/resolvers`, `zod` v4 | `components/country/form/LeadForm.tsx:3-5` |
| Date/calendar | `react-day-picker`, `date-fns` | `components/ui/calendar.tsx` |
| Radix primitives | Accordion, Dialog, Select, Tabs, etc. | `package.json:14-25`, `components/ui/` |
| Toasts | `sonner` | `components/ui/sonner.tsx` |
| WhatsApp | `wa.me/{number}` deep-links only | `components/country/form/WhatsappSupport.tsx:8` |

**Not present / not active:** payment gateway SDK, analytics, maps, email/communication SDKs. Payment is backend-driven (`payment_url` redirect).

### Environment variable names
- `NEXT_PUBLIC_FRAPPE_BASE_URL`

## LF4 — Customizations, Shared Patterns, Frappe Coupling

- Custom Tailwind theme with brand colors (`--primary: #C6992C`, `--brand-600`, etc.) and custom utilities (`hide-scrollbar`, `animate-move-right-to-left-*`) (`app/globals.css:4-196`).
- shadcn/ui primitives (~30+ files); `Button` extended with `loading`/`loadingText` (`components/ui/button.tsx:40-107`).
- Shared utilities: `cn`, `handleShare`, `formatDateToYYYYMMDD` (`lib/utils.ts:5-27`).
- Compound components: `FileUploader`, `IconInput`, `CaretBackButton`, `VerticalGoldenBar` (`components/compound/`).
- Custom hooks: `useLogin`, `useTotalPrice`, `useApplicationForm`, `useProcessDetailsForm`, `useDynamicForm`.
- Pattern: server components fetch config/lists; client components handle forms/auth; `sessionStorage` carries `lead_details` between lead form and application form; Redux manages destination grid filters/pagination.

## LF5 — Operational Procedures

- Local setup: Standard Next.js dev server (`bun dev` / `npm run dev`) (`package.json:6`, `README.md:7-15`).
- Build: `next build` / `next start` (`package.json:7-8`).
- Lint: `next lint` (`package.json:9`).
- Deployment: No repo-level CI/CD, Dockerfile, or compose file. README points to Vercel (boilerplate) (`README.md:32-34`).
- Migrations / generated clients: None evidenced.
- Required environment: `NEXT_PUBLIC_FRAPPE_BASE_URL`.

## LF6 — Repository Origin & HEAD

- **Origin:** `tvgglobal/visaguy-website-client`
- **Branch:** `main`
- **HEAD SHA:** `3b066f6baa7291fa3f778e8d7c1d70e236f0db80`
- **Last commit:** 2025-08-10 20:02:23 +0000 — "fix: process form values and files upload"
- **Working tree:** clean

## LF7 — Risks / Unresolved Questions

1. Incomplete routes: `/careers` linked but not implemented; `/contact` is placeholder.
2. `ProcessDetailsForm` Save button is simulated, not wired to an API.
3. Payment integration opaque — frontend relies on backend `payment_url`; no SDK, webhook handler, or failure page.
4. Hardcoded content in places (departure "UAE", `AED 441`, T&C assumes UAE citizenship).
5. API key and secret stored in `localStorage` and sent via request header.
6. ESLint disables many lint rules; no tests or CI/CD.
7. TODOs remain (home destination skeleton, invalid form slug not-found handling).

---

# Comparison Summary

| Concern | `visa_eligibility_checker` | `visaguy_business_client` | `visaguy-website-client` |
|---|---|---|---|
| **Owner** | `tvgglobal` | `tridz-dev` | `tvgglobal` |
| **Framework** | React 19 + Vite | Next.js 15 App Router + React 19 | Next.js 15 App Router + React 19 |
| **Package manager** | Bun (`bun.lock`) | Both `bun.lock` + `pnpm-lock.yaml`; Dockerfile uses `pnpm` | Bun (`bun.lock`) |
| **Styling** | Tailwind v4 | Tailwind v4 | Tailwind v4 |
| **UI library** | Custom components | shadcn/ui + Radix | shadcn/ui + Radix |
| **State** | Local `useState`/`useRef` | Local state + `AuthContext` | Redux Toolkit + `AuthContext` + `ConfigContext` |
| **HTTP client** | Native `fetch` | Axios (token interceptor, refresh queue) | Axios (token interceptor) |
| **Routing** | None — single-page state machine | Next.js App Router | Next.js App Router |
| **Auth** | None | OAuth2 password + refresh tokens in `localStorage` | Email/OTP → API key/secret in `localStorage` |
| **Backend** | FastAPI (`server/`) + direct Frappe REST | Direct Frappe REST/RPC | Direct Frappe REST/RPC |
| **Generated API client** | None | None | None |
| **Tests** | None | None | None |
| **CI/CD** | None | Jenkins + Docker + GitHub Actions | None |
| **Containerization** | None | Dockerfile + compose.yaml | None |
| **Payments** | WhatsApp deep-link only | Backend `payment_url` redirect | Backend `payment_url` redirect |
| **Analytics** | None | None | None |
| **Most recent commit** | 2026-06-25 | 2026-03-27 | 2025-08-10 |

## Cross-Frontend Relationships & Frappe Coupling

1. All three frontends target Frappe/ERPNext backends, but each targets a different surface:
   - `visa_eligibility_checker` writes to `Raw Lead` and `Lead` doctypes (guest/public).
   - `visaguy_business_client` targets `Business Client`, `Business Client Visa Order`, `Sales Invoice`, etc.
   - `visaguy-website-client` targets `Visaguy Website Visa Order`, `Destination`, `FF File Collection`, etc.
2. **No shared component library or monorepo** across the three repos; each has its own component set, theme tokens, and API service layer.
3. **No generated API clients** anywhere; all HTTP calls are hand-written against Frappe REST/RPC.
4. **No shared authentication/session** across frontends; each has its own token storage strategy.
5. **Payment flow pattern is consistent** between `visaguy_business_client` and `visaguy-website-client`: backend returns a `payment_url`, frontend redirects.
6. **Tailwind v4 + shadcn/ui** is the direction for the two Next.js apps; `visa_eligibility_checker` uses a custom component library.

## Workspace Status

- Output written to: `/home/shzd/Projects/workspaces/visaguy_workspace/ongoing/visaguy-workspace-initialization/01a-local-frontends.md`
- Git status of all three frontend repositories: **clean**.
- No secrets, credentials, `.env` values, build artifacts, or dependency trees were read or recorded.
