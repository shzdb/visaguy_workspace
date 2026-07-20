# Frontends

VisaGuy has three independent web frontends. Each targets a different actor and uses a different authentication model.

| Repository | Owner | Framework | HEAD / Date | Actors | Auth |
|---|---|---|---|---|---|
| `visa_eligibility_checker` | `tvgglobal` | React 19 + Vite 7 | `2d46af4e` / 2026-06-25 | Anonymous consumers | None (guest Frappe writes) |
| `visaguy_business_client` | `tridz-dev` | Next.js 15.2.8 App Router | `6c3d365a` / 2026-03-27 | Business admins, standard business users | OAuth2 password grant |
| `visaguy-website-client` | `tvgglobal` | Next.js 15.3.5 App Router | `3b066f6b` / 2025-08-10 | Consumer applicants | Email/OTP → API key/secret |

## Frontend 1 — Public eligibility checker

### Framework and build

- React 19, Vite 7, TypeScript 5.9, Tailwind CSS v4, Bun.
- No routing library; single-page state machine driven by `mode` and `step`.
- Build: `bun run build` → `dist/`; preview: `bun run preview`.
- FastAPI/OpenAI companion backend in `server/` directory.

### State and data flow

- Pure local React `useState`/`useRef`.
- Native `fetch` for HTTP.
- Chat flow: name/mobile → create `Raw Lead` → incremental updates → score → qualified `Lead` creation.
- Voice flow: collect name/phone → OpenAI Realtime interview → `complete_assessment` tool → same processing path.

### API contracts

| Contract | Method / Path | Purpose |
|---|---|---|
| FastAPI voice secret | `POST /api/voice/client-secret` | Ephemeral OpenAI client secret |
| FastAI recommendation | `POST /api/recommendations` | AI next-step recommendation |
| Create Raw Lead | `POST /api/resource/Raw Lead` | Lead capture |
| Update Raw Lead | `PUT /api/resource/Raw Lead/{name}` | Incremental updates |
| Create Lead | `POST /api/resource/Lead` | Qualified lead when score ≥ 55 |

### Environment variables

- `VITE_PUBLIC_ZONE`
- `VITE_PUBLIC_API_URL`
- `VITE_PUBLIC_FRAPPE_BASE_URL`
- `VITE_PUBLIC_WHATSAPP_NUMBER`
- `OPENAI_API_KEY` (backend only)

## Frontend 2 — B2B business portal

### Framework and build

- Next.js 15.2.8 App Router, React 19, Tailwind CSS v4, shadcn/ui.
- Both `bun.lock` and `pnpm-lock.yaml` exist; `Dockerfile` uses `pnpm`.
- Build config disables ESLint and TypeScript errors during build.
- Docker, compose, Jenkins, and GitHub Actions workflows exist.

### Routes

| Route | Purpose |
|---|---|
| `/` | Dashboard |
| `/login`, `/signup` | Authentication |
| `/orders`, `/orders/[id]` | Order list and detail |
| `/order-new` | Create order |
| `/destinations`, `/destinations/[name]` | Destination catalog |
| `/details`, `/users` | Admin-only pages |
| `/payment` | Payment return / polling |

### State and auth

- `AuthContext` holds user state; tokens stored in `localStorage` (`accessToken`, `refreshToken`).
- Axios instance with request interceptor injecting `Bearer` token.
- Response interceptor refreshes on 401 and redirects on failure.
- Admin gating is client-side only via `sessionStorage`.

### API contracts

