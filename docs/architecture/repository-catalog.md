# Repository Catalog

This catalog lists all 33 repositories: 30 Frappe bench apps and 3 frontend repositories.

Counts verified against the remote bench on 2026-08-06.

## Counts

- Total repositories: 33
- Bench apps: 30
- Site-installed on `visaguy`: 28
- Bench-only (not installed): 2 (`employee_self_service`, `mansico_meta_integration`)
- Internally maintained: 19
- External/upstream: 11
- Maintained forks: 2 (`crm`, `helpdesk`)
- Frontend repositories: 3

## Sites

The bench hosts two sites:

| Site | Apps | Purpose |
|---|---|---|
| `visaguy` | 28 | Primary site |
| `visa-tracker-test.localhost` | 8 (`frappe`, `erpnext`, `crm`, `insights`, `processflo`, `fileflo`, `the_visaguy`, `passport_extractor`) | Test site for FEAT-001 |

## Frappe bench apps

| # | App | Owner / Remote | Class | Installed | Version / HEAD | Role |
|---|---|---|---|---|---|---|
| 1 | `frappe` | Frappe Technologies / `frappe/frappe` | external | Yes | 15.113.0 / `01ea89c4e6` | Core framework, desk, auth, scheduler, files |
| 2 | `erpnext` | Frappe Technologies / `frappe/erpnext` | external | Yes | 15.106.0 / `4dd9f0b255` | ERP backbone: accounts, selling, CRM base, stock |
| 3 | `hrms` | Frappe Technologies / `frappe/hrms` | external | Yes | 15.45.2 / `5b3285fa` | HR, payroll, leaves, expenses, projects |
| 4 | `payments` | Frappe Technologies / `frappe/payments` | external | Yes | 0.0.1 / `68b54a7` | Payment gateway scaffolding |
| 5 | `india_compliance` | Resilient Tech / `resilient-tech/india-compliance` | external | Yes | 15.18.0 / `bde15f48` | Indian GST and audit-trail compliance |
| 6 | `insights` | Frappe Technologies / `frappe/insights` | external | Yes | 2.2.14 / `c9af45d` | Embedded analytics and dashboards |
| 7 | `raven` | The Commit Company / `The-Commit-Company/raven` | external | Yes | 2.7.1 / `dfde9b1e` | Team messaging and document notifications |
| 8 | `frappe_whatsapp` | Shridhar Patil / `shridarpatil/frappe_whatsapp` | external | Yes | 1.0.12 / `27f3438` | WhatsApp Business API integration |
| 9 | `non_profit` | Frappe / `frappe/non_profit` | external | Yes | 0.0.1 / `ea2c88d` | Memberships, donations, non-profit modules |
| 10 | `employee_self_service` | Nesscale Solutions / `nesscale-com/employee_self_service` | external | **No** | 2.1.29 / `f3c1e43` | Mobile ESS / HR self-service (bench-only) |
| 11 | `mansico_meta_integration` | Ahmed Mansy / `Ahmed-Mansy-Mansico/mansico_meta_integration` | external | **No** | 1.2.1 / `8e595ea` | Meta/Facebook lead sync (bench-only) |
| 12 | `crm` | `tridz-dev/frappe-crm` | maintained fork | Yes | 2.0.0-dev / `b3328bc9` | Modern CRM UI, lead/deal pipeline |
| 13 | `helpdesk` | `tridz-dev/helpdesk_frk` | maintained fork | Yes | 0.10.0 / `a671e5f` | Customer support tickets and KB |
| 14 | `fileflo` | `tridz-dev/FileFlo` | original | Yes | 0.0.1 / `c7244a4` | Document forms, file collection, zip downloads |
| 15 | `processflo` | `tridz-dev/ProcessFlo` | original | Yes | 0.0.1 / `2f2b565` | Process workflow engine for visa cases |
| 16 | `quick_kanban` | `tridz-dev/quick_kanban` | original | Yes | 0.0.1 / `8ca57a6` | Enhanced Vue-based Kanban view |
| 17 | `the_visaguy` | `tvgglobal/the_visaguy` | original | Yes | 0.0.1 / `e690b5b` | Core VisaGuy domain: leads, destinations, WhatsApp feedback |
| 18 | `waflo` | `tridz-dev/waflo` | original | Yes | 0.0.1 / `2167958` | WhatsApp conversational flow engine |
| 19 | `frappe_conversions_api` | `tridz-dev/frappe_conversions_api` | integration | Yes | 0.0.1 / `3a240c6` | Meta/Google Conversions API event forwarding |
| 20 | `frappe_notifier` | `tridz-dev/frappe_notifier` | integration | Yes | 0.0.1 / `8da7603` | FCM push notifications via Frappe Relay |
| 21 | `otp_authentication` | `tridz-dev/otp_authentication` | integration | Yes | 0.0.1 / `f4409ba` | OTP generation/verification for consumer portal |
| 22 | `payment_integrations` | `tridz-dev/payment_integrations` | integration | Yes | 0.0.1 / `c424a1b` | Custom TotalPay/MyFatoorah gateways |
| 23 | `visaguy_business` | `tridz-dev/visaguy_business` | integration | Yes | 0.0.1 / `301dbee` | B2B portal ordering, wallet, invoices |
| 24 | `visaguy_crm` | `tridz-dev/visaguy_crm` | integration | Yes | 0.0.1 / `1b28a82` | Legacy operational CRM around ERPNext Lead |
| 25 | `visaguy_frappe_crm` | `tridz-dev/visaguy_frappe_crm` | integration | Yes | 0.0.1 / `a1e22da` | Frappe CRM customization and migration bridge |
| 26 | `visaguy_helpdesk` | `tridz-dev/visaguy_helpdesk` | integration | Yes | 0.0.1 / `1692b38` | Customization layer over Frappe Helpdesk |
| 27 | `visaguy_hrms` | `tridz-dev/visaguy_hrms` | integration | Yes | 0.0.1 / `94d341a` | HRMS customizations: leave, timesheet, interviews |
| 28 | `visaguy_raven` | `tridz-dev/visaguy_raven` | integration | Yes | 0.0.1 / `330fa1b` | Raven notification orchestration |
| 29 | `visaguy_website` | `tvgglobal/visaguy_website` | integration | Yes | 0.0.1 / `1466adf` | Consumer website/e-commerce backend |
| 30 | `passport_extractor` | `tridz-dev/passport_extractor` | original | Yes | 0.0.1 / `0216829` | Reusable passport OCR/MRZ extraction and history (FEAT-001) |

