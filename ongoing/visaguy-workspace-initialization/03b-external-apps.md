# EA — External app and dependency inventory

Generated: 2026-07-20. Source: accepted reconnaissance in `01b-remote-bench.md` and `STATE.md`; read-only against `/home/fasil/fasil-bench-v15`.

## Executive summary

- External/upstream apps on bench: **11**.
- Installed on site `visaguy`: **9**.
- Bench-only (not installed): **2** (`employee_self_service`, `mansico_meta_integration`).
- Dirty working trees: **2** external repositories (`insights`, `mansico_meta_integration`). Exact diffs not inspected per policy.
- Compatibility risks: **7** (branch drift, dirty trees, overlapping maintained wrappers, Node runtime split).
- Verdict: the VisaGuy stack is a Frappe v15 multi-app bench with clean upstream checkouts for core ERP/HR/payments/chat, plus two dirty/external apps that need reconciliation before any upgrade.

## EA1 — External app catalog

| # | App | Origin / upstream | Branch | HEAD | Version | Installed | Role in VisaGuy | Direct VisaGuy dependencies / integration points | Verification |
|---|---|---|---|---|---|---|---|---|---|
| 1 | `frappe` | Frappe Technologies (`frappe/frappe`) | `version-15` | `01ea89c4e6` | 15.113.0 | Yes | Core framework, desk, website, auth, files, scheduler, notifications | Used by every app; OAuth login and file manager overrides present; `sms_settings`, `push_notification_settings`, `oauth_provider_settings`, etc. | Source / hooks.py / `__init__.py` |
| 2 | `erpnext` | Frappe Technologies (`frappe/erpnext`) | `version-15` | `4dd9f0b255` | 15.106.0 | Yes | ERP backbone: accounts, selling, CRM base, stock | Used by `visaguy_business`, `visaguy_crm`, `payment_integrations`, `non_profit`; `Address` class and `frappe.www.contact.send_message` overridden; `crm_settings`, `voice_call_settings` present | Source / hooks.py / `__init__.py` |
| 3 | `hrms` | Frappe Technologies (`frappe/hrms`) | `version-15` | `5b3285fa` | 15.45.2 | Yes | HR, payroll, leaves, expenses, projects | Wrapped by `visaguy_hrms`; `Employee`, `Timesheet`, `Payment Entry`, `Project` classes overridden | Source / hooks.py / `__init__.py` |
| 4 | `payments` | Frappe Technologies (`frappe/payments`) | `version-15` | `68b54a7` | 0.0.1 | Yes | Payment gateway scaffolding (Stripe, Razorpay, PayPal, etc.) | Required by `payment_integrations`; `Web Form` class and `frappe.website.doctype.web_form.web_form.accept` overridden | Source / hooks.py |
| 5 | `india_compliance` | Resilient Tech (`resilient-tech/india-compliance`) | `version-15` | `bde15f48` | 15.18.0 | Yes | Indian GST, e-Waybill, audit-trail compliance | Hard dependency on `frappe`/`erpnext`; `Customize Form` and `payment_entry.get_outstanding_reference_documents` overridden; `gst_settings` present | Source / hooks.py |
| 6 | `insights` | Frappe Technologies (`frappe/insights`) | `main` | `c9af45d` | 2.2.14 | Yes | Embedded analytics / dashboards / charts | Fixtures `Insights Data Source`; referenced by `visaguy_crm`, `visaguy_hrms`, `the_visaguy` fixtures; `insights_settings` present | Source / hooks.py |
| 7 | `raven` | The Commit Company (`The-Commit-Company/raven`) | `main` | `dfde9b1e` | 2.7.1 | Yes | Team messaging, document notifications, AI features | Wrapped by `visaguy_raven`; `raven_settings` present; document notifications hook into all doctypes | Source / hooks.py |
| 8 | `frappe_whatsapp` | Shridhar Patil (`shridarpatil/frappe_whatsapp`) | `master` | `27f3438` | 1.0.12 | Yes | WhatsApp Business API integration | Used by `waflo`, `the_visaguy`, `crm`; `whatsapp_settings` present; broad `doc_events` hooks | Source / hooks.py |
| 9 | `non_profit` | Frappe (`frappe/non_profit`) | `develop` | `ea2c88d` | 0.0.1 | Yes | Memberships, donations, chapter/grant management | Requires `erpnext`; `Payment Entry` class overridden; `non_profit_settings` present | Source / hooks.py |
| 10 | `employee_self_service` | Nesscale Solutions (`nesscale-com/employee_self_service`) | `version-15` | `f3c1e43` | 2.1.29 | **No** | Mobile ESS / HR self-service | None observed on `visaguy` (bench-only); requires ERPNext + HRMS; `employee_self_service_settings`, `ess_notification_settings` present in code | Source / hooks.py |
| 11 | `mansico_meta_integration` | Ahmed Mansy (`Ahmed-Mansy-Mansico/mansico_meta_integration`) | `master` | `8e595ea` | 1.2.1 | **No** | Facebook / Meta lead sync into ERPNext Lead | None observed on `visaguy` (bench-only); requires `erpnext`; `meta_facebook_settings` present; Lead validation hook declared | Source / hooks.py |

