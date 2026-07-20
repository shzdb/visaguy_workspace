# Customizations

## Precedence matrix

| Domain | Base app | Custom layer(s) | Hook / override type | Migration / upgrade risk | Validation gate |
|---|---|---|---|---|---|
| Frappe / ERPNext core | `frappe`, `erpnext` | `visaguy_crm`, `visaguy_business`, `visaguy_hrms`, `payment_integrations`, `non_profit`, `india_compliance`, `frappe_whatsapp` | File-manager methods; `Address` class; `Web Form` class; `Payment Entry` class; `send_message`; outstanding-reference method | High — base classes/methods overridden by multiple apps | Run `bench migrate` in staging; execute wrapper tests; verify payment, leave, invoice, ticket flows |
| CRM | `crm` (maintained fork) | `visaguy_crm` (legacy), `visaguy_frappe_crm` (migration bridge) | `doc_events` on `CRM Lead`, `ToDo`; `permission_query_conditions`; fixtures; `erpnext_crm_settings` | High — three layers with overlapping lead/customer events; fork drift | Duplicate-lead check, lead→deal conversion, ERPNext customer creation, legacy lead capture |
| Helpdesk | `helpdesk` (maintained fork) | `visaguy_helpdesk` | Class override of `HD Ticket`; `doc_events`; `permission_query_conditions` | Medium-High — fork on non-standard branch; class override fragile | Ticket creation, agent assignment, reply/comment, permission scoping |
| HRMS | `hrms` | `visaguy_hrms` | Class overrides of `Interview`, `Expense Claim`, `Employee`; method override `hrms.api.get_leave_types`; `frappe.core...email.make`; `doc_events` | Medium-High — only 2 tests for 69 .py files | Leave application, expense claim, interview reschedule, timesheet, appointment-letter file collection |
| Raven | `raven` | `visaguy_raven` | `doc_events` on many doctypes; daily timesheet reminder scheduler; fixtures | Medium — base branch not version-15; no whitelisted APIs | Trigger notifications for each subscribed doctype; verify Raven channel delivery |
| Payments | `payments` | `payment_integrations` (TotalPay/MyFatoorah) | `required_apps`; `Payment Request` `on_update_after_submit`; webhook handlers | Medium-High — gateway webhooks depend on stable endpoints/signatures | End-to-end payment request, redirect, webhook, invoice status, refund path |
| FileFlo / ProcessFlo | `fileflo`, `processflo` | `visaguy_crm`, `visaguy_business`, `visaguy_website` | Form generation, data collection, zip download; PF Process File actions/deliverables; web bundles | Medium — `processflo` dirty tree; web bundles require `bench build` | Generate file collection, fetch actions, create deliverables, submit form data, download zip |

## Hooks and overrides

### DocType class overrides

| App | Overridden class | Base app |
|---|---|---|
| `erpnext` | `Address` | `erpnext` |
| `payments` | `Web Form` | `frappe` |
| `india_compliance` | `Customize Form` | `frappe` |
| `non_profit` | `Payment Entry` | `erpnext` |
| `visaguy_crm` | `Payment Request` | `erpnext` |
| `visaguy_hrms` | `Interview`, `Expense Claim`, `Employee` | `hrms` / `frappe` |
| `visaguy_helpdesk` | `HD Ticket` | `helpdesk` |
| `crm` | `Contact`, `Email Template` | `frappe` |
| `hrms` | `Employee`, `Timesheet`, `Payment Entry`, `Project` | `frappe` / `erpnext` |

### Whitelisted method overrides

| App | Overridden method | Base app |
|---|---|---|
| `frappe` | File-manager download/unzip/search/move/zip methods | `frappe` |
| `frappe` | OAuth login routes (`login_via_google`, `login_via_github`, etc.) | `frappe` |
| `erpnext` | `frappe.www.contact.send_message` | `frappe` |
| `payments` | `frappe.website.doctype.web_form.web_form.accept` | `frappe` |
| `india_compliance` | `erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents` | `erpnext` |
| `visaguy_crm` | `fileflo.data_collection.fetch_form_data`, `add_form_data`, `fileflo.form_generation.generate_form` | `fileflo` |
| `visaguy_hrms` | `hrms.api.get_leave_types`, `frappe.core.doctype.communication.email.make` | `hrms` / `frappe` |
| `frappe_notifier` | `notification_relay.api.*` token/topic/send methods | external relay |

### `doc_events`

Key event wiring by app:

