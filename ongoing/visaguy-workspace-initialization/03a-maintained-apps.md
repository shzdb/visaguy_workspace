# MA1–MA7 — Maintained Frappe Apps Synthesis

**Scope:** the 18 internally maintained Frappe apps installed on site `visaguy`.  
**Evidence accepted:** `maintained_raw.json`, `01b-remote-bench.md`, `02-triage.md`, `prompts/03a-maintained-apps.txt`.  
**Cautions applied:** `maintained_raw.json` is a shallow static extraction — its empty `doctypes` arrays do **not** prove a DocType is absent. Domain entities below are inferred from source paths, fixtures, settings DocTypes listed in `01b-remote-bench.md`, and hook references. No secrets, production data, raw logs, or dirty diffs are reproduced.

---

## 1. Maintained app catalog (MA1 + MA2)

| # | App | Classification | Primary responsibility | Key actors / entities | Representative public interfaces | Key hooks / overrides / fixtures | Branch | Dirty | Tests | Verification |
|---|-----|----------------|------------------------|----------------------|----------------------------------|----------------------------------|--------|-------|-------|--------------|
| 1 | `crm` | maintained fork of Frappe CRM | Modern CRM UI, lead/deal pipeline, call/WhatsApp/ERPNext integration | Sales users, consultants, agents; CRM Lead, CRM Deal, CRM Organization, Contact, Address, CRM Call Log, CRM View Settings, FCRM/ERPNext-CRM/Twilio/Exotel settings | `crm/fcrm/doctype/crm_lead/api.py:get_lead:8`, `crm_lead.py:convert_to_deal:404`, `crm_deal/api.py:get_deal:8`, `crm_deal.py:create_deal:309`, `api/views.py:get_views:6`, `api/contact.py`, `api/whatsapp.py`, `integrations/twilio/api.py`, `integrations/exotel/handler.py`, `erpnext_crm_settings.py` | `website_route_rules` `/crm`, `before_install`, `after_install`, `before_uninstall`, `after_migrate`, `doc_events` on Contact/ToDo/Comment/WhatsApp Message/CRM Deal/User | `tridz-dev` | no | 26 | source-wired; settings surface present; runtime activation unverified |
| 2 | `fileflo` | original | Document forms, file collection, data collection, zip downloads | Applicants, back-office; Fileflo Settings, form templates, FF File Collection (referenced by other apps) | `fileflo/settings.py:get_settings:5`, `fileflo/form_generation.py:generate_form:5`, `fileflo/document_fetch.py:document_fetch:9`, `fileflo/data_collection.py:fetch_form_data:6`, `add_form_data:138`, `fileflo/download_file.py:download_files_as_zip:10` | `app_include_js`, `website_route_rules` `/form` | `fix/mandatory-file` | no | 4 | source-wired |
| 3 | `frappe_conversions_api` | integration app | Meta/Google Conversions API event forwarding | Marketing/tracking; Conversion Account/Event (inferred) | `frappe_conversions_api/api/meta/webhook.py:webhook:5` | `after_install` | `develop` | no | 3 | source-wired; provider credentials runtime unverified |
| 4 | `frappe_notifier` | integration app | FCM push notifications via Frappe Relay | Mobile users; FN Notification Log, Frappe Notifier Settings | `frappe_notifier/api/token.py:add:7/remove:23`, `api/topic.py:add:8/remove:22/subscribe:49/unsubscribe:72`, `api/send_notification.py:topic:197/user:267`, `api/get_config.py:get_config:7` | `after_install` `setup_users`, `scheduler_events` daily `clear_old_logs`, fixtures Role/Custom DocPerm | `develop` | no | 4 | source-wired; FCM/Relay runtime unverified |
| 5 | `helpdesk` | maintained fork of Frappe Helpdesk | Customer support tickets, KB, agent portal | Customers, agents, support leads; HD Ticket, HD Agent, HD Team, HD Article, HD Ticket Template, HD Settings | `helpdesk/api/ticket.py:bulk_assign_ticket_to_agent:22`, `hd_ticket/hd_ticket.py:assign_agent:345`, `reply_via_agent:460`, `new_comment:447`, `hd_ticket/api.py:new:13/get_one:37`, `api/article.py:search:4`, `api/dashboard.py:get_all:9` | `before_install`, `after_install`, `after_migrate` `build_index_in_background`, `scheduler_events` `all`, `website_route_rules` `/helpdesk`, `doc_events` Contact/Assignment Rule, `has_permission` HD Ticket | `modification_develop_branch` | no | 26 | source-wired |
| 6 | `otp_authentication` | integration/custom app | OTP generation/verification and API credential issuance for consumer portal | Consumer portal users; OTP Settings | `otp_authentication/otp_verification.py:otp_verification:10`, `generate_api_credentials:86`, `check_customer_verification:128`, `otp_generation.py:get_auth_config:11`, `otp_creation_and_storing:22`, `user_check_otp_send:56`, `www/customer-details/index.py:update_customer_details:6` | — | `email` | no | 1 | source-wired; OTP gateway runtime unverified |
| 7 | `payment_integrations` | integration/custom app | Custom payment gateways (TotalPay, MyFatoorah) | Payers, finance; TotalPay Settings, MyFatoorah Settings | `payment_integrations/.../totalpay_settings.py:handle_webhook:169`, `payment_success:257`, `payment_cancel:267`, `identify_site:275`, `webhook/myfatoorah.py:handle_webhook:6`, `payment_gateways/totalpay.py:handle_webhook:40` | `required_apps` `erpnext`, `payments`; `after_install`; `doc_events` Payment Request `on_update_after_submit` → `payment_integrations.integrations.on_update_after_submit` | `develop` | no | 3 | source-wired; gateway credentials/runtime unverified |
| 8 | `processflo` | original | Process workflow engine and deliverables for visa cases | Operations; PF Process File, PF Process Action, PF Process Deliverables | `processflo/generate_file_collection.py:generate_file_collection_process_file:72`, `processflo/doctype/pf_process_file/pf_process_file.py:fetch_actions:63`, `create_process_deliverables:43` | `web_include_js` `/assets/processflo/js/fetch_action.js`, `create_file_collection.js` | `develop` | **yes** | 4 | source-wired; dirty tree diffs not inspected |
| 9 | `quick_kanban` | original | Enhanced Vue-based Kanban view | Desk users; Kanban Board Highlight (inferred) | `quick_kanban/get_beta _users.py:get_kanban_config:5` | `app_include_css` `quick_kanban.bundle.css`, `app_include_js` `kanban_view.bundle.js` | `main` | no | 0 | source-wired; no tests |
| 10 | `the_visaguy` | original domain app | Core Visa Guy domain: raw leads, destinations, WhatsApp feedback, quality feedback | Public applicants, customers, ops; Raw Lead, Destination Configuration, Quality Feedback, WhatsApp Default/Templates | `the_visaguy/tvg_crm/doctype/raw_lead/raw_lead.py:convert_to_crm_lead:20`, `tvg_core/doctype/destination_configuration/destination_configuration.py:get_visa_types:26`, `tvg_business/api/get_invoice_items.py:get_invoice_items:7`, `get_visa_price.py:get_visa_price:5` | `on_session_creation`, `doc_events` WhatsApp Message/Lead/CRM Lead/PF Process File/Quality Feedback, `scheduler_events` daily `tmp_file_clearing`, fixtures Custom Field/Workspace/Custom HTML Block/Insights Query/Chart | `main` | no | 7 | source-wired |
| 11 | `visaguy_business` | integration/custom app | B2B portal ordering, wallet, business client visa orders, invoices | Business clients, managers, consultants; Business Client Settings, Business Client Visa Order | `visaguy_business/functions/api/generate_preliminary_documents.py:generate_preliminary_documents:8`, `get_applicant_files.py:5`, `get_invoice_items.py:7`, `get_business_details.py:4`, `get_visa_price.py:6`, `create_process_file.py:create_process_file:13`, `request_payment_for_visa_order:241` | `has_permission` Sales Invoice; `doc_events` Payment Entry/PF Process File/FF File Collection/Sales Invoice; fixtures Account/Price List/Customer Group/Roles/Custom Fields/Property Setter | `develop` | no | 5 | source-wired |
| 12 | `visaguy_crm` | integration/custom app (legacy CRM layer) | Legacy operational CRM around ERPNext Lead, process files, payments, Zoho integration, lead allocation | Sales/ops/consultants; Lead (ERPNext), Customer, ToDo, FF File Collection, PF Process File, Sales/Invoice/Payment docs | `visaguy_crm/customer_creation.py:enque_create_customer:168`, `create_customer_id_existing_lead:200`, `lead_functions.py`, `file_collection_from_lead.py:generate_file_collection_lead:9`, `allocated_to_process_file.py:create_process_file:49`, `data_collecting_form.py`, `api/update_applicant_details.py:update_applicant_details:6`, `server_scripts/payment_from_lead/*`, `server_scripts/rpa/generate_application_form.py:generate_application_form:47` | `has_permission` Lead; `permission_query_conditions` Lead/PF Process File/Sales Order; extensive `doc_events` on Lead/Customer/ToDo/FF/PF/Sales Invoice/Payment Entry/Sales Order/Payment Request/Journal Entry/User/Notification Settings; fixtures workflows/roles/insights; overrides Payment Request class and `fileflo.*` methods; `app_include_js` `visaguy_crm.bundle.js` | `main` | no | 17 | source-wired |
| 13 | `visaguy_frappe_crm` | integration/custom app (Frappe CRM wrapper) | Customize and migrate to Frappe CRM; zone, customer, validations, duplicate checks | Sales/ops; CRM Lead, ToDo (via `crm`), CRM Migration Settings | `visaguy_frappe_crm/functions/lead_file_collection.py:handle_lead_send_form:12`, `functions/session_user.py:get_details_of_session_user:3`, `functions/apis/get_zone_details.py:get_zone_details:5`, `functions/apis/check_duplicate_lead.py:check_duplicate_lead:4` | `doc_events` CRM Lead before_insert/before_save/validate, ToDo before_save; `permission_query_conditions` CRM Lead/Department; fixtures CRM Fields Layout/Global Settings/Property Setter/Custom DocPerm | `develop` | **yes** | 1 | source-wired; dirty tree diffs not inspected |
| 14 | `visaguy_helpdesk` | integration/custom app | Customization layer over Frappe Helpdesk; agent group assignment, ticket override, permissions | Support agents; HD Ticket (from `helpdesk`) | `visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:assign_agent:419`, `get_last_communication:473`, `new_comment:524`, `reply_via_agent:541`, `create_communication_via_contact:677`, `mark_seen:803` | overrides `HD Ticket` class; `doc_events` ToDo/HD Ticket; `permission_query_conditions` HD Ticket; fixtures Role | `develop` | no | 1 | source-wired |
| 15 | `visaguy_hrms` | integration/custom app | HRMS customizations: leave, timesheet, interviews, appointment letters, expense claims | Employees, HR, managers; Interview, Expense Claim, Employee, Leave Application, Leave Allocation, Appointment Letter | `visaguy_hrms/api/get_leave_types.py:get_leave_types:5`, `custom_scripts/expense_claim_doctype_class_override.py`, `interview_doctype_class_override.py`, `appointment_letter_server_scripts.py:generate_file_collection_for_appointment_letter:11`, `email_send_override.py:make_override:26` | overrides classes Interview/Expense Claim/Employee and methods `hrms.api.get_leave_types`, `frappe.core.doctype.communication.email.make`; `doc_events` Interview/Timesheet/Leave Application/Leave Allocation/Appointment Letter/FF File Collection; `permission_query_conditions` Appraisal/Leave Application/Timesheet; `has_permission` Notification Settings; fixtures workflows/notifications/templates/roles/etc. | `main` | no | 2 | source-wired |
| 16 | `visaguy_raven` | integration/custom app | Raven notification orchestration for CRM, HR, business, accounts events | CRM/HR/accounts teams; Raven Bot/User/Document Notification | internal `doc_event` handlers: `functions/send_form_submission`, `send_assignment`, `send_comment`, `send_leave_request`, `send_business`, `send_sales_order`, `send_credit_note`, `send_refund`, `send_timesheet_reminders` | `doc_events` Lead/CRM Lead/PF Process File/ToDo/Comment/Leave Application/Business Client Visa Order/Sales Order/Sales Invoice/Payment Entry; `scheduler_events` daily timesheet reminders; fixtures Raven Bot/User/Document Notification | `develop` | **yes** | 1 | source-wired; dirty tree diffs not inspected |
| 17 | `visaguy_website` | integration/custom app | Consumer/e-commerce Next.js website backend: visa orders, destinations, applications, file status | Consumers; Visaguy Website Visa Order, Destination (custom fields) | `visaguy_website/api/create_visa_order.py:create_visa_order:12`, `api/submit_application.py:submit_application:15`, `api/get_destination_items.py:get_destination_items:11`, `api/get_file_template.py:get_file_template:11`, `api/get_applicant_files.py:get_applicant_files:5` | `doc_events` FF File Collection/PF Process File; `permission_query_conditions` Visaguy Website Visa Order; fixtures Custom Field/Role | `develop` | no | 7 | source-wired |
| 18 | `waflo` | original | WhatsApp conversational flow engine and retry handling | WhatsApp users, ops; WF Account Settings, WF Settings, WF Active Chat Flow | `waflo/waflo/messaging/retry_message.py:retry_message:6`; internal `flow.processor.process_incoming_whatsapp_message`, `wf_settings.process_retry_message` | `doc_events` WhatsApp Message/WhatsApp Notification Log; `scheduler_events` cron `expire_inactive_flows` and `schedule_retry_message` | `develop` | no | 4 | source-wired; WhatsApp/SAP runtime unverified |

