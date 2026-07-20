# Risks and Open Questions

Each item uses the workspace evidence labels defined in `AGENTS.md`: **present**, **source-wired**, **configured-unverified**, or **runtime-verified**. A label describes the evidence supporting the risk or question, not whether the risk has been resolved.

## Deployment and upgrade risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 1 | Five dirty working trees on the bench (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`) block reproducible builds. | Deployment | runtime-verified |
| 2 | Non-standard / non-version-15 branches on `crm` (`tridz-dev`), `helpdesk` (`modification_develop_branch`), `fileflo` (`fix/mandatory-file`), `otp_authentication` (`email`), plus external `insights`/`raven`/`frappe_whatsapp`/`non_profit`/`mansico_meta_integration`. | Upgrade | runtime-verified |
| 13 | Node v12 system runtime vs Node v18 socketio runtime split. | Infrastructure | runtime-verified |

## Security risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 3 | Eligibility checker performs unauthenticated guest writes to `Raw Lead`/`Lead`. | Security | source-wired |
| 4 | FastAPI CORS `allow_origins=["*"]` with credentials enabled. | Security | source-wired |
| 5 | OAuth tokens and consumer API key/secret stored in browser `localStorage`. | Security | source-wired |
| 6 | Business-client admin gating relies on client-side `sessionStorage` only. | Security | source-wired |

## Functionality and quality risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 7 | Consumer `ProcessDetailsForm` Save button simulates a delay and makes no API call. | Functionality | source-wired |
| 8 | Consumer `/contact` is placeholder; `/careers` nav link has no route. | Functionality | present |
| 9 | No automated tests in any frontend; several maintained apps have minimal tests. | Quality | present |
| 10 | Business client disables ESLint and TypeScript errors during build. | Quality | source-wired |
| 11 | Mixed lockfiles in business client (`bun.lock` + `pnpm-lock.yaml`). | Build | present |
| 12 | Hard-coded fallback API URL in `visaguy_business_client/app/orders/[id]/page.tsx:32`. | Configuration | source-wired |

## Architecture and configuration questions

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 14 | Overlapping CRM layers (`crm`, `visaguy_crm`, `visaguy_frappe_crm`) — runtime precedence unclear. | Architecture | present |
| 15 | Overlapping helpdesk layers (`helpdesk`, `visaguy_helpdesk`) — runtime precedence unclear. | Architecture | present |
| 16 | Overlapping Raven layers (`raven`, `visaguy_raven`) — runtime precedence unclear. | Architecture | present |
| 17 | Active payment gateway configuration (TotalPay / MyFatoorah / upstream gateways) not verified. | Integration | configured-unverified |
| 18 | Active WhatsApp / Twilio / Exotel / OTP / FCM provider traffic not verified. | Integration | configured-unverified |
| 19 | Active Meta / Google Conversions API event forwarding not verified. | Integration | configured-unverified |
| 20 | Backup jobs (S3 / Dropbox) and retention not verified. | Operations | configured-unverified |
| 21 | GST / India Compliance active configuration not verified. | Compliance | configured-unverified |
| 22 | Consumer website order → `PF Process File` / payment join is unresolved at the frontend source level. | Workflow | source-wired |
| 23 | `visaguy_website` does not invoke `visaguy_business.create_process_file` in the frontend evidence. | Workflow | source-wired |

## Notes

- Do not mark a `present`, `source-wired`, or `configured-unverified` question as settled without the follow-up evidence required to answer it.
- Dirty-tree diffs were intentionally not inspected; reconciliation is a prerequisite to any upgrade.
