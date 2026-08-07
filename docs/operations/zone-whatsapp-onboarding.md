# Onboarding a Zone to WhatsApp

How to configure a new zone — TVG Qatar first — to send its own WhatsApp auto messages and feedback messages.

**Prerequisite: FEAT-002 must be deployed.** Before it is, `waflo` resolves a single globally-flagged outgoing account and ignores per-zone configuration entirely. Configuring a zone early has no effect, and would push that zone's templates through the wrong WhatsApp Business Account — where they do not exist, so Meta rejects the send. See [FEAT-002](../../features/ongoing/multi-zone-whatsapp/README.md).

Keyed on **Zone**, not Company. Zone is the customer-facing market; Company is the employing legal entity. `TVG India` is back office — it serves other zones, has no zone of its own, and needs no WhatsApp configuration. See [ADR-006](../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) and [ADR-007](../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md).

## Step 1 — Meta side

Covered by [TASK-018](../../tasks/ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md). This has real external lead time; start it first.

- A WhatsApp Business Account (WABA) for the zone's legal entity.
- A registered, verified phone number.
- Six approved templates (see step 3).
- The Flow used by the two feedback templates **published** under the new WABA. A template can pass review while its Flow is not, and the failure only appears at send time.
- Note the number's quality rating and messaging tier — they inform the FEAT-003 account ceiling.

## Step 2 — `WhatsApp Account` record

Create one in Frappe with the credentials from step 1: `account_name`, `token`, `url`, `version`, `phone_id`, `business_id`, `app_id`, `webhook_verify_token`, `status = Active`.

**Do not set `is_default_outgoing` or `is_default_incoming`.** Those flags belong to the existing primary account. Setting them would redirect every zone's traffic to the new number.

Record credentials in the password manager, never in this workspace.

## Step 3 — Template records

Meta approves templates per WABA, so each zone needs its own `WhatsApp Templates` records.

**Name collision.** `WhatsApp Templates` is autonamed `format:{template_name}-{language_code}`, and `lead_form-en` is already taken by the primary account. Use a zone-suffixed `template_name` with an **unchanged** `actual_name` — `actual_name` is what `send.py` puts in the Meta payload, so Meta never sees the suffix.

| `template_name` | `actual_name` | Notes |
|---|---|---|
| `lead_form_<zone>` | `lead_form` | Dynamic URL button |
| `process_form_<zone>` | `process_form` | Dynamic URL button |
| `payment_success_<zone>` | `payment_success` | Document header (invoice PDF) |
| `payment_completion_feedback_<zone>` | `payment_completion_feedback` | Image header + FLOW button |
| `visa_completion_feedback_<zone>` | `visa_completion_feedback` | Image header + FLOW button |
| `default_reply_<zone>` | `default_reply` | Image header; used for inbound replies |

Set `whatsapp_account` on each record to the account from step 2, and `language_code` to the approved language — the send path now reads the language from the template rather than assuming English.

## Step 4 — `Whatsapp Default` record

One per zone.

| Field | Value |
|---|---|
| `zone` | the Zone (this is the record's name) |
| `whatsapp_account` | the account from step 2 |
| `enabled` | leave **off** until everything below is filled in |
| `introduction_image`, `helpline_number` | zone-specific |
| `event_template` | five rows — see below |
| `feedback_defaults` | two rows with header images |

Required `event_template` rows — **all five**:

`Lead Form`, `Process Form`, `Payment Success`, `Payment Feedback`, `Completion Feedback`

`Visa Completion` is **not** required. That message goes out together with the completion feedback message; there is no separate send.

Required `feedback_defaults` rows — **both**: `Payment Feedback`, `Completion Feedback`, each with a header image.

Only then tick `enabled`. Saving an enabled record with anything missing is rejected, and the error names exactly what is absent. Configuration is **never inherited** from another zone — a zone sending another zone's templates through its own number would be rejected by Meta anyway, since templates are per-WABA.

## Step 5 — Verify before real traffic

1. Confirm the zone's `Whatsapp Default` saves with `enabled` ticked — that alone proves the configuration is complete.
2. Trigger one auto message for a test lead in that zone. Check the resulting `WhatsApp Message` record shows the **zone's** `whatsapp_account`, not the primary one.
3. Send an inbound message to the zone's number and confirm the default reply comes back **from that same number**.
4. Trigger a feedback message and confirm the reply is matched against the zone's feedback configuration.
5. Check the Error Log for warnings naming the zone — a misconfigured zone now logs rather than failing silently.

## Failure modes and what they mean

| Symptom | Cause |
|---|---|
| Save rejected naming missing rows | Step 4 incomplete. The message lists exactly what to add. |
| Throws "WhatsApp Account ... was not found" | `whatsapp_account` on `Whatsapp Default` names a record that does not exist. Deliberate — it refuses to fall back to the default account rather than message a customer from the wrong number. |
| Meta rejects the send, template not found | The template's `actual_name` is not approved under **that account's** WABA. Check step 3. |
| Message sends from the wrong number | The zone's `Whatsapp Default` has no `whatsapp_account` bound, or the lead's `custom_zone` is unset. Check the Error Log. |
| Nothing sends, no error | Check `enabled` on the zone's record, and the customer's `custom_enable_whatsapp_notifications`. |
| Message delayed by up to an hour | Rate limited and deferred to the hourly retry. Never dropped. See FEAT-003 and `max_replies_per_window`. |

## What is not covered

- **Inbound webhook routing** already resolves by `phone_id`, so it needs no per-zone change.
- **Event types are fixed.** Adding a new event type still requires a code change; the extensible event-type model was deferred from FEAT-002.
- **One account per zone.** Multiple numbers for a single zone are explicitly out of scope.