## Frontend repositories

| # | Repository | Owner / Remote | Class | Framework | HEAD / Date | Role |
|---|---|---|---|---|---|---|
| 31 | `visa_eligibility_checker` | `tvgglobal/visa_eligibility_checker` | frontend | React 19 + Vite 7 | `2d46af4e` / 2026-06-25 | Public eligibility and lead capture |
| 32 | `visaguy_business_client` | `tridz-dev/visaguy_business_client` | frontend | Next.js 15.2.8 | `6c3d365a` / 2026-03-27 | B2B business portal |
| 33 | `visaguy-website-client` | `tvgglobal/visaguy-website-client` | frontend | Next.js 15.3.5 | `3b066f6b` / 2025-08-10 | Consumer website/e-commerce |

Frontend HEADs are as recorded during the 2026-07 reconnaissance. **None of the three frontend repositories is currently cloned on the active workstation**, so these values have not been re-verified since. A fourth frontend, `visa_tracker`, is planned by FEAT-001 but does not exist yet.

## Dirty working trees

The following repositories have uncommitted changes. Their diffs were not inspected.

- `insights` (external, installed)
- `mansico_meta_integration` (external, bench-only)
- `processflo` (internal, installed)
- `visaguy_frappe_crm` (internal, installed)
- `visaguy_raven` (internal, installed)

## Non-standard branches

Verified 2026-08-06.

- `crm`: `tridz-dev`
- `helpdesk`: `modification_develop_branch`
- `fileflo`: `feat/visa-tracker` (was `fix/mandatory-file`; moved by FEAT-001)
- `passport_extractor`: `feat/visa-tracker`
- `otp_authentication`: `email`
- `insights`: `main`
- `raven`: `main`
- `frappe_whatsapp`: `master`
- `non_profit`: `develop`
- `mansico_meta_integration`: `master`

## FEAT-001 feature branches

Three repositories carry unmerged `feat/visa-tracker` work, all pushed to upstream as of 2026-08-06. Merging is manual and owner-only — see [TASK-011](../../tasks/blocked/visa-tracking/TASK-011-staging-and-live-deployment.md).

| Repository | Branch head | Checked out on bench? |
|---|---|---|
| `the_visaguy` | `8254f93` | No — bench is on `main` |
| `fileflo` | `c7244a4` | Yes |
| `passport_extractor` | `0216829` | Yes |

Because `the_visaguy` is checked out on `main`, the visa tracking code is **not active** on site `visaguy`.

## Source evidence

- Bench app inventory: `archive/visaguy-workspace-initialization/01b-remote-bench.md`, re-verified live 2026-08-06.
- Frontend inventory: `archive/visaguy-workspace-initialization/01a-local-frontends.md` (not re-verified; repositories not cloned locally).
