# 03d — Integration Reconciliation, System Topology & Operational Procedures

Generated: 2026-07-20.  
Source: accepted phase reports `01a-local-frontends.md`, `01b-remote-bench.md`, `02-triage.md`, `03a-maintained-apps.md`, `03b-external-apps.md`, `03c-frontends.md`.  
Scope: synthesize cross-system topology, reconcile workflow claims, classify integrations, document customization precedence, and produce evidence-grounded operational runbooks.  
No production commands were executed; no secrets, config values, dirty diffs, or production data are recorded below.

---

## IP1 — End-to-End System Topology

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
│  Internally maintained apps (18)                                              │
│  crm · fileflo · frappe_conversions_api · frappe_notifier · helpdesk          │
│  otp_authentication · payment_integrations · processflo · quick_kanban        │
│  the_visaguy · visaguy_business · visaguy_crm · visaguy_frappe_crm           │
│  visaguy_helpdesk · visaguy_hrms · visaguy_raven · visaguy_website · waflo   │
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

### Trust boundaries and data flow

| Boundary | From | To | Evidence |
|---|---|---|---|
| Voice/chat assessment | `visa_eligibility_checker` | FastAPI companion (`server/main.py:26-27`) | `01a-local-frontends.md` LF3 |
| Ephemeral OpenAI secret | FastAPI (`server/routers/voice.py:18`) | OpenAI Realtime API | `01a-local-frontends.md` LF3 |
| Recommendation | FastAPI (`server/routers/recommendations.py:12`) | OpenAI Chat Completions | `01a-local-frontends.md` LF3 |
| Public lead capture | `visa_eligibility_checker` | Frappe `/api/resource/Raw Lead`, `/api/resource/Lead` | `03c-frontends.md` §3.5 |
| B2B order & payment | `visaguy_business_client` | `visaguy_business` custom APIs + Frappe REST | `03c-frontends.md` §4.5 |
| Consumer order & application | `visaguy-website-client` | `visaguy_website`, `otp_authentication`, `fileflo` | `03c-frontends.md` §5.5 |
| Internal process/file workflow | `visaguy_website` / `visaguy_business` | `processflo`, `fileflo`, `payment_integrations` | `03a-maintained-apps.md` MA3 W2/W3 |
| CRM pipeline | `the_visaguy` / `visaguy_frappe_crm` | `crm` → ERPNext `Customer` | `03a-maintained-apps.md` MA3 W1 |
| Notifications | Doc events across apps | `visaguy_raven`, `frappe_notifier`, `frappe_whatsapp` | `03a-maintained-apps.md` MA3 |

---

## IP2 — Workflow Claim Reconciliation

A join is marked **confirmed** only when both the consumer and the producer side are evidenced in the accepted reports.  Inferred or single-sided joins are labeled **source-wired** or **unresolved**.

