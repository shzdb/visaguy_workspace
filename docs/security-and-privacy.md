# Security and Privacy

This section records evidenced controls and recommended follow-up decisions. It does not claim unverified controls are implemented.

## Credentials and tokens

| Asset | Location / handling | Evidence | Recommended control |
|---|---|---|---|
| OpenAI API key | FastAPI backend env (`server/utils/openai_client.py`) | `03c-frontends.md` §3.6 | Keep server-side; rotate periodically. |
| OAuth access/refresh tokens | Browser `localStorage` (`accessToken`, `refreshToken`) | `03c-frontends.md` §4.4 | Move to `httpOnly` secure cookies; add token binding/rotation. |
| OAuth client ID/secret | Public env + login form (`lib/auth.ts`) | `03c-frontends.md` §4.4 | Use PKCE or confidential backend proxy; avoid exposing client secret. |
| API key/secret (consumer portal) | Browser `localStorage` + `token {key}:{secret}` header | `03c-frontends.md` §5.4 | Replace with short-lived session cookies; enforce key rotation. |
| Frappe site secrets | `site_config.json` (not inspected) | `01b-remote-bench.md` RB1 | Restrict file permissions; do not commit. |

## CORS / guest access

- Eligibility checker sends unauthenticated `POST/PUT` to `/api/resource/Raw Lead` and `/api/resource/Lead` with only `Content-Type: application/json`.
- FastAPI companion sets `allow_origins=["*"]` and `allow_credentials=True`.

**Recommended follow-up:** restrict CORS to known origins; require a lightweight rate-limited token or captcha for public lead writes; validate Frappe DocType permissions for guest `Raw Lead`/`Lead` creation.

## PII / lead / application data

Data classes observed:

- Eligibility checker: full name, mobile number, destination, nationality, residency, employment, salary, bank statements, visa refusals.
- Consumer portal: email, phone, travellers, travel dates, passport/identity documents, applicant files.
- B2B portal: business details, applicant documents, invoices, payments.

**Recommended follow-up:** document data-retention policy; encrypt uploads at rest; mask PII in logs; add consent capture for marketing use.

## Browser storage

- `localStorage`: OAuth tokens (B2B), API key/secret (consumer).
- `sessionStorage`: `lead_details` between lead form and application form (consumer); `businessDetails` for client-side admin gating (B2B).

**Recommended follow-up:** migrate auth credentials out of `localStorage`; do not rely on `sessionStorage` for authorization decisions.

## Provider secrets

Provider credentials for OpenAI, WhatsApp, Twilio/Exotel, FCM, Meta/Google, MyFatoorah/TotalPay, OTP gateway, S3/Dropbox are stored in settings DocTypes or environment variables. This audit inspected only key names, not values.

**Recommended follow-up:** audit all settings DocTypes for populated secrets; store env secrets in a vault; rotate any long-lived keys.

## Uploads

- File uploads use Frappe `upload_file`.
- Documents are collected via `FF File Collection` and `fileflo.data_collection.add_form_data`.

**Recommended follow-up:** restrict file types and sizes; scan uploads; ensure private files are not publicly accessible.

## Database / config / log exclusions

- Do not commit `site_config.json`, `.env`, `*.pem`, database dumps, or error logs to application repositories.
- Build outputs (`dist/`, `.next/`) are gitignored.

**Recommended follow-up:** add pre-commit hooks for secret scanning; centralize log shipping with PII redaction.

## High-risk findings

| # | Finding | Risk |
|---|---|---|
| 1 | Eligibility checker performs unauthenticated guest writes to `Raw Lead`/`Lead`. | High |
| 2 | FastAPI CORS `allow_origins=["*"]` with credentials enabled. | High |
| 3 | OAuth tokens and consumer API key/secret stored in browser `localStorage`. | High |
| 4 | Business-client admin gating relies on client-side `sessionStorage` only. | High |
| 5 | PII/lead data sent to Frappe without evident rate limiting or captcha. | High |

See [`risks-and-open-questions.md`](risks-and-open-questions.md) for the full register.
