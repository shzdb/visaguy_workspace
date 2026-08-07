---
id: TASK-018
feature: FEAT-002
title: TVG Qatar — Meta WABA, number, and template approval
status: ready
repository: none (external — Meta Business Manager)
owners: []
depends_on: []
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# TVG Qatar — Meta WABA, number, and template approval

## Objective

Get everything on the Meta side ready for TVG Qatar to send WhatsApp messages, so that the moment the FEAT-002 code lands, configuration is the only remaining step.

## Why this is the first task

This is the **critical path**. It needs no code, depends on nothing else in the project, and has real external lead time — Meta template review is measured in days and is outside our control. Everything else in FEAT-002 can proceed in parallel.

It is also the only part of the Qatar rollout that can start today. See "What is blocked" below.

## Inputs

- Access to Meta Business Manager for the TVG Qatar entity.
- The Qatar business phone number to register.
- The existing seven `Visaguy UAE` templates as content reference.

## Required outputs

1. A WhatsApp Business Account (WABA) for TVG Qatar.
2. A registered, verified phone number under that WABA.
3. The credentials needed for a Frappe `WhatsApp Account` record: `token`, `url`, `version`, `phone_id`, `business_id`, `app_id`, `webhook_verify_token`.
4. Six approved templates under the Qatar WABA, matching the event types `Whatsapp Default` requires.

## Templates to submit

Content mirrors the existing UAE templates. `actual_name` — the name Meta knows — stays identical to the UAE version; only the Frappe-side record name will differ later (see the constraint below).

| Event type | Meta template name | Notes |
|---|---|---|
| Lead Form | `lead_form` | Has a dynamic URL button — the button suffix is supplied per send |
| Process Form | `process_form` | Dynamic URL button |
| Payment Success | `payment_success` | Document header (invoice PDF) |
| Payment Feedback | `payment_completion_feedback` | Image header + **FLOW button** |
| Completion Feedback | `visa_completion_feedback` | Image header + **FLOW button** |
| Default reply | `default_reply` | Image header, used by `send_default_message` |

`hello_world-en_US` is a Meta sample and does not need recreating.

The two feedback templates use WhatsApp Flows. Confirm the Flow itself is published under the Qatar WABA — a template can be approved while its Flow is not, and the send will then fail at runtime.

## Constraint carried into the next task

`WhatsApp Templates` in Frappe is autonamed `format:{template_name}-{language_code}`, and `lead_form-en` is already taken by the UAE account. Qatar's Frappe records must therefore use a zone-suffixed `template_name` with an unchanged `actual_name`:

| Frappe `template_name` | `actual_name` sent to Meta |
|---|---|
| `lead_form_qatar` | `lead_form` |
| `process_form_qatar` | `process_form` |
| `payment_success_qatar` | `payment_success` |
| `payment_completion_feedback_qatar` | `payment_completion_feedback` |
| `visa_completion_feedback_qatar` | `visa_completion_feedback` |
| `default_reply_qatar` | `default_reply` |

This convention must be applied consistently for every future zone.

## Constraints

- Do not change the `is_default_outgoing` flag on `Visaguy UAE`. Until FEAT-002's M1 lands, that flag decides where **every** message goes; flipping it would redirect UAE traffic to Qatar.
- Do not create the Frappe `WhatsApp Account` or `Whatsapp Default` records yet — that is the follow-up task, and creating them early has no effect while account routing is unimplemented.
- Record credentials in the password manager or Meta console only. **No tokens, phone IDs, or secrets in this workspace** — see `.agents/rules/project-rules.md`.

## Validation

- Meta Business Manager shows the Qatar WABA with a verified number.
- All six templates show status `APPROVED` under the Qatar WABA.
- The Flow used by the two feedback templates is published.
- Quality rating and messaging tier for the new number are noted — they feed the FEAT-003 account-ceiling value.

## Definition of done

Qatar can send WhatsApp messages from Meta's side. Nothing in Frappe has been changed.

## What is blocked until code lands

Creating a Frappe `WhatsApp Account` and a `Whatsapp Default` row for Qatar will **not** make Qatar messages send from the Qatar number. `waflo/waflo/messaging/send.py` resolves the outgoing account via `get_whatsapp_account(account_type="outgoing")` — the globally-flagged default — and `send_whatsapp_template` has no account parameter.

Configuring Qatar before FEAT-002 M1 would attempt to send Qatar's templates through the UAE WABA, where they do not exist. Meta would reject the send.

Sequence: **TASK-018 (this, now) → FEAT-003 deployed ([TASK-017](../../blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md)) → FEAT-002 code M1–M16 → Qatar Frappe configuration.**

FEAT-003 comes before the FEAT-002 code because both edit `waflo/waflo/messaging/send.py`.