| Workflow join | Producer side | Consumer side | Status | Notes |
|---|---|---|---|---|
| Eligibility checker → create `Raw Lead` | Frontend `POST /api/resource/Raw Lead` (`03c-frontends.md` §3.5) | Backend `the_visaguy.tvg_crm.doctype.raw_lead.raw_lead.py:convert_to_crm_lead` (`03a-maintained-apps.md` MA3 W1) | **Confirmed** | Writes are unauthenticated (guest). |
| Eligibility checker → update `Raw Lead` | Frontend `PUT /api/resource/Raw Lead/{name}` (`03c-frontends.md` §3.5) | Backend `Raw Lead` DocType exists (`03a-maintained-apps.md` MA1) | **Confirmed** | Same guest boundary. |
| Eligibility checker → create qualified `Lead` | Frontend `POST /api/resource/Lead` when score ≥ 55 (`03c-frontends.md` §3.3) | Backend legacy CRM / `visaguy_frappe_crm` hooks (`03a-maintained-apps.md` MA3 W1) | **Confirmed** | Trigger is score-threshold fire-and-forget. |
| `Raw Lead` → `CRM Lead` | `the_visaguy.convert_to_crm_lead` (`03a-maintained-apps.md` MA3 W1) | `visaguy_frappe_crm` before_insert hooks (`03a-maintained-apps.md` MA4) | **Confirmed** | Backend-only lifecycle. |
| `CRM Lead` → `CRM Deal` → ERPNext `Customer` | `crm.crm_lead.convert_to_deal` + `erpnext_crm_settings.create_customer_in_erpnext` (`03a-maintained-apps.md` MA3 W1) | ERPNext `Customer` DocType (`03b-external-apps.md` EA2) | **Confirmed** | Backend-only. |
| B2B portal → create `Business Client Visa Order` | Frontend `POST /api/resource/Business Client Visa Order` (`03c-frontends.md` §4.5) | Backend `visaguy_business` DocType + fixtures (`03a-maintained-apps.md` MA1) | **Confirmed** | |
| B2B portal → `create_process_file` | Frontend calls `visaguy_business.functions.api.create_process_file.create_process_file` (`03c-frontends.md` §4.5) | Backend `visaguy_business/functions/api/create_process_file.py` (`03a-maintained-apps.md` MA1) | **Confirmed** | |
| B2B portal → request payment | Frontend calls `visaguy_business.functions.api.create_process_file.request_payment_for_visa_order` (`03c-frontends.md` §4.5) | Backend returns `payment_url` (`03a-maintained-apps.md` MA3 W3) | **Confirmed** | Provider SDK not in frontend. |
| Consumer website → create visa order | Frontend `visaguy_website.api.create_visa_order` (`03c-frontends.md` §5.5) | Backend `visaguy_website/api/create_visa_order.py` (`03a-maintained-apps.md` MA1) | **Confirmed** | |
| Consumer website → submit application | Frontend `visaguy_website.api.submit_application` (`03c-frontends.md` §5.5) | Backend `visaguy_website/api/submit_application.py` (`03a-maintained-apps.md` MA1) | **Confirmed** | |
| Consumer website → `visaguy_business.create_process_file` | **No evidence** — frontend never imports or calls `visaguy_business` methods (`03c-frontends.md` §6) | `visaguy_business.create_process_file` exists (`03a-maintained-apps.md` MA1) | **Unresolved** | Separate interfaces only. |
| Consumer order → `PF Process File` / payment | Backend `processflo`/`payment_integrations` exist (`03a-maintained-apps.md` MA1) | Frontend only sees `payment_url` from `submit_application` (`03c-frontends.md` §5.5) | **Unresolved** | No proven order→process/payment join in the frontend source. |
| Consumer website → `fileflo.data_collection.add_form_data` | Frontend calls `fileflo.data_collection.add_form_data` (`03c-frontends.md` §5.5) | Backend `fileflo/data_collection.py:add_form_data` (`03a-maintained-apps.md` MA1) | **Confirmed** | Used in process-details form. |
| OTP login → API credentials | Frontend `otp_authentication.otp_generation.user_check_otp_send` / `otp_verification` (`03c-frontends.md` §5.5) | Backend `otp_authentication` issues API key/secret (`03a-maintained-apps.md` MA1) | **Confirmed** | Long-lived API credentials in browser storage. |
| B2B OAuth login → token/session | Frontend `frappe.integrations.oauth2.get_token` (`03c-frontends.md` §4.5) | Frappe OAuth provider (`03b-external-apps.md` EA2) | **Confirmed** | Tokens stored in `localStorage`. |

---

## IP3 — Integration Matrix

Legend:

- **Present** — settings DocType or capability surface exists in source.
- **Source-wired** — hooks, imports, or caller/callee relationships are evidenced in code.
- **Configured** — environment/config values observed only as key names; activation not verified unless explicitly stated.
- **Runtime-verified** — live traffic or provider call confirmed in this audit.  None are runtime-verified unless noted.

