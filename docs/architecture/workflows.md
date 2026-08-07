# Workflows — End-to-End Code Flows

This document traces how functionality is actually assembled across apps: entry point → hook → service → DocType → downstream effect.

It is the companion to [`frappe-apps.md`](frappe-apps.md), which is a per-app responsibility inventory. Where that document answers *"what does this app own"*, this one answers *"how does a feature actually work end to end"*.

## How to read this

- All anchors are `path/to/file.py:function` relative to the app root, as evidenced in source.
- Every workflow is **source-wired** unless stated otherwise: hooks, imports, and caller/callee relationships are evidenced in code. Live traffic and external-provider configuration are **not** verified. See the verification labels in [`../../AGENTS.md`](../../AGENTS.md).
- Line numbers from the original reconnaissance are retained where they were recorded, but they drift; treat the function name as the stable anchor.

## Workflow index

| # | Workflow | Primary apps | State |
|---|---|---|---|
| W1 | Public eligibility → lead capture → CRM → ERPNext customer | `the_visaguy`, `visaguy_frappe_crm`, `crm`, `erpnext` | live |
| W2 | Consumer visa order → documents → process file → payment | `visaguy_website`, `visaguy_business`, `processflo`, `fileflo`, `payment_integrations` | live |
| W3 | B2B portal → wallet / invoice / order | `visaguy_business`, `erpnext` | live |
| W4 | HR leave / timesheet / interview → approval → notification | `visaguy_hrms`, `hrms`, `visaguy_raven` | live |
| W5 | Support ticket → agent assignment → helpdesk | `helpdesk`, `visaguy_helpdesk`, `visaguy_raven` | live |
| W6 | Passport upload → extraction → visa tracking → public lookup | `fileflo`, `passport_extractor`, `the_visaguy` | **unmerged** |
| W7 | Payment request → gateway → webhook → settlement | `payment_integrations`, `payments`, `erpnext` | live |
| W8 | Consumer OTP login → API credentials | `otp_authentication` | live |
| W9 | Inbound WhatsApp → conversational flow → retry | `frappe_whatsapp`, `waflo`, `the_visaguy` | live |

---

## W1 — Public eligibility / lead capture → CRM → ERPNext customer

1. The public form writes a `Raw Lead` via `the_visaguy/tvg_crm/doctype/raw_lead/raw_lead.py:convert_to_crm_lead`, or a `CRM Lead` is created via `visaguy_frappe_crm/functions/apis/check_duplicate_lead.py:check_duplicate_lead`.
2. `visaguy_frappe_crm` hooks fire on `CRM Lead`:
   - `before_insert` → `add_zone`, `customer_creation`
   - `before_save` → `update_number_of_applicants`, `update_department`
   - `validate` → `crm_lead_validations`, `validate_payment_confirmed`
3. Core `crm` serves the lead through `crm_lead/api.py:get_lead` and list views via `api/views.py:get_views`.
4. Sales converts `CRM Lead` → `CRM Deal` via `crm/.../crm_lead.py:convert_to_deal`.
5. `CRM Deal.on_update` triggers `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.py:create_customer_in_erpnext`, creating an ERPNext `Customer`.
6. Side effects: `the_visaguy/handlers/whatsapp_message.py:send_lead_updates` sends WhatsApp lead updates; `visaguy_raven` sends CRM form-submission notifications.

**Precedence note.** Three CRM layers touch this flow — `crm` (fork), `visaguy_crm` (legacy), `visaguy_frappe_crm` (migration bridge). Runtime precedence between them is an open question; see [`../risks-and-open-questions.md`](../risks-and-open-questions.md) #14.

---

## W2 — Consumer visa order → document collection → process file → payment → communications

1. The consumer portal calls `visaguy_website/api/create_visa_order.py:create_visa_order`, then `api/submit_application.py:submit_application`.
2. `visaguy_business/functions/api/create_process_file.py:create_process_file` and `request_payment_for_visa_order` create a `PF Process File` and a payment request.
3. `processflo/processflo/doctype/pf_process_file/pf_process_file.py:fetch_actions` and `:create_process_deliverables` drive the workflow; `processflo/generate_file_collection.py:generate_file_collection_process_file` links documents to the case.
4. `fileflo/form_generation.py:generate_form` and `fileflo/data_collection.py:add_form_data` produce an `FF File Collection` for applicant uploads.
5. Payment settles through W7.
6. `visaguy_business` `doc_events` update the wallet on `Payment Entry` submit and mark completion on `PF Process File` / `FF File Collection` updates.
7. Communications: `waflo` processes inbound WhatsApp (W9); `the_visaguy/handlers/whatsapp_message.py:send_process_file_updates` sends status messages; `visaguy_raven` notifies on `PF Process File` / `ToDo` / `Comment` changes.

