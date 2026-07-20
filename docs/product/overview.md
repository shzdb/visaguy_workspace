# Product Overview

## What VisaGuy is

VisaGuy is a Frappe v15 multi-application platform for visa services. It supports public lead capture, B2B business-client ordering, consumer e-commerce ordering, internal case/process workflows, payments, CRM, helpdesk, HRMS, and notifications.

## Primary actors and surfaces

| Actor | Surface | Repository | Authentication |
|---|---|---|---|
| Anonymous consumer | Public visa eligibility checker | `tvgglobal/visa_eligibility_checker` | None (guest Frappe writes) |
| Business admin / standard business user | B2B business portal | `tridz-dev/visaguy_business_client` | OAuth2 password grant |
| Consumer applicant | Consumer website / e-commerce | `tvgglobal/visaguy-website-client` | Email/OTP → API key/secret |
| Sales / operations / consultants | Frappe Desk / CRM / process workflows | Frappe site `visaguy` | Frappe session |
| Support agents | Helpdesk portal | Frappe site `visaguy` | Frappe session |
| Employees / HR / managers | HRMS portal | Frappe site `visaguy` | Frappe session |

## Product scope

### In scope

- Multi-zone visa eligibility assessment (chat and voice) with OpenAI Realtime.
- Public lead capture into Frappe CRM.
- B2B visa order creation, applicant management, document collection, payment requests, and invoice download.
- Consumer destination browsing, visa order creation, multi-applicant application form, file upload, and payment redirect.
- Internal process/file workflows (`processflo` + `fileflo`).
- CRM pipeline across legacy ERPNext Lead, modern Frappe CRM Lead/Deal, and migration bridge.
- Helpdesk ticketing with agent assignment.
- HR leave, timesheet, interview, expense claim, and appointment-letter workflows.
- Notifications via Raven, WhatsApp, FCM push, and email.
- Payment gateways: TotalPay, MyFatoorah, and upstream payment scaffolding.

### Out of scope (external or unverified)

- `employee_self_service` and `mansico_meta_integration` are bench-only and not installed on site `visaguy`.
- Active provider traffic (WhatsApp, Twilio/Exotel, FCM, Meta/Google Conversions API, OTP gateway, backup jobs) is not runtime-verified.
- The public consumer website does not call `visaguy_business.create_process_file`; that join is unresolved.

## Verification notes

All product capabilities listed here are **source-wired** unless explicitly marked otherwise. Live traffic, external-provider configuration, and production workflows were not verified in this audit.