---

## 2. CRM three-layer responsibility / precedence (MA4)

| Layer | App | Primary DocTypes | Key hooks / overrides | Representative interfaces | Precedence / notes |
|-------|-----|------------------|-----------------------|---------------------------|--------------------|
| **Legacy operational CRM** | `visaguy_crm` | ERPNext `Lead`, `Customer`, `ToDo`, `FF File Collection`, `PF Process File`, Payment/Sales docs | `has_permission` Lead; `permission_query_conditions` Lead/PF/Sales Order; extensive `doc_events` on Lead/Customer/ToDo/FF/PF/Sales Invoice/Payment Entry/Sales Order/Payment Request/Journal Entry/User/Notification Settings; overrides `Payment Request` class and `fileflo` methods | `customer_creation.py`, `lead_functions.py`, `allocated_to_process_file.py:create_process_file`, `data_collecting_form.py`, `server_scripts/payment_from_lead/*`, `server_scripts/rpa/generate_application_form.py` | Still source-wired for legacy pipeline, Zoho integration, and payment flows. Do not assume it is unused. |
| **Modern CRM core** | `crm` | `CRM Lead`, `CRM Deal`, `CRM Organization`, `Contact`, `ToDo`, `Comment`, `WhatsApp Message`, `User` | `doc_events` on Contact/ToDo/Comment/WhatsApp Message/CRM Deal/User; `after_migrate` FCRM settings; ERPNext integration via `erpnext_crm_settings` | `crm_lead/api.py:get_lead`, `crm_lead.py:convert_to_deal`, `crm_deal/api.py:get_deal`, `api/views.py:get_views`, `api/contact.py`, `api/whatsapp.py`, `integrations/twilio/api.py`, `integrations/exotel/handler.py` | Primary UI/pipeline layer. `CRM Deal` `on_update` creates an ERPNext `Customer` via `erpnext_crm_settings.create_customer_in_erpnext`. |
| **Frappe CRM customization / migration bridge** | `visaguy_frappe_crm` | `CRM Lead`, `ToDo` (via `crm`) | `doc_events` on `CRM Lead` before_insert/before_save/validate and `ToDo` before_save; `permission_query_conditions` CRM Lead/Department; fixtures for layouts/property setters/permissions | `handle_lead_send_form`, `check_duplicate_lead`, `get_zone_details`, `get_details_of_session_user` | Runs **before** core CRM persists a `CRM Lead`. `crm_migration_settings` implies a migration path from legacy to Frappe CRM. |