| Integration | Level | Evidence | Verification note |
|---|---|---|---|
| **OpenAI** | Source-wired | FastAPI `server/routers/voice.py:18`, `recommendations.py:12`, `server/utils/openai_client.py:17`; eligibility frontend receives ephemeral secret (`03c-frontends.md` §3.5) | Browser never sees API key; provider traffic not tested. |
| **Frappe REST / RPC** | Source-wired | All three frontends call `/api/resource/*` and `/api/method/*` (`03c-frontends.md` §3.5, §4.5, §5.5); maintained apps expose whitelisted methods (`03a-maintained-apps.md` MA5) | Guest writes and API-key auth both present. |
| **OAuth / OTP** | Source-wired | B2B: `frappe.integrations.oauth2.get_token` (`03c-frontends.md` §4.4); Consumer: `otp_authentication.otp_generation.user_check_otp_send` / `otp_verification` (`03c-frontends.md` §5.4) | OAuth/OTP gateway credentials and live send/verify not tested. |
| **WhatsApp** | Source-wired | `frappe_whatsapp` settings + doc_events; `waflo` flow processor/retry; `the_visaguy` lead/PF updates; eligibility/website wa.me deep-links (`01b-remote-bench.md` RB7, `03c-frontends.md` §3.6, §5.6) | Provider account and inbound message flow not tested. |
| **Raven** | Source-wired | Base `raven` installed; `visaguy_raven` doc_event handlers for CRM/HR/business/accounts (`03a-maintained-apps.md` MA1, MA3 W4/W5) | No whitelisted APIs listed; runtime delivery not tested. |
| **FCM push** | Present / Source-wired | `frappe_notifier_settings`; `frappe_notifier/api/token.py`, `topic.py`, `send_notification.py`; `employee_self_service` FCM keyword (`01b-remote-bench.md` RB7) | Service-account placement and relay URL not inspected. |
| **Meta / Google Conversions API** | Source-wired | `frappe_conversions_api/api/meta/webhook.py:webhook` (`03a-maintained-apps.md` MA1); keyword hits `meta`, `google` (`01b-remote-bench.md` RB7) | Provider tokens and event forwarding not tested. |
| **MyFatoorah / TotalPay** | Source-wired | `payment_integrations` settings DocTypes; webhook handlers (`totalpay_settings.py:handle_webhook`, `webhook/myfatoorah.py`); `Payment Request` `on_update_after_submit` hook (`03a-maintained-apps.md` MA1) | Gateway credentials and live webhooks not tested. |
| **Upstream Payments gateways** | Present | `payments` app settings: PayPal, Razorpay, PayTM, Braintree, GoCardless, Stripe, M-Pesa (`01b-remote-bench.md` RB7); checkout templates present (`03a-maintained-apps.md` MA5) | No evidence of active configuration. |
| **Zoho (legacy CRM)** | Source-wired | `visaguy_crm` server scripts reference Zoho integration and payment-from-lead flows (`03a-maintained-apps.md` MA1, MA3 W1) | No settings DocType observed. |
| **Twilio / Exotel** | Present / Source-wired | `crm_twilio_settings`, `crm_exotel_settings`; `crm/integrations/twilio/api.py`, `integrations/exotel/handler.py` (`01b-remote-bench.md` RB7, `03a-maintained-apps.md` MA1) | Provider credentials and call flows not tested. |
| **Insights** | Present / Source-wired | `insights_settings`; fixtures shipped by `visaguy_crm`, `visaguy_hrms`, `the_visaguy` (`01b-remote-bench.md` RB7, `03a-maintained-apps.md` MA1) | Data-source connectivity not tested. |
| **Backups (S3 / Dropbox)** | Present | `s3_backup_settings`, `dropbox_settings` in `frappe` (`01b-remote-bench.md` RB7) | Actual backup jobs and retention not inspected. |
| **GST / India Compliance** | Source-wired | `india_compliance` installed; `gst_settings`; overrides `Customize Form` and payment-entry method (`03b-external-apps.md` EA2) | Indian entity config and GST returns not verified. |

---

## IP4 — Customization / Precedence Matrix