| Contract | Method / Path | Backend App |
|---|---|---|
| OAuth token | `POST /api/method/frappe.integrations.oauth2.get_token` | Frappe |
| Business Client CRUD | `POST/GET/PUT /api/resource/Business Client` | `visaguy_business` |
| Business Client User CRUD | `GET/POST/PUT/DELETE /api/resource/Business Client User` | `visaguy_business` |
| Business Client Visa Order CRUD | `GET/POST/PUT /api/resource/Business Client Visa Order` | `visaguy_business` |
| Get visa types | `POST /api/method/the_visaguy...get_visa_types` | `the_visaguy` |
| Get visa price / invoice items | `POST /api/method/the_visaguy...get_visa_price`, `get_invoice_items` | `the_visaguy` |
| Generate preliminary docs | `POST /api/method/visaguy_business...generate_preliminary_documents` | `visaguy_business` |
| Create process file | `POST /api/method/visaguy_business...create_process_file` | `visaguy_business` |
| Request payment | `POST /api/method/visaguy_business...request_payment_for_visa_order` | `visaguy_business` |
| Applicant files | `POST /api/method/visaguy_business...get_applicant_files` | `visaguy_business` |

### Environment variables

- `NEXT_PUBLIC_API_BASE_URL`
- `NEXT_PUBLIC_CLIENT_ID`
- `NEXT_PUBLIC_CLIENT_SECRET`
- `NEXT_PUBLIC_ZONE`
- `NEXT_PUBLIC_CURRENCY`
- `NEXT_PUBLIC_CONTACT_URL`
- `NEXT_PUBLIC_INVOICE_PRINT_FORMAT`
- `NEXT_PUBLIC_INVOICE_LETTERHEAD`

## Frontend 3 — Consumer website

### Framework and build

- Next.js 15.3.5 App Router, React 19, Tailwind CSS v4, shadcn/ui "new-york".
- Turbopack dev server (`next dev --turbopack`).
- No repo-level Docker/CI; README points to Vercel boilerplate.

### Routes

| Route | Purpose |
|---|---|
| `/` | Home / destination list |
| `/login` | OTP login |
| `/dashboard`, `/dashboard/[slug]` | Protected visa applications |
| `/country` | Destination grid |
| `/country/[slug]` | Country detail + lead form |
| `/country/[slug]/[formSlug]` | Application form |
| `/contact` | Placeholder |
| `/payment/success` | Static success page |

### State and auth

- Redux Toolkit for destination grid filters/pagination.
- `AuthContext` stores `api_key`/`api_secret` in `localStorage`.
- Axios request interceptor adds `token {apiKey}:{apiSecret}` header.
- `RequireAuth` guards dashboard routes.

### API contracts

| Contract | Method / Path | Backend App |
|---|---|---|
| Send OTP | `POST /api/method/otp_authentication.otp_generation.user_check_otp_send` | `otp_authentication` |
| Verify OTP | `POST /api/method/otp_authentication.otp_verification.otp_verification` | `otp_authentication` |
| Create visa order | `POST /api/method/visaguy_website.api.create_visa_order.create_visa_order` | `visaguy_website` |
| Get destination items | `GET /api/method/visaguy_website.api.get_destination_items.get_destination_items` | `visaguy_website` |
| Get file template | `GET /api/method/visaguy_website.api.get_file_template.get_file_template` | `visaguy_website` |
| Submit application | `POST /api/method/visaguy_website.api.submit_application.submit_application` | `visaguy_website` |
| Get applicant files | `GET /api/method/visaguy_website.api.get_applicant_files.get_applicant_files` | `visaguy_website` |
| Add form data | `POST /api/method/fileflo.data_collection.add_form_data` | `fileflo` |
| File upload | `POST /api/method/upload_file` | Frappe |

### Environment variables

- `NEXT_PUBLIC_FRAPPE_BASE_URL`

## Cross-frontend observations

- No shared component library or monorepo.
- No generated API clients; all hand-rolled fetch/axios against Frappe.
- No shared auth/session strategy; three separate patterns.
- Payment flow is consistent between B2B and consumer: backend returns `payment_url`, frontend redirects.
- Tailwind v4 + shadcn/ui is the direction for the two Next.js apps.

## Security notes

See [`docs/security-and-privacy.md`](../security-and-privacy.md) for details on:

- Unauthenticated eligibility-checker writes.
- OAuth/API-key tokens in `localStorage`.
- Client-side admin gating in B2B portal.
- FastAPI CORS configuration.

## Local development

See [`docs/operations/local-development.md`](../operations/local-development.md) for setup, build, and lint commands per repository.