## EA2 — VisaGuy surfaces used per installed external app

Only surfaces materially wired into VisaGuy are listed; upstream product documentation is not restated.

### `frappe`
- Core platform dependency for all 29 apps.
- **Overrides observed**: file manager download/unzip/search/move methods; OAuth social-login routes (`login_via_google`, `login_via_github`, `login_via_facebook`, `login_via_frappe`, `login_via_office365`, `login_via_salesforce`, `login_via_fairlogin`).
- **Settings surfaces used**: `google_settings`, `s3_backup_settings`, `dropbox_settings`, `ldap_settings`, `push_notification_settings`, `oauth_provider_settings`, `sms_settings`.
- **VisaGuy wiring**: `otp_authentication`, `frappe_notifier`, `frappe_whatsapp`, `waflo`, `the_visaguy`, `visaguy_website`, `visaguy_business` all hook into Frappe events and auth.

### `erpnext`
- Financial and CRM backbone.
- **Overrides observed**: `Address` DocType class; `frappe.www.contact.send_message` whitelisted method.
- **Settings surfaces used**: `plaid_settings`, `crm_settings`, `voice_call_settings`, `incoming_call_settings`.
- **VisaGuy wiring**: `visaguy_business` imports ERPNext accounts controllers and payment-entry flows; `visaguy_crm` listens to Lead/Sales Order events; `payment_integrations` extends payment flows; `non_profit` requires `erpnext`.

### `hrms`
- HR and payroll module.
- **Overrides observed**: `Employee`, `Timesheet`, `Payment Entry`, `Project` DocType classes.
- **Settings surfaces used**: `payroll_settings`, `hr_settings`.
- **VisaGuy wiring**: `visaguy_hrms` overrides Interview/Expense Claim/Employee and hooks into leave, timesheet, and appointment-letter flows.

### `payments`
- Payment gateway abstraction.
- **Overrides observed**: `Web Form` DocType class; `frappe.website.doctype.web_form.web_form.accept` whitelisted method.
- **Settings surfaces used**: `paypal_settings`, `razorpay_settings`, `paytm_settings`, `braintree_settings`, `gocardless_settings`, `stripe_settings`, `mpesa_settings`.
- **VisaGuy wiring**: required by `payment_integrations` (MyFatoorah / TotalPay gateways).

### `india_compliance`
- Indian GST and audit-trail compliance.
- **Overrides observed**: `Customize Form` class; `erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents` method.
- **Settings surfaces used**: `gst_settings`.
- **VisaGuy wiring**: none direct beyond being installed; affects ERPNext transactions for Indian entity.

### `insights`
- Embedded analytics.
- **Overrides observed**: `has_permission` for Insights Data Source/Table/Query/Dashboard.
- **Settings surfaces used**: `insights_settings`.
- **VisaGuy wiring**: fixtures ship `Insights Data Source`; `visaguy_crm`, `visaguy_hrms`, `the_visaguy` ship Insights Query/Chart/Dashboard fixtures.