| Domain | Base app | Custom layer(s) | Hook / override type | Migration / upgrade risk | Validation gate |
|---|---|---|---|---|---|
| **Frappe / ERPNext core** | `frappe`, `erpnext` | `visaguy_crm`, `visaguy_business`, `visaguy_hrms`, `payment_integrations`, `non_profit`, `india_compliance`, `frappe_whatsapp` | File-manager methods; `Address` class; `Web Form` class; `Payment Entry` class; `frappe.www.contact.send_message`; payment-entry outstanding-reference method (`01b-remote-bench.md` RB5, `03b-external-apps.md` EA4) | **High** — base classes/methods overridden by multiple apps; Frappe/ERPNext upgrades can silently change base signatures. | Run `bench migrate` in staging; execute wrapper test suites; verify payment, leave, invoice, and ticket flows after every base upgrade. |
| **CRM** | `crm` (maintained fork, branch `tridz-dev`) | `visaguy_crm` (legacy ERPNext Lead lifecycle), `visaguy_frappe_crm` (migration bridge) | `doc_events` on `CRM Lead`, `ToDo`; `permission_query_conditions`; fixtures for layouts/permissions; `erpnext_crm_settings.create_customer_in_erpnext` (`03a-maintained-apps.md` MA4) | **High** — three layers with overlapping lead/customer events; fork drift risk. | Duplicate-lead check, lead→deal conversion, ERPNext customer creation, legacy lead capture. |
| **Helpdesk** | `helpdesk` (maintained fork, branch `modification_develop_branch`) | `visaguy_helpdesk` | Class override of `HD Ticket`; `doc_events` on `HD Ticket`/`ToDo`; `permission_query_conditions` (`03a-maintained-apps.md` MA1, MA3 W5) | **Medium-High** — fork on non-standard branch; class override may break on upstream changes. | Ticket creation, agent assignment, reply/comment, permission scoping. |
| **HRMS** | `hrms` (version-15) | `visaguy_hrms` | Class overrides of `Interview`, `Expense Claim`, `Employee`; method override `hrms.api.get_leave_types`; `frappe.core.doctype.communication.email.make`; `doc_events` on leave/timesheet/appointment-letter flows (`03a-maintained-apps.md` MA1, MA3 W4) | **Medium-High** — only 2 tests for 69 .py files; class overrides fragile on HRMS patch. | Leave application, expense claim, interview reschedule, timesheet submission, appointment-letter file collection. |
| **Raven** | `raven` (branch `main`) | `visaguy_raven` | `doc_events` on Lead/CRM Lead/PF Process File/ToDo/Comment/Leave Application/Business Client Visa Order/Sales Order/Sales Invoice/Payment Entry; daily timesheet-reminder scheduler; fixtures (`03a-maintained-apps.md` MA1) | **Medium** — base branch not version-15; notification handlers have no whitelisted APIs. | Trigger notifications for each subscribed doctype; verify Raven channel delivery. |
| **Payments** | `payments` (upstream gateways) | `payment_integrations` (TotalPay/MyFatoorah) | `required_apps` `erpnext`/`payments`; `Payment Request` `on_update_after_submit`; webhook handlers; overrides in `payments` (`Web Form`) (`03a-maintained-apps.md` MA1, `03b-external-apps.md` EA2) | **Medium-High** — gateway webhooks depend on stable endpoint names and signatures; `non_profit` also overrides `Payment Entry`. | End-to-end payment request, redirect, webhook callback, invoice status update, refund path. |
| **FileFlo / ProcessFlo** | `fileflo`, `processflo` (both original) | `visaguy_crm`, `visaguy_business`, `visaguy_website` interact with them | `fileflo`: form generation, data collection, zip download; `processflo`: PF Process File actions/deliverables, web JS bundles (`03a-maintained-apps.md` MA1, MA3 W2/W3) | **Medium** — `processflo` has a dirty working tree; web bundles require `bench build`. | Generate file collection from B2B/consumer order, fetch actions, create deliverables, submit form data, download zip. |

---

## IP5 — Operational Runbooks

**Audit disclaimer:** every command in this section is documented from checked-in scripts, `Procfile`, `package.json`, and the accepted reports.  None were executed as part of this audit, and no production mutations were performed.  Run each runbook against a staging bench or with a verified backup first.

### RB-01 — Safe reconnaissance (read-only)

**Goal:** establish baseline state without changing code, data, or configuration.

**Preconditions:** SSH or shell access to the bench directory; user has read-only or operator privileges.

**Procedure:**