**Unresolved join.** The consumer frontend is not evidenced calling `visaguy_business.create_process_file`; it only observes a returned `payment_url`. Do not claim that join — see [`../risks-and-open-questions.md`](../risks-and-open-questions.md) #22 and #23.

---

## W3 — B2B business portal → wallet / invoice / order

1. The business portal calls `visaguy_business/functions/api/`: `get_business_details`, `get_invoice_items`, `get_visa_price`, `generate_preliminary_documents`, `create_process_file`, `request_payment_for_visa_order`.
2. `visaguy_business/hooks.py` fixtures provision Business Client roles, a price list, a customer group, and the `Wallet Advance - T` account.
3. `permission_query_conditions` restrict `Business Client Visa Order` and `Sales Invoice`; `has_permission` on `Sales Invoice` enforces B2B access scoping.
4. `Payment Entry.on_submit` updates the business wallet; `Sales Invoice.on_submit` updates the `Business Client Visa Order`.

**Security note.** Business-client admin gating is enforced client-side only in the portal (`sessionStorage`); the server-side scoping above is the real control. See [`../risks-and-open-questions.md`](../risks-and-open-questions.md) #6.

---

## W4 — HR leave / timesheet / interview → approval → notifications

1. `visaguy_hrms` overrides the `Interview`, `Expense Claim`, and `Employee` classes, and the `hrms.api.get_leave_types` method.
2. `doc_events` enforce interview emails, timesheet restrictions, leave-balance validation, maternity checks, and appointment-letter file sync.
3. Fixtures ship the `Leave Approval` and `Overtime Approval` workflows.
4. `visaguy_raven` sends leave-request notifications on `Leave Application` insert/update, plus a daily timesheet reminder from its scheduler.
5. Optional push layer: `frappe_notifier` (via `notification_relay` overrides) and `employee_self_service` FCM hooks — note `employee_self_service` is bench-only and **not installed** on site `visaguy`.

**Quality note.** `visaguy_hrms` carries only 2 tests across 69 Python files while overriding three core classes. This is the highest-risk wrapper during an HRMS upgrade.

---

## W5 — Support ticket → agent assignment → helpdesk

1. Customers and agents use the `/helpdesk` route, registered via `helpdesk/hooks.py` `website_route_rules`.
2. `helpdesk` provides `HD Ticket`, `HD Agent`, `HD Team`, and ticket APIs: `hd_ticket/api.py:new`, `:get_one`, `hd_ticket.py:assign_agent`, `:reply_via_agent`.
3. `visaguy_helpdesk` overrides the `HD Ticket` class via `server_scripts/hd_ticket_class_override.py` and sets agent groups through `doc_events`.
4. `visaguy_helpdesk` adds `permission_query_conditions` on `HD Ticket`.
5. `visaguy_raven` sends `ToDo` assignment and `Comment` notifications.

**Fragility note.** The `HD Ticket` class override sits on a fork (`modification_develop_branch`) of an upstream app. Any helpdesk upgrade must re-validate it.

---

## W6 — Passport upload → extraction → visa tracking → public lookup

**State: implemented on `feat/visa-tracker` branches, pushed upstream, not merged, and NOT active on site `visaguy`** — the bench has `the_visaguy` checked out on `main`. See [FEAT-001](../../features/ongoing/visa-tracking/README.md).

This flow is deliberately split so that no generic app learns about VisaGuy, and no expensive work runs in a web request.

### Stage 1 — synchronous, in-request (must stay trivial)

1. An applicant submits a passport through a FileFlo form. `fileflo/data_collection.py:add_form_data` persists the field and file, carrying a stable `field_id` on rows created by both the single- and multi-upload paths.
2. `fileflo/events.py:dispatch_after_commit_extension_event` reads the `fileflo_extension_handlers` hook list and, for each handler, calls `frappe.enqueue(handler, queue="short", enqueue_after_commit=True)`.

   FileFlo does no business logic here and knows none of its consumers. It ships the hook list empty. See [ADR-003](../../decisions/ADR-003-fileflo-consumer-agnostic-extension-point.md).