**Synthesis:** The three layers are not mutually exclusive. New leads may enter as `Raw Lead` (`the_visaguy`) or directly as `CRM Lead` (`visaguy_frappe_crm`/`visaguy_website`); `visaguy_frappe_crm` enriches the `CRM Lead` before the core `crm` app stores/presents it. The core `crm` layer owns the modern pipeline and converts `CRM Deal` into ERPNext `Customer`. `visaguy_crm` continues to own the legacy ERPNext `Lead` lifecycle, process files, and payment/Zoho integrations. Runtime precedence by entry point must be confirmed with maintainers.

---

## 3. Evidenced end-to-end workflows (MA3)

All workflows are **source-wired**; live traffic and external-provider configuration are unverified.

### W1 — Public eligibility / lead capture → CRM → ERPNext customer
1. Public form writes a `Raw Lead` (`the_visaguy/tvg_crm/doctype/raw_lead/raw_lead.py:convert_to_crm_lead`) or a `CRM Lead` is created via `visaguy_frappe_crm/functions/apis/check_duplicate_lead.py:check_duplicate_lead`.
2. `visaguy_frappe_crm` hooks run on `CRM Lead` before insert (`add_zone`, `customer_creation`) and before save (`update_number_of_applicants`, `update_department`) and validate (`crm_lead_validations`, `validate_payment_confirmed`).
3. Core `crm` serves the lead through `crm_lead/api.py:get_lead` and list views (`api/views.py:get_views`).
4. Sales converts `CRM Lead` to `CRM Deal` via `crm_lead.py:convert_to_deal`.
5. `CRM Deal` `on_update` triggers `crm/fcrm/doctype/erpnext_crm_settings/erpnext_crm_settings.create_customer_in_erpnext`, creating an ERPNext `Customer`.
6. Side effects: `the_visaguy` sends WhatsApp lead updates and conversion events; `visaguy_raven` sends CRM form-submission notifications.