1. Change to the bench root (e.g., `/home/shahzad/bench`).
2. Record baseline:
   ```bash
   bench --version
   bench --site visaguy list-apps
   bench doctor --site visaguy
   ```
3. Inspect repository state per app:
   ```bash
   # inside each apps/<app>/ directory
   git status --short
   git log --oneline -5
   git rev-parse --abbrev-ref HEAD
   ```
4. Capture scheduler/worker health:
   ```bash
   sudo supervisorctl status   # only when Supervisor is the configured manager
   # or inspect the explicitly configured systemd units
   ```

**Checkpoint:** store the output in a dated runbook log before any further action.

---

### RB-02 — Local frontend setup / build / lint / test

#### `visa_eligibility_checker`

**Preconditions:** Bun installed; Python 3.10+ available for the companion backend.

**Procedure:**

```bash
# Frontend
cd /path/to/visa_eligibility_checker
bun install
cp .env.example .env   # set VITE_PUBLIC_ZONE, VITE_PUBLIC_API_URL,
                       # VITE_PUBLIC_FRAPPE_BASE_URL, VITE_PUBLIC_WHATSAPP_NUMBER
bun run lint
bun run build          # tsc -b && vite build → dist/
bun run preview        # serve dist/ locally
bun dev                # http://localhost:5173

# Companion backend
cd server
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env   # set OPENAI_API_KEY
uvicorn main:app --reload --port 8000
```

**Checkpoint:** `git status` must remain clean; build output is in `dist/` (gitignored).

#### `visaguy_business_client`

**Preconditions:** pnpm or Bun installed (Dockerfile uses pnpm; both lockfiles exist).

**Procedure:**

```bash
cd /path/to/visaguy_business_client
pnpm install          # or bun install; pick one and align lockfile

cp env.example .env.local
# NEXT_PUBLIC_API_BASE_URL
# NEXT_PUBLIC_CLIENT_ID, NEXT_PUBLIC_CLIENT_SECRET
# NEXT_PUBLIC_ZONE, NEXT_PUBLIC_CURRENCY
# NEXT_PUBLIC_CONTACT_URL
# NEXT_PUBLIC_INVOICE_PRINT_FORMAT, NEXT_PUBLIC_INVOICE_LETTERHEAD

pnpm dev              # http://localhost:3000
pnpm lint
pnpm build
pnpm start
```

**Checkpoint:** verify the hard-coded fallback URL at `app/orders/[id]/page.tsx:32` does not override the intended backend.

#### `visaguy-website-client`

**Preconditions:** Bun (or npm/pnpm/yarn) installed.

**Procedure:**

```bash
cd /path/to/visaguy-website-client
bun install
cp env.example .env.local   # set NEXT_PUBLIC_FRAPPE_BASE_URL
bun dev                     # Turbopack, http://localhost:3000
bun run lint
bun run build
bun run start
```

**Checkpoint:** confirm `next.config.ts` image hostnames match the chosen Frappe domain.

**Note:** no test scripts exist in any of the three repositories.

---

### RB-03 — Bench install / migrate / build

**Goal:** add or update an app on a site safely.

**Preconditions:** bench CLI available; target app repository accessible; dependencies installed (`erpnext`, `payments`, etc. as required).

**Backup checkpoint:** run `bench --site visaguy backup --with-files` before migrate.

**Procedure:**

```bash
# 1. Add app to bench (Bench derives the app name from the repository)
bench get-app --branch <branch> <remote-url>

# 2. Install on site
bench --site visaguy install-app <app-name>

# 3. Run migrations and patches
bench --site visaguy migrate

# 4. Rebuild assets (required when bundles change)
bench build
# or, for development
bench watch

# 5. Restart the configured process manager
bench restart --supervisor
# or, for a systemd-managed deployment
bench restart --systemd
```

**Upgrade-order recommendation** (from `03b-external-apps.md` EA5):

1. `frappe`
2. `erpnext`
3. `hrms` / `payments`
4. `india_compliance`
5. remaining apps
6. run wrapper tests between each step.

**Checkpoint:** site loads, login works, and a representative smoke test passes before declaring success.

---

### RB-04 — Scheduler / workers / background jobs