### `raven`
- Team chat and document notifications.
- **Overrides observed**: permission query conditions and `has_permission` for Raven Channel/Message/Poll/etc.
- **Settings surfaces used**: `raven_settings`.
- **VisaGuy wiring**: `visaguy_raven` wraps it and reacts to Lead/CRM Lead/PF Process File updates.

### `frappe_whatsapp`
- WhatsApp Business API messaging.
- **Overrides observed**: broad `doc_events` server-script runner.
- **Settings surfaces used**: `whatsapp_settings`.
- **VisaGuy wiring**: `waflo` processes incoming WhatsApp messages and retries; `the_visaguy` handles WhatsApp feedback/lead updates; `crm` validates WhatsApp messages.

### `non_profit`
- Non-profit membership/donations.
- **Overrides observed**: `Payment Entry` DocType class.
- **Settings surfaces used**: `non_profit_settings`.
- **VisaGuy wiring**: none directly observed; installed and depends on `erpnext`.

## EA3 — Maintained forks versus true upstream checkouts

The 11 apps above are **true upstream/external checkouts** — their primary Git remote points to an upstream organization, not `tridz-dev` or `tvgglobal`.

Two additional bench apps are **maintained forks** of upstream projects and are therefore documented as internally maintained apps:

- `crm` — remote `git@tridz:tridz-dev/frappe-crm.git`, branch `tridz-dev`, version `2.0.0-dev`. Fork of Frappe CRM.
- `helpdesk` — remote `git@tridz:tridz-dev/helpdesk_frk.git`, branch `modification_develop_branch`, version `0.10.0`. Fork of Frappe Helpdesk.

These forks carry VisaGuy-specific customizations and are covered in `03a-maintained-apps.md`, not in this external inventory.

## EA4 — Branch/version drift, dirty status, overrides, and risks

### Branch / version drift

| App | Branch | Concise drift note |
|---|---|---|
| `frappe` | `version-15` | Aligned with declared Frappe v15 baseline. |
| `erpnext` | `version-15` | Aligned with ERPNext v15 baseline. |
| `hrms` | `version-15` | Aligned with HRMS v15 baseline. |
| `payments` | `version-15` | Aligned with Frappe v15 ecosystem. |
| `india_compliance` | `version-15` | Aligned with v15; verify against ERPNext 15.106.0 on upgrade. |
| `employee_self_service` | `version-15` | Aligned with v15; bench-only so drift is latent. |
| `insights` | `main` | Not a `version-15` branch; confirm 2.2.14 compatibility with Frappe 15.113.0 before upgrade. |
| `raven` | `main` | Not a `version-15` branch; 2.7.1 compatibility with Frappe 15.x must be verified. |
| `frappe_whatsapp` | `master` | Not a `version-15` branch; verify against Frappe 15.113.0 on upgrade. |
| `non_profit` | `develop` | Bleeding-edge branch; highest drift risk among installed apps. |
| `mansico_meta_integration` | `master` | Third-party app on `master`; bench-only but dirty. |

### Dirty status

- `insights`: 1 modified/untracked file. Diffs not inspected.
- `mansico_meta_integration`: 1 modified/untracked file. Diffs not inspected.

Both dirty repositories are external. Dirty state on a production bench is a blocker to reproducible builds and upgrades until reconciled.

### Local static hook overrides affecting external apps

Per `RB5` in `01b-remote-bench.md`:

- `frappe`: file-manager and OAuth login methods overridden.
- `erpnext`: `Address` class and `frappe.www.contact.send_message` overridden.
- `hrms`: `Employee`, `Timesheet`, `Payment Entry`, `Project` classes overridden.
- `payments`: `Web Form` class and `frappe.website.doctype.web_form.web_form.accept` overridden.
- `india_compliance`: `Customize Form` class and ERPNext payment-entry method overridden.
- `non_profit`: `Payment Entry` class overridden.

### Risks

