# Capability Map

## Legend

- **present** — settings DocType or capability surface exists.
- **source-wired** — hooks, imports, or caller/callee relationships are evidenced.
- **configured-unverified** — config values observed as key names only; activation not verified.
- **runtime-verified** — live traffic or active configuration confirmed.

## Public eligibility and lead capture

| Capability | Status | Evidence |
|---|---|---|
| Chat-based eligibility assessment | source-wired | `visa_eligibility_checker` chat step machine |
| Voice AI interview via OpenAI Realtime | source-wired | `visa_eligibility_checker` `VoiceRealtime` |
| Frontend scoring and verdict | source-wired | `calcScore`, `ResultScreen` |
| Raw Lead creation/update | source-wired | `POST /api/resource/Raw Lead`, `PUT /api/resource/Raw Lead/{name}` |
| Qualified Lead creation when score ≥ 55 | source-wired | `POST /api/resource/Lead` fire-and-forget |
| WhatsApp CTA | source-wired | `result-screen.tsx` wa.me deep-link |

## B2B business portal

| Capability | Status | Evidence |
|---|---|---|
| OAuth2 login | source-wired | `frappe.integrations.oauth2.get_token` |
| Dashboard with wallet and order counts | source-wired | `visaguy_business_client` dashboard |
| Visa order CRUD | source-wired | `Business Client Visa Order` resource APIs |
| Applicant management | source-wired | Order detail page |
| Preliminary document generation | source-wired | `visaguy_business.functions.api.generate_preliminary_documents` |
| Process file creation | source-wired | `visaguy_business.functions.api.create_process_file` |
| Payment request and redirect | source-wired | `request_payment_for_visa_order` |
| Invoice PDF download | source-wired | `frappe.utils.print_format.download_pdf` |
| Business admin pages | source-wired | `/details`, `/users` (client-side gating) |

## Consumer website

| Capability | Status | Evidence |
|---|---|---|
| Destination browsing | source-wired | Server-fetched destination grid |
| Lead form and visa order creation | source-wired | `visaguy_website.api.create_visa_order` |
| Multi-applicant application form | source-wired | `ApplicationForm`, `useApplicationForm` |
| Dynamic file template per applicant type | source-wired | `visaguy_website.api.get_file_template` |
| File upload | source-wired | `upload_file` |
| Application submission and payment redirect | source-wired | `visaguy_website.api.submit_application` |
| OTP login | source-wired | `otp_authentication.otp_generation.user_check_otp_send` / `otp_verification` |
| Dashboard and application detail | source-wired | `/dashboard`, `/dashboard/[slug]` |
| Process details form submission | source-wired | `fileflo.data_collection.add_form_data` |

## Internal operations

| Capability | Status | Evidence |
|---|---|---|
| Process workflow engine | source-wired | `processflo` PF Process File actions/deliverables |
| Document collection and zip download | source-wired | `fileflo` form generation, data collection, download |
| Legacy CRM lead/customer lifecycle | source-wired | `visaguy_crm` hooks and server scripts |
| Modern CRM lead/deal pipeline | source-wired | `crm` fork |
| Frappe CRM migration bridge | source-wired | `visaguy_frappe_crm` hooks |
| Helpdesk tickets and KB | source-wired | `helpdesk` fork + `visaguy_helpdesk` override |
| HRMS customizations | source-wired | `visaguy_hrms` class/method overrides |
| Raven notifications | source-wired | `visaguy_raven` doc_event handlers |

## Integrations

| Capability | Status | Evidence |
|---|---|---|
| OpenAI Realtime / Chat Completions | source-wired | FastAPI companion backend |
| WhatsApp messaging | source-wired | `frappe_whatsapp`, `waflo`, `the_visaguy` |
| FCM push notifications | source-wired | `frappe_notifier` |
| Meta / Google Conversions API | source-wired | `frappe_conversions_api` |
| TotalPay / MyFatoorah payments | source-wired | `payment_integrations` |
| Upstream payment gateways | present | `payments` settings DocTypes |
| Twilio / Exotel calls | source-wired | `crm` settings and integration modules |
| OTP gateway | source-wired | `otp_authentication` |
| Zoho legacy CRM sync | source-wired | `visaguy_crm` server scripts |

## Gaps and placeholders

- Consumer `/contact` is a placeholder.
- Consumer `/careers` is linked in navigation but has no route.
- Consumer `ProcessDetailsForm` Save button simulates a delay and makes no API call.
- Business client `/oauth-callback` redirects immediately to `/login`.