**Goal:** verify background processing is running and inspect scheduled jobs.

**Preconditions:** Frappe bench supervisor/systemd services configured.

**Procedure:**

```bash
# Inspect background workers and the configured process manager
bench doctor --site visaguy
sudo supervisorctl status   # Supervisor deployments only

# Inspect registered scheduler hooks (interactive and read-only when used exactly as shown)
bench --site visaguy console
# then in console:
# frappe.get_hooks("scheduler_events")
```

Do **not** run `bench schedule` or `bench worker` manually on production; those are foreground processes already managed by the configured service manager.

Key scheduled jobs evidenced (`01b-remote-bench.md` RB5, `03a-maintained-apps.md` MA6):

- `the_visaguy`: daily tmp-file clearing
- `frappe_notifier`: daily log cleanup
- `waflo`: cron every minute flow expiry, hourly retries
- `visaguy_raven`: daily timesheet reminders
- `helpdesk`: `all` search-index check
- `crm`: `after_migrate` settings
- `frappe_whatsapp`: frequent intervals

**Checkpoint:** confirm no failed/error jobs in the scheduler/error log before production release.

---

### RB-05 — Deployment / update sequence

**Goal:** roll out a bench update with rollback points.

**Preconditions:** staging validation passed; branch/commit hashes recorded; backup available.

**Procedure:**

1. **Pre-deploy checkpoint**
   - `bench --site visaguy backup --with-files`
   - Record `git rev-parse HEAD` for every app.
   - Record dirty apps: `insights`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`, `mansico_meta_integration`.
2. **Update apps** in dependency order (see RB-03).
3. **Migrate and build**
   ```bash
   bench --site visaguy migrate
   bench build
   bench restart --supervisor   # or --systemd, matching the deployment
   ```
4. **Frontend deploy** (business client example)
   ```bash
   docker compose down
   docker compose up -d --build
   ```
   (Jenkinsfile equivalent documented in `03c-frontends.md` §4.7.)
5. **Post-deploy validation** (see RB-07).

**Rollback:** restore the pre-deploy backup and revert app checkouts to recorded HEADs, then run `bench --site visaguy migrate`, `bench build`, and the deployment-appropriate `bench restart --supervisor` or `--systemd`.

---

### RB-06 — Backup / rollback preparation

**Goal:** ensure a recoverable backup exists before any change.

**Preconditions:** sufficient disk space; backup target configured.

**Procedure:**

```bash
# Frappe site backup (database + files)
bench --site visaguy backup --with-files
```

**Checkpoint:** record the generated database, public-file, private-file, and configuration backup paths; verify the artifacts are non-empty; then store them in an access-controlled off-site location. S3/Dropbox settings are present but actual backup jobs and retention were not verified.

**Rollback plan:**

1. Stop the configured bench services and preserve the failed state for investigation.
2. Revert each app to the recorded pre-change commit.
3. Restore the site using the exact generated artifacts:
   ```bash
   bench --site visaguy restore <database-backup.sql.gz> \
     --with-public-files <public-files-backup.tar> \
     --with-private-files <private-files-backup.tar>
   ```
4. Supply `--encryption-key` only when required by the backup; obtain it through the approved secret-management process and never place it in this workspace or shell history.
5. Run `bench --site visaguy migrate` only if required for the restored code/schema combination.
6. Run `bench build`, then `bench restart --supervisor` or `bench restart --systemd` to match the deployment.

---

### RB-07 — Validation gates

**Goal:** prove the site is functional after changes.

**Procedure:**

```bash
# 1. Unit tests per app
bench --site visaguy run-tests --app <app>

# 2. Frontend build / lint
# (run in each frontend repository)
bun run lint
bun run build

# 3. Smoke tests (manual or scripted)
# - eligibility checker: complete chat flow and verify Raw Lead created
# - B2B portal: login, create order, request payment
# - consumer portal: OTP login, create visa order, submit application
# - helpdesk: create and assign ticket
# - HRMS: submit leave / expense claim
# - Raven: trigger a notification
# - payments: complete a test transaction via gateway sandbox
```

**Checkpoint:** all gates pass on staging before touching production.

---

### RB-08 — Dirty-tree handling

**Goal:** reconcile uncommitted changes before any build or upgrade.

**Affected repositories:** `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`.

**Preconditions:** repository owner identified; changes are not production data or secrets.

**Procedure:**

```bash
cd apps/<app>
git status --short
git diff --stat        # do not copy diff contents into runbook log
git stash list

