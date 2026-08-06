# System Overview

## Topology

```text
┌──────────────────────────────────────────────────────────────────────────────┐
│                              External Providers                               │
│  OpenAI  │  WhatsApp (Business API / wa.me)  │  Twilio / Exotel  │  FCM     │
│  Meta / Google Conversions API  │  MyFatoorah / TotalPay  │  Stripe / Razorpay │
│  PayPal / PayTM / Braintree / GoCardless / M-Pesa  │  Zoho (legacy CRM) │
│  S3 / Dropbox backups  │  SAP (Waflo keyword)  │  OTP gateway  │            │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
┌──────────────────────────────────────────────────────────────────────────────┐
│                         Frappe Bench — site `visaguy`                         │
│  Frappe 15.113.0 + ERPNext 15.106.0 + HRMS 15.45.2 + Payments 0.0.1         │
│  Redis  │  scheduler (`bench schedule`)  │  workers (`bench worker`)         │
│  Node v12 system / Node v18 socketio (via `.nvm`)                           │
├──────────────────────────────────────────────────────────────────────────────┤
│  Installed external apps (9)                                                  │
│  frappe · erpnext · hrms · payments · india_compliance · insights · raven    │
│  frappe_whatsapp · non_profit                                                 │
├──────────────────────────────────────────────────────────────────────────────┤
│  Internally maintained apps (19)                                              │
│  crm · fileflo · frappe_conversions_api · frappe_notifier · helpdesk          │
│  otp_authentication · passport_extractor · payment_integrations · processflo  │
│  quick_kanban · the_visaguy · visaguy_business · visaguy_crm                  │
│  visaguy_frappe_crm · visaguy_helpdesk · visaguy_hrms · visaguy_raven         │
│  visaguy_website · waflo                                                      │
├──────────────────────────────────────────────────────────────────────────────┤
│  Bench-only external apps (2, not installed on `visaguy`)                     │
│  employee_self_service · mansico_meta_integration                             │
└──────────────────────────────────────────────────────────────────────────────┘
                                       │
┌─────────────────────────────┬─────────────────────────────┬──────────────────┐
│ visa_eligibility_checker    │ visaguy_business_client     │ visaguy-website-client│
│ (React 19 + Vite 7, Bun)    │ (Next.js 15.2.8, App Router)│ (Next.js 15.3.5)      │
│                             │                             │                       │
│  · FastAPI/OpenAI companion │  · OAuth2 password flow     │  · Email/OTP login    │
│  · OpenAI Realtime voice    │  · Bearer tokens in         │  · API key/secret in  │
│  · Chat eligibility scoring │    localStorage             │    localStorage       │
│  · Direct Frappe Raw Lead / │  · Business Client Visa     │  · Consumer visa order│
│    Lead writes (guest)      │    Order lifecycle          │    / application form │
│  · WhatsApp CTA             │  · process file + payment   │  · payment_url redirect│
└─────────────────────────────┴─────────────────────────────┴──────────────────┘
```

## Core domain axes — Zone and Company

Read this before designing anything that scopes data. Getting it wrong is invisible in a single-market setup and expensive later. Full rationale in [ADR-006](../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md).

**Zone and Company are independent axes carried on the same record. Neither derives from the other.**

| | Zone | Company |
|---|---|---|
| Means | The operational **market** an employee works in | The **legal entity** employing the person |
| Drives | Lead management, operations, permission scoping, currency, customer-facing identity | Invoicing, payroll, statutory and GST compliance, HR |
| Example attribute | `Zone.currency` | Employment and financial records |
| Set by | `visaguy_frappe_crm/functions/add_zone.py` from the session user's Employee | same function, independently |

Current values: zones `TVG`, `TVG Qatar`, `TVG Saudi`; companies `TVG`, `TVG Qatar`, `TVG Saudi`, `TVG  India`.

**`TVG India` is a back-office branch.** Its employees work in India but handle leads and operations belonging to the UAE or Qatar markets. So a Lead can legitimately carry `custom_zone = TVG` (UAE market) and `custom_company = TVG India` (the entity that employs whoever created it), and staff assigned to the `TVG` zone can access it.

This is why there are four companies but three zones. **The missing `TVG India` zone is correct by design, not a data gap** — a back office serves other zones and has no customers of its own.

Three of the four names coincide, which makes wrong code look right during development. Do not rely on name matching between the two axes. Note also that `TVG  India` contains a double space.

### Routing rule