3. `the_visaguy/hooks.py` subscribes:

   ```
   fileflo_extension_handlers = [
       "the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection",
   ]
   ```

   Nothing else happens in the request. The transaction commits and the user gets their response.

### Stage 2 — short queue: is this even a passport?

`the_visaguy/visa_tracking/services/fileflo_inspection_service.py`:

1. Reload the persisted FileFlo record.
2. Load cached `Visa Tracker Settings` via `visa_tracking/utils/settings.py`.
3. Stop if the feature is disabled.
4. Compare the persisted `field_id` against the exact field IDs configured in settings — one per line, no wildcards in this release.
5. Validate the value is a supported private file.
6. Compute an idempotency key via `visa_tracking/utils/idempotency.py` so a resubmission does not duplicate work.
7. Create the `Passport Extraction` record (owned by `passport_extractor`).
8. Enqueue the long OCR job after commit, via `visa_tracking/services/extraction_orchestrator.py`.

Even the cheap field-ID comparison happens here rather than in the request — a deliberate constraint from ADR-003.

### Stage 3 — long queue: extraction (`passport_extractor`, domain-free)

`passport_extractor/services/extraction_service.py`, driven by `passport_extractor/jobs.py`:

1. Mark the record Processing.
2. Resolve the private file safely.
3. `ocr/pdf_renderer.py` renders PDF pages to images where needed.
4. `ocr/image_preprocessor.py` handles orientation (canvas-expanding rotation), cropping, and preprocessing, retaining raw-image candidates.
5. `ocr/paddle_ocr_engine.py` runs PaddleOCR locally. **No passport file or passport data leaves the bench** — no external OCR service, no LLM. See [ADR-004](../../decisions/ADR-004-passport-extraction-as-standalone-reusable-app.md).
6. `ocr/mrz_parser.py` detects TD3 MRZ candidates, parses values, and validates check digits.
7. Store the raw result and reviewed-value candidates.
8. Classify as **Extracted**, **Needs Review**, or **Failed**. Raw passport details are never logged. Retries are bounded and auditable.

`passport_extractor` imports nothing from `fileflo`, `processflo`, `Lead`, `Customer`, or `Visa Tracking Application`. It does not know VisaGuy exists.

### Stage 4 — domain linking and tracking lifecycle (`the_visaguy`)

`doc_events` in `the_visaguy/hooks.py` drive this stage:

| Event | Handler |
|---|---|
| `Passport Extraction.on_update` | `visa_tracking/handlers/passport_extraction_handlers.py:on_update` |
| `Customer.after_insert`, `Customer.on_update` | `visa_tracking/handlers/lead_handlers.py:on_customer_save` |
| `PF Process File.on_update` | `visa_tracking/handlers/process_file_handlers.py:on_update` |

1. On a **verified** extraction, `visa_tracking/services/lifecycle_service.py` links it to `Lead` / `Customer` (`custom_passport_extraction` holds the current preferred verified extraction, not the history) and creates a `Visa Tracking Application`.
2. Initial status is read from `Visa Tracker Settings` — never a hardcoded label.
3. When a `PF Process File` is created or linked, its tracking Link is populated and the configured created-status is applied.
4. Operations then drive status day-to-day from `PF Process File.custom_client_status`.
5. Exceptional direct corrections on `Visa Tracking Application` synchronise back to the Process File **without recursion** — every status write routes through `visa_tracking/services/status_service.py`, which writes exactly one `Visa Tracking Status Log` row per *effective* change. Re-saving the same status writes no row.
6. `visa_tracking/services/reconciliation_service.py` repairs missed FileFlo events and mismatched statuses.
7. `visa_tracking/services/audit_service.py` writes to `Visa Tracker Audit Log`.

Statuses are `Visa Tracking Status` **records**, not Select options — code branches on stable codes and flags (`final`, `success`, `allow_on_process_file`), never on labels.

### Stage 5 — public lookup