1. **Dirty trees on production bench** (`insights`, `mansico_meta_integration`) prevent clean upgrades and reproducible deploys.
2. **Branch drift** (`insights`, `raven`, `frappe_whatsapp` on non-version-15 branches; `non_profit` on `develop`) increases regression risk during Frappe/ERPNext upgrades.
3. **Bench-only apps** (`employee_self_service`, `mansico_meta_integration`) consume bench maintenance without adding site value unless intentionally installed later.
4. **Overlapping maintained wrappers** (`visaguy_hrms`/`hrms`, `visaguy_raven`/`raven`, plus CRM/helpdesk forks) multiply the upgrade test surface.
5. **`india_compliance` version coupling**: its `before_migrate`/`after_migrate` version checks can fail migrations if ERPNext/Frappe advance unevenly.
6. **`frappe_whatsapp` master**: broad `doc_events` hook may change behavior with Frappe API changes.
7. **Node runtime split** (system Node 12 vs Socket.IO Node 18) is not caused by these apps but can break frontend builds during upgrades.

## EA5 — Dependency/version compatibility table and safe upgrade checklist

### Compatibility matrix

| Component | Installed version | Branch | Frappe v15 declared target | Risk level | Notes |
|---|---|---|---|---|---|
| Frappe | 15.113.0 | `version-15` | Yes | Low | Base platform. |
| ERPNext | 15.106.0 | `version-15` | Yes | Low | Core ERP. |
| HRMS | 15.45.2 | `version-15` | Yes | Low | HR/payroll. |
| Payments | 0.0.1 | `version-15` | Yes | Low | Gateway abstraction. |
| India Compliance | 15.18.0 | `version-15` | Yes | Medium | Tight coupling with ERPNext accounts/GST logic; verify release notes. |
| Insights | 2.2.14 | `main` | Unclear | Medium-High | Not a version-15 branch; dirty tree; dashboards depend on it. |
| Raven | 2.7.1 | `main` | Unclear | Medium | Messaging layer; `visaguy_raven` depends on it. |
| Frappe WhatsApp | 1.0.12 | `master` | Unclear | Medium | `waflo`/`the_visaguy`/`crm` depend on WhatsApp flows. |
| Non Profit | 0.0.1 | `develop` | No | High | Bleeding-edge branch; overrides `Payment Entry`. |
| Employee Self Service | 2.1.29 | `version-15` | Yes | Low (latent) | Bench-only; no site impact unless installed. |
| Mansico Meta Integration | 1.2.1 | `master` | Unclear | High (latent) | Bench-only, dirty, third-party Meta lead sync. |

**Compatibility risk count: 7** (India Compliance, Insights, Raven, Frappe WhatsApp, Non Profit, Employee Self Service latent, Mansico Meta Integration latent/dirty).

### Safe upgrade impact checklist

Before any Frappe/ERPNext/HRMS/Payments upgrade:

1. **Reconcile dirty trees** — commit or revert changes in `insights` and `mansico_meta_integration`.
2. **Pin branches** — move `insights`, `raven`, `frappe_whatsapp`, `non_profit`, and `mansico_meta_integration` to version-compatible tags or branches if available.
3. **Review `required_apps` constraints** — `india_compliance`, `hrms`, `non_profit`, `payment_integrations`, and `mansico_meta_integration` declare `frappe`/`erpnext` dependencies; upgrade order must respect them.
4. **Test maintained wrappers** — `visaguy_hrms`, `visaguy_raven`, `visaguy_crm`, `visaguy_frappe_crm`, `visaguy_helpdesk`, `payment_integrations` override classes/methods in the apps above; run their critical paths after upgrade.
5. **Verify payment gateway webhooks** — `payments` + `payment_integrations` (MyFatoorah/TotalPay) changes can break checkout flows.
6. **Validate India Compliance migrations** — its `before_migrate` version check can block site migration if ERPNext/Frappe versions are incompatible.
7. **Validate WhatsApp flows** — `frappe_whatsapp` and `waflo` chat-flow engine must be regression-tested end-to-end.
8. **Validate Insights dashboards** — `visaguy_crm`, `visaguy_hrms`, `the_visaguy` ship Insights fixtures; confirm data-source connectivity after upgrade.
9. **Do not install bench-only apps until needed** — `employee_self_service` and `mansico_meta_integration` should remain uninstalled unless product decision changes.
10. **Record upgrade order** — recommended sequence: `frappe` → `erpnext` → `hrms`/`payments` → `india_compliance` → remaining apps, with `bench migrate` and wrapper tests between each step.

---

*End of report.*