- **Customer-facing → Zone.** WhatsApp numbers and messaging configuration, currency, market defaults, communication branding.
- **Legal, financial, HR → Company.** Invoices, payroll, statutory compliance.
- **Permission scoping → either, by configuration.** `visaguy_frappe_crm/functions/lead_restrictions.py` branches on `TVG User Restriction.lead_manager_company_restriction` versus `.lead_manager_zone_restriction`.

When a question presents itself as "which company owns this", check whether it is really "which market is this customer in". If it is customer-visible, the answer is Zone.

## Trust boundaries and data flow

| Boundary | From | To | Evidence | Status |
|---|---|---|---|---|
| Voice/chat assessment | `visa_eligibility_checker` | FastAPI companion | `server/main.py` routers | source-wired |
| Ephemeral OpenAI secret | FastAPI | OpenAI Realtime API | `server/routers/voice.py` | source-wired |
| Recommendation | FastAPI | OpenAI Chat Completions | `server/routers/recommendations.py` | source-wired |
| Public lead capture | `visa_eligibility_checker` | Frappe `/api/resource/Raw Lead`, `/api/resource/Lead` | `03c-frontends.md` §3.5 | source-wired |
| B2B order & payment | `visaguy_business_client` | `visaguy_business` APIs + Frappe REST | `03c-frontends.md` §4.5 | source-wired |
| Consumer order & application | `visaguy-website-client` | `visaguy_website`, `otp_authentication`, `fileflo` | `03c-frontends.md` §5.5 | source-wired |
| Internal process/file workflow | `visaguy_website` / `visaguy_business` | `processflo`, `fileflo`, `payment_integrations` | `03a-maintained-apps.md` W2/W3 | source-wired |
| CRM pipeline | `the_visaguy` / `visaguy_frappe_crm` | `crm` → ERPNext `Customer` | `03a-maintained-apps.md` W1 | source-wired |
| Notifications | Doc events across apps | `visaguy_raven`, `frappe_notifier`, `frappe_whatsapp` | `03a-maintained-apps.md` MA3 | source-wired |
| Passport extraction | `fileflo` upload | `the_visaguy.visa_tracking` → `passport_extractor` (local OCR only) | [`workflows.md`](workflows.md) W6 | source-wired, unmerged |
| Public status lookup | `visa_tracker` SPA (not built) | `the_visaguy.visa_tracking.api` guest endpoints | [`workflows.md`](workflows.md) W6 | backend source-wired; no client exists |

Full call chains for every workflow are documented in [`workflows.md`](workflows.md).

## Verified vs unresolved joins

### Confirmed joins

| Join | Evidence |
|---|---|
| Eligibility checker → create/update `Raw Lead` | Frontend endpoints + backend `Raw Lead` DocType |
| Eligibility checker → create qualified `Lead` | Frontend score threshold + backend CRM hooks |
| `Raw Lead` → `CRM Lead` | `the_visaguy.convert_to_crm_lead` + `visaguy_frappe_crm` hooks |
| `CRM Lead` → `CRM Deal` → ERPNext `Customer` | `crm.crm_lead.convert_to_deal` + `erpnext_crm_settings` |
| B2B portal → `Business Client Visa Order` | Frontend resource API + backend DocType/fixtures |
| B2B portal → `create_process_file` | Frontend calls backend whitelisted method |
| B2B portal → request payment | Frontend calls backend method returning `payment_url` |
| Consumer website → create visa order / submit application | Frontend calls backend whitelisted methods |
| Consumer website → `fileflo.data_collection.add_form_data` | Frontend calls backend whitelisted method |
| OTP login → API credentials | Frontend OTP flow + backend credential issuance |

### Unresolved joins

| Join | Status |
|---|---|
| Consumer website → `visaguy_business.create_process_file` | Unresolved — no frontend evidence |
| Consumer order → `PF Process File` / payment | Unresolved — frontend only sees `payment_url` |
| Exact owner of `Raw Lead` / `Lead` DocTypes consumed by eligibility checker | Unresolved from frontend evidence |
| Exact owner of `Destination` / `Destination Mode` / `Destination Region` | Unresolved from frontend evidence |
| Exact owner of `Applicant Type` and `FF File Collection` | Unresolved from frontend evidence |

## Process topology

The Frappe bench runs the following services (from `Procfile`):

- Redis trio: `redis_cache`, `redis_socketio`, `redis_queue`.
- Web: `bench serve --port 8008`.
- SocketIO: Node v18 runtime for `apps/frappe/socketio.js`.
- Watch: `bench watch`.
- Schedule: `bench schedule`.
- Worker: `bench worker`.

## Runtime notes

- System Node is v12.22.9 while Socket.IO uses Node v18.20.8 via `.nvm`.
- This split may affect frontend builds and asset tooling during upgrades.