### W2 — Consumer website visa order → document collection → process file → payment → communications
1. Consumer portal calls `visaguy_website/api/create_visa_order.py:create_visa_order` and `api/submit_application.py:submit_application`.
2. `visaguy_business/functions/api/create_process_file.py:create_process_file` and `request_payment_for_visa_order` create a `PF Process File` and a payment request.
3. `processflo/processflo/doctype/pf_process_file/pf_process_file.py:fetch_actions` and `create_process_deliverables` drive the process workflow.
4. `fileflo/form_generation.py:generate_form` and `fileflo/data_collection.py:add_form_data` produce an `FF File Collection` for applicant uploads.
5. `payment_integrations` receives TotalPay/MyFatoorah webhooks (`totalpay_settings.py:handle_webhook`, `webhook/myfatoorah.py:handle_webhook`); `Payment Request` `on_update_after_submit` calls `payment_integrations.integrations.on_update_after_submit`.
6. `visaguy_business` doc_events update the wallet on `Payment Entry` submit and mark completion on `PF Process File` / `FF File Collection` updates.
7. Communications: `waflo` processes incoming WhatsApp messages; `the_visaguy` sends PF Process File updates; `visaguy_raven` notifies on PF Process File/ToDo/Comment changes.

### W3 — B2B business portal → wallet / invoice / order
1. Business portal calls `visaguy_business/functions/api/get_business_details`, `get_invoice_items`, `get_visa_price`, `generate_preliminary_documents`, `create_process_file`, and `request_payment_for_visa_order`.
2. Fixtures provision Business Client roles, a price list, a customer group, and the `Wallet Advance - T` account (`visaguy_business/hooks.py` fixtures).
3. `permission_query_conditions` restrict `Business Client Visa Order` and `Sales Invoice`; `has_permission` Sales Invoice enforces B2B access.
4. `Payment Entry` `on_submit` updates the business wallet; `Sales Invoice` `on_submit` updates the business client visa order.