1. The `visa_tracker` SPA (**not built yet** — TASK-008/009) posts passport number and date of birth to `the_visaguy/visa_tracking/api/verification.py`.
2. `visa_tracking/services/lookup_service.py` performs an HMAC-based lookup; `visa_tracking/utils/security.py` holds the primitives.
3. `visa_tracking/services/rate_limit_service.py` applies rate limiting and temporary lockout. Every failure mode returns **one generic response** — wrong passport, wrong DOB, no record, and locked-out are indistinguishable.
4. On success, `visa_tracking/services/session_service.py` issues a short-lived **opaque** Redis-backed token that encodes nothing.
5. `visa_tracking/api/status.py` + `services/response_service.py` return only the approved public fields: masked name, masked passport number, destination and visa type when approved, current status, configured message, last-updated timestamp, timeline, and a generic support link.

The full exclusion list and rationale are in [ADR-005](../../decisions/ADR-005-visa-tracker-public-exposure-boundary.md).

### Open items on W6

1. **Auto-verification.** `the_visaguy` `8254f93` auto-verifies extractions. FEAT-001 excludes automatic use of unverified data. The promotion criteria must be reviewed in TASK-010 before this is sanctioned.
2. **OCR is not runtime-verified.** No live PaddleOCR run has been recorded on the bench, and model-file availability to production workers is unconfirmed.

---

## W7 — Payment request → gateway → webhook → settlement

1. A payment request originates from W2 (`visaguy_business/functions/api/...:request_payment_for_visa_order`) or from legacy `visaguy_crm` flows.
2. `payment_integrations/integrations.py:on_update_after_submit` is wired to `Payment Request.on_update_after_submit`.
3. The client is redirected to the gateway. Custom gateways: TotalPay and MyFatoorah. Upstream `payments` additionally ships checkout for Stripe, Razorpay, PayPal, PayTM, Braintree, GoCardless, and M-Pesa (`payments/templates/pages/stripe_checkout.py:make_payment` and siblings) — **no evidence any upstream gateway is actively configured**.
4. The gateway calls back:
   - `payment_integrations/.../totalpay_settings/totalpay_settings.py:handle_webhook`
   - `payment_integrations/webhook/myfatoorah.py:handle_webhook`
5. Settlement flows into ERPNext `Payment Entry` / `Sales Invoice`, which in turn fire the W3 wallet and order updates.
6. `non_profit` also overrides `Payment Entry`, and `india_compliance` overrides `get_outstanding_reference_documents` — both sit in this path and must be re-validated on any payments upgrade.

**Verification.** Gateway credentials and live webhooks are **not** tested. Webhook endpoints and signatures are the fragile surface during any upgrade.

---

## W8 — Consumer OTP login → API credentials

1. The consumer website requests an OTP via `otp_authentication/otp_generation.py:user_check_otp_send`.
2. The user submits the code to `otp_authentication/otp_verification.py:otp_verification`.
3. On success, `otp_authentication:generate_api_credentials` issues an API key/secret pair.
4. The consumer client stores the key and secret in browser `localStorage` and uses them for subsequent Frappe REST calls.

**Security note.** Long-lived API credentials in `localStorage` is a standing risk — see [`../risks-and-open-questions.md`](../risks-and-open-questions.md) #5. Contrast with W6, which deliberately uses a short-lived opaque token instead.

---

## W9 — WhatsApp: inbound flows and outbound event messaging

Two distinct paths share one send function. Traced in detail 2026-08-06.

> **`waflo` is not primarily a flow engine today.** Despite its name and module layout, its live role is a send helper for template features `frappe_whatsapp` lacks — dynamic URL buttons, FLOW buttons, caller-supplied header and body params — plus rate limiting and retry. See [ADR-009](../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md). The conversational flow engine described in W9a steps 4–5 has **never been tested and is switched off** (`WF Settings.enable_flow_engine = 0`); it is planned as [FEAT-004](../../features/planned/whatsapp-flow-engine/README.md).

### W9a — Inbound: provider webhook → conversational flow

1. `frappe_whatsapp/utils/webhook.py` receives provider callbacks and creates `WhatsApp Message` records. The inbound account is resolved by `phone_id` via `frappe_whatsapp/utils/__init__.py:get_whatsapp_account` — **inbound multi-account already works**.
2. `waflo` `doc_events` on `WhatsApp Message` route into `waflo/flow/processor.py:process_incoming_whatsapp_message`, which enqueues `_process_incoming_whatsapp_message`.
3. That worker checks `rate_limiting.py:is_rate_limited(account, mobile_no)`. If limited, it sets `custom_rate_limited` on the message and returns.
4. If `WF Settings.enable_flow_engine` is off, it falls through to `send_default_message(doc)` using `WF Account Settings.default_template`.
5. Otherwise `process_whatsapp_message` either starts the default `WF Message Flow` or advances the existing `WF Active Chat Flow` via `flow/triggers.py:match_step` and `flow/actions.py:eval_template_params`.
6. Schedulers run flow expiry on a per-minute cron and retries hourly; `waflo/messaging/retry_message.py:retry_message` is the manual retry API.
7. `the_visaguy/handlers/receive_feedback.py:receive_feedback` captures quality feedback replies.