- `the_visaguy`: WhatsApp Message, Lead, CRM Lead, PF Process File, Quality Feedback.
- `visaguy_crm`: Lead, Customer, ToDo, FF File Collection, PF Process File, Sales Invoice, Payment Entry, Sales Order, Payment Request, Journal Entry, User, Notification Settings.
- `visaguy_frappe_crm`: CRM Lead (before_insert/before_save/validate), ToDo (before_save).
- `visaguy_business`: Payment Entry, PF Process File, FF File Collection, Sales Invoice.
- `visaguy_website`: FF File Collection, PF Process File.
- `visaguy_hrms`: Interview, Timesheet, Leave Application, Leave Allocation, Appointment Letter, FF File Collection.
- `visaguy_helpdesk`: ToDo, HD Ticket.
- `visaguy_raven`: Lead, CRM Lead, PF Process File, ToDo, Comment, Leave Application, Business Client Visa Order, Sales Order, Sales Invoice, Payment Entry.
- `waflo`: WhatsApp Message, WhatsApp Notification Log.
- `frappe_whatsapp`: Broad `*` server-script runner.
- `payment_integrations`: Payment Request `on_update_after_submit`.

### `permission_query_conditions` and `has_permission`

- `visaguy_crm`: Lead, PF Process File, Sales Order; `has_permission` on Lead.
- `visaguy_business`: Business Client Visa Order, Sales Invoice; `has_permission` on Sales Invoice.
- `visaguy_hrms`: Appraisal Record, Leave Application, Timesheet; `has_permission` on Notification Settings.
- `visaguy_frappe_crm`: CRM Lead, Department.
- `visaguy_helpdesk`: HD Ticket.
- `the_visaguy`: Raw Lead.

## Fixtures

Apps shipping fixtures must run `bench --site visaguy migrate` or `bench --site visaguy export-fixtures` after configuration changes.

| App | Fixture target DocTypes |
|---|---|
| `visaguy_business` | Account, Price List, Customer Group, Custom DocPerm, Role, Role Profile, Client Script, Custom Field, Property Setter |
| `visaguy_hrms` | Workflow, Workflow State, Notification, Appointment Letter Template, Interview Type, Email Template, Server Script, Client Script, Role, Designation, Insights Query/Chart/Dashboard, Print Format, Custom HTML Block, Leave Type, Salary Component |
| `visaguy_crm` | Workflow, Workflow State, Workflow Action Master, Client Script, Insights Dashboard/Query/Chart, Role, Print Format, Custom HTML Block, Workspace |
| `visaguy_helpdesk` | Role |
| `the_visaguy` | Custom Field, Workspace, Custom HTML Block, Insights Query, Insights Chart |
| `visaguy_frappe_crm` | CRM Fields Layout, CRM Global Settings, Property Setter, Custom DocPerm |
| `frappe_notifier` | Role, Custom DocPerm |
| `visaguy_website` | Custom Field, Role |
| `visaguy_raven` | Raven Bot, Raven User, Raven Document Notification |
| `insights` | Insights Data Source |
| `employee_self_service` | ESS Notification, ESS Notification Template |

## Scheduler events

Key scheduled jobs evidenced:

- `the_visaguy`: daily tmp-file clearing.
- `frappe_notifier`: daily log cleanup.
- `waflo`: cron every minute flow expiry; hourly retries.
- `visaguy_raven`: daily timesheet reminders.
- `helpdesk`: `all` search-index check.
- `crm`: `after_migrate` settings.
- `frappe_whatsapp`: frequent intervals.
- `frappe`, `erpnext`, `hrms`, `payments`, `insights`, `employee_self_service`, `non_profit`, `mansico_meta_integration`: standard intervals.

Run `bench --site visaguy console` and inspect `frappe.get_hooks("scheduler_events")` for the full current list.

## Patches and migration hooks

- Most apps include `patches.txt` with `[pre_model_sync]` and `[post_model_sync]` entries.
- Apps with install/migrate hooks: `crm`, `helpdesk`, `payment_integrations`, `frappe_conversions_api`, `raven`, `hrms`, `employee_self_service`, `india_compliance`, `non_profit`, `frappe_notifier`.
- Run `bench --site visaguy migrate` after any app update.

## Asset bundles

Rebuild with `bench build` or `bench watch` after changes to:

- `fileflo` desk JS (`form_creation.js`, `document_fetch.js`, `download_zip.js`)
- `visaguy_crm` bundle (`visaguy_crm.bundle.js`)
- `visaguy_hrms` desk JS (`js/desk.js`)
- `processflo` web JS (`fetch_action.js`, `create_file_collection.js`)
- `quick_kanban` bundle (`quick_kanban.bundle.css`, `kanban_view.bundle.js`)

**Caveat:** system Node is v12 while Socket.IO uses Node v18 via `.nvm`; verify build toolchain compatibility.

## Upgrade gates

Before any Frappe/ERPNext/HRMS/Payments upgrade:

1. Reconcile dirty trees in `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`.
2. Pin non-standard branches (`insights`, `raven`, `frappe_whatsapp`, `non_profit`, `mansico_meta_integration`) to version-compatible tags/branches.
3. Review `required_apps` constraints and upgrade order.
4. Run wrapper tests for `visaguy_hrms`, `visaguy_raven`, `visaguy_crm`, `visaguy_frappe_crm`, `visaguy_helpdesk`, `payment_integrations`.
5. Verify payment gateway webhooks end-to-end.
6. Validate India Compliance migrations.
7. Validate WhatsApp flows.
8. Validate Insights dashboards and data sources.