### W4 — HR leave / timesheet / interview → approval → notifications
1. `visaguy_hrms` overrides `Interview`, `Expense Claim`, and `Employee` classes and `hrms.api.get_leave_types`.
2. `doc_events` enforce interview emails, timesheet restrictions, leave-balance validation, maternity checks, and appointment-letter file sync.
3. Fixtures ship `Leave Approval` and `Overtime Approval` workflows.
4. `visaguy_raven` sends leave-request notifications on `Leave Application` insert/update and daily timesheet reminders.
5. Optional push layer: `frappe_notifier` (external `notification_relay` overrides) and `employee_self_service` FCM hooks.

### W5 — Support ticket → agent assignment → helpdesk
1. Customers/agents use the `/helpdesk` route (`helpdesk/hooks.py` `website_route_rules`).
2. `helpdesk` provides `HD Ticket`, `HD Agent`, `HD Team`, and ticket APIs (`hd_ticket/api.py:new/get_one`, `hd_ticket.py:assign_agent/reply_via_agent`).
3. `visaguy_helpdesk` overrides the `HD Ticket` class (`server_scripts/hd_ticket_class_override.py`) and sets agent groups via `doc_events`.
4. `visaguy_helpdesk` adds `permission_query_conditions` on `HD Ticket`.
5. `visaguy_raven` sends `ToDo` assignment and `Comment` notifications.

---

## 4. Reusable interface tables (MA5)

### Business / B2B interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Get business details | `visaguy_business` | `functions/api/get_business_details.py:get_business_details:4` | B2B client context |
| Get invoice items | `visaguy_business` | `functions/api/get_invoice_items.py:get_invoice_items:7` | Priced line items for B2B |
| Get visa price | `visaguy_business` | `functions/api/get_visa_price.py:get_visa_price:6` | Destination pricing |
| Generate preliminary documents | `visaguy_business` | `functions/api/generate_preliminary_documents.py:generate_preliminary_documents:8` | Document generation |
| Create process file / request payment | `visaguy_business` | `functions/api/create_process_file.py:create_process_file:13`, `request_payment_for_visa_order:241` | Start case and payment |
| Get applicant files | `visaguy_business` | `functions/api/get_applicant_files.py:get_applicant_files:5` | Uploaded file listing |

### Consumer website interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Create visa order | `visaguy_website` | `api/create_visa_order.py:create_visa_order:12` | Consumer order creation |
| Submit application | `visaguy_website` | `api/submit_application.py:submit_application:15` | Final application submit |
| Get destination items | `visaguy_website` | `api/get_destination_items.py:get_destination_items:11` | Destination catalog |
| Get file template | `visaguy_website` | `api/get_file_template.py:get_file_template:11` | Required documents template |
| Get applicant files | `visaguy_website` | `api/get_applicant_files.py:get_applicant_files:5` | Consumer file status |