### W9b — Outbound: business event → auto message / feedback

1. `doc_events` in `the_visaguy/hooks.py` fire `handlers/whatsapp_message.py:send_lead_updates` (Lead, CRM Lead) and `:send_process_file_updates` (PF Process File).
2. Each checks `doc.has_value_changed(...)` on a trigger field — `custom_file_request_link_sent`, `custom_process_file_created`, `custom_payment_received`, or `workflow_state` — and enqueues a private `_send_*` worker with `enqueue_after_commit=True`.
3. The worker calls `whatsapp_default.is_enabled(company, customer)` — the parameter is named `company` but every caller passes `doc.custom_zone`, a **Zone**. It checks the `Whatsapp Default.enabled` flag and the customer's `custom_enable_whatsapp_notifications` preference.
4. It loads `Whatsapp Default` for that zone and picks the template for the event from the `event_template` child table, plus a header image from `feedback_defaults` for feedback events.
5. It calls `waflo/messaging/send.py:send_whatsapp_template`, which builds the Meta payload and posts to `{account.url}/{version}/{phone_id}/messages`, then logs via `messaging/logs.py:log_whatsapp_message`.

Event types today: Lead Form, Process Form, Payment Success, Visa Completion (auto) and Payment Feedback, Completion Feedback (feedback, sent with `use_flow=True`).

### Known defects in this workflow

This path has open defects, planned in [FEAT-002](../../features/ongoing/multi-zone-whatsapp/README.md) and [FEAT-003](../../features/ongoing/waflo-correctness/README.md). Read those before changing anything here.

**The defects below describe the currently deployed system.** FEAT-003 fixes most of them on branch `feat/waflo-correctness` @ `56899f2` (20/20 tests pass), but that branch is **not merged and not deployed** — so this section stays as written until [TASK-017](../../tasks/blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md) records both deployment gates. The FEAT-002 items (account routing, Zone keying, unconfigured event types) are not addressed by that branch at all.

When FEAT-003 deploys, W9b gains two behaviours worth knowing now: outbound transactional sends become rate limited, and a limited send is deferred to the hourly `schedule_retry_message` rather than sent immediately — never dropped, but potentially up to an hour late.

- **`send.py:29` always resolves the global default outgoing account.** `send_whatsapp_template` takes no account parameter, so every outbound message leaves from one number regardless of company. This is the multi-company blocker.
- **`processor.py:61` raises `NameError`** (`doc` not in scope), which is swallowed by a broad `except`. `create_active_flow` on the next line never runs, so new conversations get no `WF Active Chat Flow` record and the initial step can be re-sent on every subsequent inbound message. Dormant while the flow engine is off — a blocker for FEAT-004, not a live bug.
- **The rate limiter never increments on flow paths**, so it would be inert if the flow engine were enabled. With the engine off, the default-reply path does increment correctly. W9b is not rate limited at all — that one is live.
- **Configuration lookup keys a Zone name into a Company field** (`{"company": doc.custom_zone}`), resolving only because the names currently coincide. The callers are right — WhatsApp is customer-facing and therefore Zone-scoped — and the field is wrong. See [ADR-006](../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) and [ADR-007](../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md).
- **Unconfigured event types raise `IndexError`** at six `[...][0]` call sites.

`frappe_whatsapp` also registers a broad `*` server-script runner in `doc_events` — a wide surface worth auditing before upgrades.

**Note.** FEAT-001 explicitly excludes WhatsApp conversational status retrieval. WhatsApp will only deep-link to the public tracker.

---

## Source evidence

W1–W5 and the interface anchors were established during the 2026-07 reconnaissance and are recorded in `archive/visaguy-workspace-initialization/03a-maintained-apps.md` (§3 workflows, §4 interface tables) and `03d-integrations-procedures.md`. W6 was traced directly from the `feat/visa-tracker` branches on the remote bench on 2026-08-06. W7–W9 were assembled from the reconnaissance interface tables.
