# Integrations

## Verification model

| Level | Meaning |
|---|---|
| **present** | Settings DocType or capability surface exists in source. |
| **source-wired** | Hooks, imports, or caller/callee relationships are evidenced in code. |
| **configured-unverified** | Environment/config values observed only as key names; activation not verified. |
| **runtime-verified** | Live traffic or provider call confirmed. |

This audit runtime-verified SSH access, installed apps, versions, and CLI help; it did not verify provider traffic or production workflows.

## Integration matrix

| Integration | Level | Evidence | Verification note |
|---|---|---|---|
| **OpenAI** | source-wired | FastAPI `server/routers/voice.py`, `recommendations.py`, `server/utils/openai_client.py`; eligibility frontend ephemeral secret | Browser never sees API key; provider traffic not tested. |
| **Frappe REST / RPC** | source-wired | All three frontends call `/api/resource/*` and `/api/method/*`; maintained apps expose whitelisted methods | Guest writes and API-key auth both present. |
| **OAuth / OTP** | source-wired | B2B: `frappe.integrations.oauth2.get_token`; Consumer: `otp_authentication.otp_generation.user_check_otp_send` / `otp_verification` | OAuth/OTP gateway credentials and live send/verify not tested. |
| **WhatsApp** | source-wired | `frappe_whatsapp` settings + doc_events; `waflo` flow processor/retry; `the_visaguy` lead/PF updates; eligibility/website wa.me deep-links | Provider account and inbound message flow not tested. |
| **Raven** | source-wired | Base `raven` installed; `visaguy_raven` doc_event handlers for CRM/HR/business/accounts | No whitelisted APIs listed; runtime delivery not tested. |
| **FCM push** | source-wired | `frappe_notifier_settings`; `frappe_notifier/api/token.py`, `topic.py`, `send_notification.py`; `employee_self_service` FCM keyword | Service-account placement and relay URL not inspected. |
| **Meta / Google Conversions API** | source-wired | `frappe_conversions_api/api/meta/webhook.py`; keyword hits `meta`, `google` | Provider tokens and event forwarding not tested. |
| **MyFatoorah / TotalPay** | source-wired | `payment_integrations` settings DocTypes; webhook handlers; `Payment Request` `on_update_after_submit` hook | Gateway credentials and live webhooks not tested. |
| **Upstream Payments gateways** | present | `payments` app settings: PayPal, Razorpay, PayTM, Braintree, GoCardless, Stripe, M-Pesa; checkout templates | No evidence of active configuration. |
| **Zoho (legacy CRM)** | source-wired | `visaguy_crm` server scripts reference Zoho integration and payment-from-lead flows | No settings DocType observed. |
| **Twilio / Exotel** | source-wired | `crm_twilio_settings`, `crm_exotel_settings`; `crm/integrations/twilio/api.py`, `integrations/exotel/handler.py` | Provider credentials and call flows not tested. |
| **Insights** | source-wired | `insights_settings`; fixtures shipped by `visaguy_crm`, `visaguy_hrms`, `the_visaguy` | Data-source connectivity not tested. |
| **Backups (S3 / Dropbox)** | present | `s3_backup_settings`, `dropbox_settings` in `frappe` | Actual backup jobs and retention not inspected. |
| **GST / India Compliance** | source-wired | `india_compliance` installed; `gst_settings`; overrides `Customize Form` and payment-entry method | Indian entity config and GST returns not verified. |
| **SAP** | present (keyword) | `sap` keyword in `waflo` and `the_visaguy` hooks | No integration surface identified. |

## Integration settings DocTypes

| App | Settings DocType |
|---|---|
| `frappe` | `google_settings`, `s3_backup_settings`, `dropbox_settings`, `ldap_settings`, `push_notification_settings`, `oauth_provider_settings`, `sms_settings` |
| `erpnext` | `plaid_settings`, `crm_settings`, `voice_call_settings`, `incoming_call_settings` |
| `payments` | `paypal_settings`, `razorpay_settings`, `paytm_settings`, `braintree_settings`, `gocardless_settings`, `stripe_settings`, `mpesa_settings` |
| `india_compliance` | `gst_settings` |
| `insights` | `insights_settings` |
| `raven` | `raven_settings` |
| `frappe_whatsapp` | `whatsapp_settings` |
| `crm` | `crm_twilio_settings`, `erpnext_crm_settings`, `crm_exotel_settings`, `fcrm_settings`, `crm_global_settings`, `crm_view_settings` |
| `visaguy_frappe_crm` | `crm_migration_settings` |
| `visaguy_crm` | `tvg_crm_settings` |
| `visaguy_business` | `business_client_settings` |
| `visaguy_helpdesk` | `tvg_hd_settings` |
| `visaguy_hrms` | `tvg_hr_settings` |
| `visaguy_raven` | `visaguy_raven_settings` |
| `visaguy_website` | (via `Visaguy Website Configuration`) |
| `payment_integrations` | `myfatoorah_settings`, `totalpay_settings` |
| `frappe_notifier` | `frappe_notifier_settings` |
| `otp_authentication` | `otp_settings` |
| `employee_self_service` | `employee_self_service_settings`, `ess_notification_settings` |
| `mansico_meta_integration` | `meta_facebook_settings` |
| `non_profit` | `non_profit_settings` |
| `waflo` | `wf_account_settings`, `wf_settings` |
| `fileflo` | `fileflo_settings` |

## No activation overclaims

The presence of a settings DocType or a webhook handler proves capability, not active use. None of the external-provider integrations were runtime-verified in this audit. Treat all provider integrations as **source-wired** or **present** unless a follow-up audit confirms live traffic.