### Document & process interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Generate form | `fileflo` | `fileflo/form_generation.py:generate_form:5` | Build upload form |
| Fetch form data | `fileflo` | `fileflo/data_collection.py:fetch_form_data:6` | Read collected data |
| Add form data | `fileflo` | `fileflo/data_collection.py:add_form_data:138` | Store applicant input |
| Document fetch | `fileflo` | `fileflo/document_fetch.py:document_fetch:9` | Retrieve documents |
| Download zip | `fileflo` | `fileflo/download_file.py:download_files_as_zip:10` | Bulk download |
| Generate file collection for process file | `processflo` | `generate_file_collection.py:generate_file_collection_process_file:72` | Link docs to case |
| Fetch process actions | `processflo` | `processflo/doctype/pf_process_file/pf_process_file.py:fetch_actions:63` | Next workflow actions |
| Create process deliverables | `processflo` | `processflo/doctype/pf_process_file/pf_process_file.py:create_process_deliverables:43` | Case outputs |

### CRM interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Convert raw lead to CRM lead | `the_visaguy` | `tvg_crm/doctype/raw_lead/raw_lead.py:convert_to_crm_lead:20` | Eligibility-form ingestion |
| Get visa types / destinations | `the_visaguy` | `tvg_core/doctype/destination_configuration/destination_configuration.py:get_visa_types:26` | Catalog lookup |
| Duplicate lead check | `visaguy_frappe_crm` | `functions/apis/check_duplicate_lead.py:check_duplicate_lead:4` | Deduplication |
| Get zone details | `visaguy_frappe_crm` | `functions/apis/get_zone_details.py:get_zone_details:5` | Zone enrichment |
| Handle lead send form | `visaguy_frappe_crm` | `functions/lead_file_collection.py:handle_lead_send_form:12` | File-collection trigger |
| Get CRM lead / deal | `crm` | `crm_lead/api.py:get_lead:8`, `crm_deal/api.py:get_deal:8` | Read CRM records |
| Convert lead to deal | `crm` | `crm_lead.py:convert_to_deal:404` | Pipeline conversion |
| Manage contacts / views | `crm` | `api/contact.py`, `api/views.py:get_views:6` | CRM UX data |
| WhatsApp / call integration | `crm` | `api/whatsapp.py`, `integrations/twilio/api.py`, `integrations/exotel/handler.py` | Communications |
| Legacy lead/customer creation | `visaguy_crm` | `customer_creation.py:enque_create_customer:168`, `create_customer_id_existing_lead:200` | Legacy CRM back-fill |
| Legacy process file creation | `visaguy_crm` | `allocated_to_process_file.py:create_process_file:49` | Legacy case creation |
| Update applicant details | `visaguy_crm` | `api/update_applicant_details.py:update_applicant_details:6` | Legacy applicant sync |

### Helpdesk interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| New / get ticket | `helpdesk` | `hd_ticket/api.py:new:13`, `get_one:37` | Ticket CRUD |
| Assign / reply / comment | `helpdesk` | `hd_ticket/hd_ticket.py:assign_agent:345`, `reply_via_agent:460`, `new_comment:447` | Agent actions |
| Search KB | `helpdesk` | `api/article.py:search:4`, `search.py:search:190` | Knowledge base search |
| Override ticket methods | `visaguy_helpdesk` | `server_scripts/hd_ticket_class_override.py:assign_agent:419`, `reply_via_agent:541`, `mark_seen:803`, etc. | Custom ticket behavior |

### HRMS interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Get leave types | `visaguy_hrms` | `api/get_leave_types.py:get_leave_types:5` | Leave catalog |
| Expense claim overrides | `visaguy_hrms` | `custom_scripts/expense_claim_doctype_class_override.py:make_bank_entry:440`, `calculate_taxes:311`, etc. | Custom claim accounting |
| Interview overrides | `visaguy_hrms` | `custom_scripts/interview_doctype_class_override.py:reschedule_interview:80`, `create_interview_feedback:393`, etc. | Interview workflow |
| Appointment letter file collection | `visaguy_hrms` | `custom_scripts/appointment_letter_server_scripts.py:generate_file_collection_for_appointment_letter:11` | Onboarding docs |
| Email send override | `visaguy_hrms` | `custom_scripts/email_send_override.py:make_override:26` | Custom mail routing |

### Raven interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| CRM form submission notifications | `visaguy_raven` | `functions/send_form_submission.py` | Lead/PF updates |
| Assignment notifications | `visaguy_raven` | `functions/send_assignment.py` | ToDo assignment |
| Comment notifications | `visaguy_raven` | `functions/send_comment.py` | Doc comments |
| Leave request notifications | `visaguy_raven` | `functions/send_leave_request.py` | HR approvals |
| Business order notifications | `visaguy_raven` | `functions/send_business.py` | B2B order lifecycle |
| Sales/discount/refund workflows | `visaguy_raven` | `functions/send_sales_order.py`, `send_credit_note.py`, `send_refund.py` | Accounts events |
| Daily timesheet reminders | `visaguy_raven` | `functions/send_timesheet_reminders.py` | Scheduled HR nudge |
| Core Raven platform | `raven` | `raven/api/*`, `raven_integrations/doctype/raven_document_notification` | Messaging infrastructure |

