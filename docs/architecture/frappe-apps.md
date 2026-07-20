# Frappe Apps

This document describes the 18 internally maintained Frappe apps installed on site `visaguy` and the 11 external/upstream apps. For ownership, version/HEAD, and install status, see [`repository-catalog.md`](repository-catalog.md).

## Internally maintained apps (18)

### Core domain and communication

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `the_visaguy` | Core VisaGuy domain: raw leads, destinations, WhatsApp feedback, quality feedback | Raw Lead, Destination Configuration, Quality Feedback, WhatsApp Defaults/Templates | `convert_to_crm_lead`, `get_visa_types`, `get_visa_price`, `get_invoice_items` | source-wired |
| `waflo` | WhatsApp conversational flow engine and retry handling | WF Account Settings, WF Settings, WF Active Chat Flow | `retry_message`, `process_incoming_whatsapp_message` | source-wired |

### CRM layers

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `crm` | Modern CRM UI, lead/deal pipeline, call/WhatsApp/ERPNext integration | CRM Lead, CRM Deal, CRM Organization, Contact, Address, CRM Call Log | `get_lead`, `convert_to_deal`, `get_deal`, `api/views`, `api/contact`, `api/whatsapp`, Twilio/Exotel integrations | source-wired |
| `visaguy_crm` | Legacy operational CRM around ERPNext Lead, process files, payments, Zoho integration, lead allocation | Lead (ERPNext), Customer, ToDo, FF File Collection, PF Process File | `customer_creation`, `lead_functions`, `create_process_file`, `update_applicant_details` | source-wired |
| `visaguy_frappe_crm` | Customize and migrate to Frappe CRM; zone, customer, validations, duplicate checks | CRM Lead, ToDo (via `crm`), CRM Migration Settings | `handle_lead_send_form`, `get_zone_details`, `check_duplicate_lead`, `get_details_of_session_user` | source-wired |

### Business and consumer surfaces

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `visaguy_business` | B2B portal ordering, wallet, business client visa orders, invoices | Business Client Settings, Business Client Visa Order | `generate_preliminary_documents`, `get_applicant_files`, `get_invoice_items`, `get_business_details`, `get_visa_price`, `create_process_file`, `request_payment_for_visa_order` | source-wired |
| `visaguy_website` | Consumer/e-commerce Next.js website backend: visa orders, destinations, applications, file status | Visaguy Website Visa Order, Destination (custom fields) | `create_visa_order`, `submit_application`, `get_destination_items`, `get_file_template`, `get_applicant_files` | source-wired |

### Document and process workflows

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `fileflo` | Document forms, file collection, data collection, zip downloads | Fileflo Settings, FF File Collection | `generate_form`, `fetch_form_data`, `add_form_data`, `document_fetch`, `download_files_as_zip` | source-wired |
| `processflo` | Process workflow engine and deliverables for visa cases | PF Process File, PF Process Action, PF Process Deliverables | `generate_file_collection_process_file`, `fetch_actions`, `create_process_deliverables` | source-wired |

### HR, helpdesk, and Raven

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `visaguy_hrms` | HRMS customizations: leave, timesheet, interviews, appointment letters, expense claims | Interview, Expense Claim, Employee, Leave Application | `get_leave_types`, class overrides for Interview/Expense Claim/Employee | source-wired |
| `visaguy_helpdesk` | Customization layer over Frappe Helpdesk; agent group assignment, ticket override, permissions | HD Ticket (from `helpdesk`) | `assign_agent`, `get_last_communication`, `new_comment`, `reply_via_agent`, `mark_seen` | source-wired |
| `visaguy_raven` | Raven notification orchestration for CRM, HR, business, accounts events | Raven Bot/User/Document Notification | `send_form_submission`, `send_assignment`, `send_comment`, `send_leave_request`, `send_business`, `send_sales_order`, `send_credit_note`, `send_refund`, `send_timesheet_reminders` | source-wired |

### Messaging, notifications, payments, and utilities

| App | Responsibility | Key DocTypes / Entities | Key Interfaces | Verification |
|---|---|---|---|---|
| `frappe_notifier` | FCM push notifications via Frappe Relay | FN Notification Log, Frappe Notifier Settings | `add`/`remove` token, `add`/`remove`/`subscribe`/`unsubscribe` topic, `send_notification` | source-wired |
| `frappe_conversions_api` | Meta/Google Conversions API event forwarding | Conversion Account/Event | `webhook` | source-wired |
| `otp_authentication` | OTP generation/verification and API credential issuance for consumer portal | OTP Settings | `otp_verification`, `generate_api_credentials`, `user_check_otp_send` | source-wired |
| `payment_integrations` | Custom payment gateways (TotalPay, MyFatoorah) | TotalPay Settings, MyFatoorah Settings | `handle_webhook`, `payment_success`, `payment_cancel`, `on_update_after_submit` | source-wired |
| `quick_kanban` | Enhanced Vue-based Kanban view | Kanban Board Highlight | `get_kanban_config` | source-wired |

## External/upstream apps (11)

| App | Role in VisaGuy | Direct VisaGuy Dependencies | Verification |
|---|---|---|---|
| `frappe` | Core framework, desk, website, auth, files, scheduler, notifications | Used by every app | source-wired |
| `erpnext` | ERP backbone: accounts, selling, CRM base, stock | `visaguy_business`, `visaguy_crm`, `payment_integrations`, `non_profit` | source-wired |
| `hrms` | HR, payroll, leaves, expenses, projects | Wrapped by `visaguy_hrms` | source-wired |
| `payments` | Payment gateway scaffolding (Stripe, Razorpay, PayPal, etc.) | Required by `payment_integrations` | source-wired |
| `india_compliance` | Indian GST, e-Waybill, audit-trail compliance | Hard dependency on `frappe`/`erpnext` | source-wired |
| `insights` | Embedded analytics / dashboards / charts | Fixtures referenced by `visaguy_crm`, `visaguy_hrms`, `the_visaguy` | source-wired |
| `raven` | Team messaging, document notifications, AI features | Wrapped by `visaguy_raven` | source-wired |
| `frappe_whatsapp` | WhatsApp Business API integration | Used by `waflo`, `the_visaguy`, `crm` | source-wired |
| `non_profit` | Memberships, donations, chapter/grant management | Requires `erpnext`; overrides `Payment Entry` | source-wired |
| `employee_self_service` | Mobile ESS / HR self-service | Bench-only; requires ERPNext + HRMS | source-wired |
| `mansico_meta_integration` | Facebook / Meta lead sync into ERPNext Lead | Bench-only; requires `erpnext` | source-wired |

## Dependency and upgrade notes

### `required_apps` constraints

- `india_compliance` → `frappe`, `erpnext`
- `non_profit` → `erpnext`
- `payment_integrations` → `erpnext`, `payments`
- `mansico_meta_integration` → `erpnext`
- `hrms` → `frappe`, `erpnext`

### Recommended upgrade order

1. `frappe`
2. `erpnext`
3. `hrms` / `payments`
4. `india_compliance`
5. Remaining apps
6. Run wrapper tests between each step.

### Fork/wrapper relationships

- `crm` (maintained fork) + `visaguy_crm` (legacy) + `visaguy_frappe_crm` (migration bridge)
- `helpdesk` (maintained fork) + `visaguy_helpdesk`
- `hrms` (upstream) + `visaguy_hrms`
- `raven` (upstream) + `visaguy_raven`
- `payments` (upstream) + `payment_integrations`