# Decision options (choose one, do not mix blindly):
# 1. Commit to a feature branch if changes are intentional.
# 2. Revert if changes are accidental.
# 3. Preserve in a named patch file for review.
```

**Policy:** do not deploy from a dirty working tree.  All five dirty trees predate this audit; their exact diffs were not inspected.

---

## IP6 — Security & Privacy Architecture

This section records **evidenced controls** and **recommended follow-up decisions**.  It does not claim unverified controls are implemented.

### Credentials and tokens

| Asset | Location / handling | Evidence | Recommended control |
|---|---|---|---|
| OpenAI API key | FastAPI backend env (`server/utils/openai_client.py:17`) | `03c-frontends.md` §3.6 | Keep server-side; rotate periodically. |
| OAuth access/refresh tokens | Browser `localStorage` (`accessToken`, `refreshToken`) | `03c-frontends.md` §4.4 | Move to `httpOnly` secure cookies; add token binding/rotation. |
| OAuth client ID/secret | Public env + login form (`lib/auth.ts:4-5`, `:27-29`) | `03c-frontends.md` §4.4 | Use PKCE or confidential backend proxy; avoid exposing client secret. |
| API key/secret (consumer portal) | Browser `localStorage` + `token {key}:{secret}` header | `03c-frontends.md` §5.4 | Replace with short-lived session cookies; enforce key rotation. |
| Frappe site secrets | `site_config.json` (not inspected) | `01b-remote-bench.md` RB1 | Restrict file permissions; do not commit. |

### CORS / guest access

- Eligibility checker sends unauthenticated `POST/PUT` to `/api/resource/Raw Lead` and `/api/resource/Lead` with only `Content-Type: application/json` (`03c-frontends.md` §3.4).
- FastAPI companion sets `allow_origins=["*"]` and `allow_credentials=True` (`03c-frontends.md` §8).

**Recommended follow-up:** restrict CORS to known origins; require a lightweight rate-limited token or captcha for public lead writes; validate Frappe DocType permissions for guest `Raw Lead`/`Lead` creation.

### PII / lead / application data

Data classes observed:

- Eligibility checker: full name, mobile number, destination, nationality, residency, employment, salary, bank statements, visa refusals (`03c-frontends.md` §3.3).
- Consumer portal: email, phone, travellers, travel dates, passport/identity documents, applicant files (`03c-frontends.md` §5.3).
- B2B portal: business details, applicant documents, invoices, payments (`03c-frontends.md` §4.3).

**Recommended follow-up:** document data-retention policy; encrypt uploads at rest; mask PII in logs; add consent capture for marketing use.

### Browser storage

- `localStorage`: OAuth tokens (B2B), API key/secret (consumer).
- `sessionStorage`: `lead_details` between lead form and application form (consumer); `businessDetails` for client-side admin gating (B2B).

**Recommended follow-up:** migrate auth credentials out of `localStorage`; do not rely on `sessionStorage` for authorization decisions.

### Provider secrets

Provider credentials for OpenAI, WhatsApp, Twilio/Exotel, FCM, Meta/Google, MyFatoorah/TotalPay, OTP gateway, S3/Dropbox are stored in settings DocTypes or environment variables.  This audit inspected only key names, not values.

**Recommended follow-up:** audit all settings DocTypes for populated secrets; store env secrets in a vault; rotate any long-lived keys.

### Uploads

- File uploads use Frappe `upload_file` (`03c-frontends.md` §4.5, §5.5).
- Documents are collected via `FF File Collection` and `fileflo.data_collection.add_form_data` (`03c-frontends.md` §5.5).

**Recommended follow-up:** restrict file types and sizes; scan uploads; ensure private files are not publicly accessible.

### Database / config / log exclusions

- Do not commit `site_config.json`, `.env`, `*.pem`, database dumps, or error logs to application repositories.
- Build outputs (`dist/`, `.next/`) are gitignored.

**Recommended follow-up:** add pre-commit hooks for secret scanning; centralize log shipping with PII redaction.

---

## IP7 — Consolidated Risks & Open Questions

Each item is labeled **statically verified** (source evidence exists) or **runtime-unverified** (no live traffic/activation confirmed).

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 1 | Five dirty working trees on the bench (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`) block reproducible builds. | Deployment | Statically verified |
| 2 | Non-standard / non-version-15 branches on `crm` (`tridz-dev`), `helpdesk` (`modification_develop_branch`), `fileflo` (`fix/mandatory-file`), `otp_authentication` (`email`), plus external `insights`/`raven`/`frappe_whatsapp`/`non_profit`/`mansico_meta_integration`. | Upgrade | Statically verified |
| 3 | Eligibility checker performs unauthenticated guest writes to `Raw Lead`/`Lead`. | Security | Statically verified |
| 4 | FastAPI CORS `allow_origins=["*"]` with credentials enabled. | Security | Statically verified |
| 5 | OAuth tokens and consumer API key/secret stored in browser `localStorage`. | Security | Statically verified |
| 6 | Business-client admin gating relies on client-side `sessionStorage` only. | Security | Statically verified |
| 7 | Consumer `ProcessDetailsForm` Save button simulates a delay and makes no API call. | Functionality | Statically verified |
| 8 | Consumer `/contact` is placeholder; `/careers` nav link has no route. | Functionality | Statically verified |
| 9 | No automated tests in any frontend; several maintained apps have minimal tests. | Quality | Statically verified |
| 10 | Business client disables ESLint and TypeScript errors during build. | Quality | Statically verified |
| 11 | Mixed lockfiles in business client (`bun.lock` + `pnpm-lock.yaml`). | Build | Statically verified |
| 12 | Hard-coded fallback API URL in `visaguy_business_client/app/orders/[id]/page.tsx:32`. | Configuration | Statically verified |
| 13 | Node v12 system runtime vs Node v18 socketio runtime split. | Infrastructure | Statically verified |
| 14 | Overlapping CRM layers (`crm`, `visaguy_crm`, `visaguy_frappe_crm`) — runtime precedence unclear. | Architecture | Runtime-unverified |
| 15 | Overlapping helpdesk layers (`helpdesk`, `visaguy_helpdesk`) — runtime precedence unclear. | Architecture | Runtime-unverified |
| 16 | Overlapping Raven layers (`raven`, `visaguy_raven`) — runtime precedence unclear. | Architecture | Runtime-unverified |
| 17 | Active payment gateway configuration (TotalPay / MyFatoorah / upstream gateways) not verified. | Integration | Runtime-unverified |
| 18 | Active WhatsApp / Twilio / Exotel / OTP / FCM provider traffic not verified. | Integration | Runtime-unverified |
| 19 | Active Meta / Google Conversions API event forwarding not verified. | Integration | Runtime-unverified |
| 20 | Backup jobs (S3 / Dropbox) and retention not verified. | Operations | Runtime-unverified |
| 21 | GST / India Compliance active configuration not verified. | Compliance | Runtime-unverified |
| 22 | Consumer website order → `PF Process File` / payment join is unresolved at the frontend source level. | Workflow | Runtime-unverified |
| 23 | `visaguy_website` does not invoke `visaguy_business.create_process_file` in the frontend evidence. | Workflow | Statically verified (absence) |

---

## Summary Metrics

| Metric | Value |
|---|---|
| Topology components mapped | 3 frontends + FastAPI/OpenAI + Frappe site + 18 maintained + 9 installed external + 2 bench-only + Redis/workers/scheduler + providers |
| Integration categories classified | 14 |
| Operational runbooks | 8 |
| Consolidated risks / open questions | 23 |
| Runtime-verified integrations | 0 |

**Verdict:** The cross-system topology, integration reconciliation, customization-precedence matrix, operational runbooks, security/privacy architecture, and consolidated risk register are complete against the accepted phase reports.  All integration claims are leveled consistently; no new files were created besides this report.