### WhatsApp / notification / OTP interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| Incoming WhatsApp flow processing | `waflo` | `waflo/flow/processor.process_incoming_whatsapp_message` | Conversational flows |
| Retry failed messages | `waflo` | `waflo/messaging/retry_message.py:retry_message:6` | Manual retry API |
| WhatsApp lead/PF updates | `the_visaguy` | `handlers/whatsapp_message.send_lead_updates`, `send_process_file_updates` | Status messaging |
| WhatsApp feedback capture | `the_visaguy` | `handlers/receive_feedback.receive_feedback` | Quality feedback |
| Bulk WhatsApp / templates | `frappe_whatsapp` | `utils/bulk_messaging.py`, `doctype/whatsapp_notification.py`, `utils/webhook.py` | Provider integration |
| FCM token/topic/push | `frappe_notifier` | `api/token.py`, `api/topic.py`, `api/send_notification.py` | Push notifications |
| OTP verify / issue credentials | `otp_authentication` | `otp_verification.py:otp_verification:10`, `generate_api_credentials:86` | Consumer auth |

### Payment & conversion-tracking interfaces

| Interface | App | Entry point | Purpose |
|-----------|-----|-------------|---------|
| TotalPay webhook | `payment_integrations` | `payment_integrations/doctype/totalpay_settings/totalpay_settings.py:handle_webhook:169` | Gateway callback |
| MyFatoorah webhook | `payment_integrations` | `webhook/myfatoorah.py:handle_webhook:6` | Gateway callback |
| Payment request integration | `payment_integrations` | `payment_integrations/integrations.py:on_update_after_submit` | Post-submit hook |
| Upstream payment checkout | `payments` | `templates/pages/stripe_checkout.py:make_payment:79`, `razorpay_checkout.py`, `paypal_settings.py`, etc. | Standard gateways |
| Meta conversion webhook | `frappe_conversions_api` | `api/meta/webhook.py:webhook:5` | Ad attribution events |

---

## 5. Operational procedures (MA6)

**All procedures are documented from source evidence; no commands were executed.**

### Installation
- Standard Frappe app install: `bench get-app <remote> --branch <branch>` then `bench --site visaguy install-app <app>`.
- `payment_integrations` declares `required_apps = ["erpnext", "payments"]`; install those first.
- Apps with `install.py`: `crm`, `payment_integrations`, `frappe_conversions_api`, `raven`, `hrms`, `employee_self_service`, `india_compliance`, `non_profit`.

### Fixtures
- Apps with fixtures (see catalog table) need a migrate or `bench --site visaguy export-fixtures` after configuration changes to avoid drift.
- Notable fixture-heavy apps: `visaguy_crm` (workflows, roles, Insights charts/queries), `visaguy_hrms` (workflows, notifications, appointment templates), `visaguy_business` (accounts, price lists, roles), `visaguy_raven` (Raven bots/users/document notifications), `the_visaguy` (quality-feedback dashboard blocks).

### Patches / migration
- Most apps include `patches.txt` with `[pre_model_sync]` / `[post_model_sync]` entries. Run via `bench --site visaguy migrate`.
- Apps with `after_migrate`/`before_migrate` hooks: `crm` (`fcrm_settings.after_migrate`), `helpdesk` (`search.build_index_in_background`), `hrms`, `employee_self_service`, `india_compliance`, `frappe`, `erpnext`, `payments`.

### Build / assets
- `bench build` or `bench watch` (Procfile already runs `bench watch`) after changes to:
  - `fileflo` desk JS (`form_creation.js`, `document_fetch.js`, `download_zip.js`)
  - `visaguy_crm` bundle (`visaguy_crm.bundle.js`)
  - `visaguy_hrms` desk JS (`js/desk.js`)
  - `processflo` web JS (`fetch_action.js`, `create_file_collection.js`)
  - `quick_kanban` bundle (`quick_kanban.bundle.css`, `kanban_view.bundle.js`)
- **Caveat:** system Node is v12 while Socket.IO uses Node v18 via `.nvm`; verify build toolchain compatibility.

### Scheduler / background jobs
- `bench schedule` runs jobs registered in `scheduler_events`.
- Key jobs: `the_visaguy` daily tmp-file clearing; `frappe_notifier` daily log cleanup; `waflo` cron every minute (flow expiry) and hourly retries; `visaguy_raven` daily timesheet reminders; `helpdesk` `all` search-index check; `crm` `after_migrate` settings; `frappe_whatsapp` frequent intervals.

### Validation / tests
- Run `bench --site visaguy run-tests --app <app>`.
- Low-coverage maintained apps: `quick_kanban` (0 tests), `visaguy_hrms` (2 tests / 69 .py), `visaguy_helpdesk` (1/16), `visaguy_frappe_crm` (1/27), `visaguy_raven` (1/23), `otp_authentication` (2/24).

---

## 6. Risk register (MA7)

| App | Primary risk | Evidence / category | Verification label |
|-----|--------------|---------------------|--------------------|
| `crm` | Maintained fork on non-standard `tridz-dev` branch; upstream drift/merge risk | `01b-remote-bench.md` RB2/RB8 | statically verified |
| `fileflo` | Branch `fix/mandatory-file` suggests unmerged patch; verify before production | `01b-remote-bench.md` RB8 | statically verified |
| `frappe_conversions_api` | Single whitelisted endpoint, minimal tests; Meta/Google credentials/runtime unverified | `maintained_raw.json` whitelisted count=1, tests=3 | source-wired, runtime unverified |
| `frappe_notifier` | Depends on external FCM/Relay; service-account placement and relay URL runtime unverified | `frappe_notifier/hooks.py` `after_install` `setup_users`, README | source-wired, runtime unverified |
| `helpdesk` | Maintained fork on `modification_develop_branch`; divergence and upgrade risk | `01b-remote-bench.md` RB8 | statically verified |
| `otp_authentication` | Non-standard `email` branch, only 1 test; OTP gateway/runtime unverified | `maintained_raw.json` tests=1, branch `email` | source-wired, runtime unverified |
| `payment_integrations` | Custom TotalPay/MyFatoorah webhooks; secrets and provider config runtime unverified | `payment_integrations/hooks.py` `doc_events`, whitelisted webhooks | source-wired, runtime unverified |
| `processflo` | Pre-existing dirty working tree (diffs not inspected); deploy from this checkout is risky | `01b-remote-bench.md` RB8 | statically verified, dirty diffs uninspected |
| `quick_kanban` | No tests; bundle override of Frappe Kanban impact unverified | `maintained_raw.json` tests=0 | source-wired, validation gap |
| `the_visaguy` | Quality Feedback/Insights fixtures reference hardcoded names; migration-order dependency | `the_visaguy/hooks.py` fixtures | source-wired, runtime unverified |
| `visaguy_business` | Wallet advance account and price-list fixtures assume a specific company chart; must be configured before use | `visaguy_business/hooks.py` fixtures | source-wired, configuration gap |
| `visaguy_crm` | Large legacy layer overlaps with `crm`/`visaguy_frappe_crm`; duplicated lead/payment lifecycle and Zoho integration risk during migration | `visaguy_crm/hooks.py` extensive `doc_events`, `01b-remote-bench.md` RB4 | source-wired, precedence unverified |
| `visaguy_frappe_crm` | Dirty working tree, only 1 test; migration settings and CRM Lead customizations runtime unverified | `maintained_raw.json` tests=1, `01b-remote-bench.md` RB8 | statically verified, dirty diffs uninspected |
| `visaguy_helpdesk` | Only 1 test; `HD Ticket` class override may break on `helpdesk` upgrade | `maintained_raw.json` tests=1, class override in hooks | source-wired, compatibility gap |
| `visaguy_hrms` | Only 2 tests for 69 .py files; class overrides on Interview/Expense Claim/Employee may conflict with HRMS patches | `maintained_raw.json` tests=2, `01b-remote-bench.md` RB5 | source-wired, compatibility gap |
| `visaguy_raven` | Dirty working tree, no whitelisted APIs; silent notification failures possible | `maintained_raw.json` whitelisted count=0, tests=1, `01b-remote-bench.md` RB8 | statically verified, dirty diffs uninspected |
| `visaguy_website` | Direct website APIs create visa orders; guest/API-key permission model needs security review | `visaguy_website/hooks.py` `permission_query_conditions`, `doc_events` | source-wired, auth model unverified |
| `waflo` | Cron every minute for flow expiration plus SAP/WhatsApp account configs; performance and provider runtime unverified | `waflo/hooks.py` `scheduler_events` cron | source-wired, runtime unverified |

### Overarching unresolved questions
- Dirty trees on `processflo`, `visaguy_frappe_crm`, `visaguy_raven` (and external `insights`, `mansico_meta_integration`) predate this work; their diffs were not inspected.
- Runtime responsibility and precedence among CRM, Helpdesk, HRMS, Raven, and payment layers still needs maintainer confirmation.
- System Node v12 vs Socket.IO Node v18 split may affect frontend builds.
