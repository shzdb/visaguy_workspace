# WhatsApp Manual Test Plan — `visaguy` dev site

For manually validating FEAT-002 (multi-zone routing) and FEAT-003 (rate limiting, retry, hardening) before they are merged.

Site: `visaguy` on `erpcode.tridz.in` — a **development** site.

## Verification findings (read before testing)

I re-read the implementation on the feature branches. Two things will affect what you observe.

### FIND-1 — a lead with no zone raises instead of skipping

`is_enabled(zone, customer)` calls `frappe.throw("Zone is required")` when zone is empty, and it runs **before** the graceful `_get_whatsapp_default` guard that logs and skips.

So a lead with `custom_zone` unset produces a **background job failure in the Error Log**, not a clean warning. Everything else in the path skips-and-warns as designed; this one path is inconsistent.

Not dangerous — the send is enqueued, so the throw is contained and logged, and no message goes out. But when you run T-E1 below, expect an Error Log entry rather than a warning. Worth a small follow-up fix.

### FIND-2 — the payment event sends two messages back to back

`_send_payment_received` sends the invoice message and then the payment-feedback message in the same worker run. With `max_replies_per_window = 3` and `window_seconds = 30`, that consumes **two-thirds of the budget for that recipient in one go**.

Add a form link within the same 30 seconds and you hit the limit — the third message defers to the hourly retry. This is the behaviour risk recorded as risk #41, and T-R3 exercises it deliberately.

### Verified clean

- All five `send_whatsapp_template` calls pass `whatsapp_account=whatsapp_default.whatsapp_account`.
- All 7 previous `[...][0]` index sites now use `_get_event_template` / `_get_feedback_default`, which log a warning naming the zone and return `None`.
- All 4 `Whatsapp Default` lookups go through `_get_whatsapp_default`, which checks existence first.
- `_send_payment_received` uses `frappe.db.exists` for the Sales Invoice — the previously unreachable `if not sales_invoice` dead code is gone.
- `clean_mobile_no` handles `None`, strips `+ - ( ) space`, and rejects anything not 8–15 digits with a logged warning.
- An unknown `whatsapp_account` name raises and explicitly refuses to fall back to the default.

---

## Part 1 — What is already configured

Captured from the site on 2026-08-06.

| Item | Value |
|---|---|
| `waflo` | `feat/multi-zone-whatsapp` @ `f81fe81`, clean |
| `the_visaguy` | `feat/multi-zone-whatsapp` @ `aa3ef89`, clean |
| `frappe_whatsapp` | `master` @ `27f3438` (not pulled), backup at `master_backup` |
| `WhatsApp Account` | **1** — `Visaguy UAE`, `phone_id 222666294254982`, default in **and** out, Active |
| `WhatsApp Templates` | **7**, all bound to `Visaguy UAE`, all APPROVED |
| `Whatsapp Default` | **1** — zone `TVG`, account `Visaguy UAE`, enabled, 5 event templates + 2 feedback defaults |
| `WF Account Settings` | `Visaguy UAE` — rate limiting **on**, **3 per 30s**, default template `default_reply-en` |
| `WF Settings` | `enable_flow_engine = 0`, `inactive_timeout = 0` |
| `Zone` | `TVG`, `TVG Qatar`, `TVG Saudi` |

Migration already applied: `Whatsapp Default` is keyed on `zone`, with `company` retained read-only.

## Part 2 — What you need to configure

### 2a. To test multi-zone routing WITHOUT a Meta account for Qatar

You do **not** need a second WhatsApp Business Account to prove routing works.

Create a second `WhatsApp Account` record reusing the **same** `phone_id`, `token`, `url`, `version` as `Visaguy UAE`:

| Field | Value |
|---|---|
| `account_name` | `Test Zone B` |
| `phone_id`, `token`, `url`, `version` | copy from `Visaguy UAE` |
| `is_default_outgoing` / `is_default_incoming` | **leave unticked** |
| `status` | Active |

Messages still physically leave from the UAE number — but the **code path is fully exercised**, and `WhatsApp Message.whatsapp_account` will record `Test Zone B`. That is the assertion that matters: it proves routing selects the bound account rather than the global default.

Then create a `Whatsapp Default` for zone **`TVG Saudi`**:

- `zone` = `TVG Saudi`, `whatsapp_account` = `Test Zone B`
- All five event templates (reuse the existing `*-en` template records — they are bound to `Visaguy UAE`, which is fine for this test since both accounts point at the same number)
- Both feedback defaults with header images
- Tick `enabled` **last**

> Delete `Test Zone B` and the `TVG Saudi` record when finished, so they are not mistaken for real configuration.

### 2b. To test real Qatar sending

Requires [TASK-018](../../tasks/ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md) first: Qatar WABA, verified number, six approved templates with zone-suffixed `template_name` and unchanged `actual_name`. Then follow [`zone-whatsapp-onboarding.md`](zone-whatsapp-onboarding.md).

### 2c. Prerequisites for any test

- Redis must be running (ports 13008 / 12008 / 11008). Start with `redis-server config/redis_*.conf` from `~/bench` if `bench migrate` complains.
- **A worker must be running** — nearly every send is enqueued with `enqueue_after_commit=True`. Without `bench worker`, nothing sends and nothing appears in the Error Log. This is the single most likely reason a test appears to "do nothing".
- A test Customer with `custom_enable_whatsapp_notifications` ticked.
- A test CRM Lead with `custom_zone`, `custom_customer_id`, `mobile_no` (your own number), `first_name`.

---

## Part 3 — Test cases

Check `WhatsApp Message` records and the Error Log after each. The key column throughout is **`whatsapp_account`**.

### Group A — Zone routing (the core of FEAT-002)

| # | Scenario | Steps | Expected |
|---|---|---|---|
| **T-A1** | TVG lead sends from UAE account | Lead with `custom_zone = TVG`; set `custom_file_request_link_sent` | `WhatsApp Message` created, `whatsapp_account = Visaguy UAE`, template `lead_form-en`, button URL `/form/<id>` |
| **T-A2** | Zone B lead sends from Zone B account | Same, `custom_zone = TVG Saudi` | `whatsapp_account = **Test Zone B**`. **This is the headline assertion.** |
| **T-A3** | No regression for TVG | Repeat T-A1 after T-A2 | Still `Visaguy UAE` |
| **T-A4** | **Back-office isolation** | Lead with `custom_zone = TVG` **and** `custom_company = TVG India` | Sends from **`Visaguy UAE`** (zone wins). This is the case that would have broken had config been keyed on Company — see [ADR-006](../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) |
| **T-A5** | Unconfigured zone | Lead with `custom_zone = TVG Qatar` (no `Whatsapp Default` yet) | **No** message. Error Log/warning: `no Whatsapp Default configured for zone 'TVG Qatar'`. Must **not** fall back to UAE. |

### Group B — Configuration validation (M9)

| # | Scenario | Steps | Expected |
|---|---|---|---|
| **T-B1** | Enable with a missing event template | On the `TVG Saudi` record, delete the `Payment Success` row, tick `enabled`, save | **Save rejected.** Error names `event template for 'Payment Success'` |
| **T-B2** | Enable with no account bound | Clear `whatsapp_account`, tick `enabled`, save | Rejected, naming `WhatsApp Account binding` |
| **T-B3** | Enable with a missing feedback default | Delete the `Completion Feedback` feedback row, save enabled | Rejected, naming `feedback default for 'Completion Feedback'` |
| **T-B4** | Disabled record may be incomplete | Untick `enabled`, remove a row, save | **Saves fine** — validation only applies when enabled |
| **T-B5** | `Visa Completion` is not required | Confirm no `Visa Completion` row exists on TVG; save enabled | Saves fine. It ships with completion feedback; nothing demands it |
| **T-B6** | Zone uniqueness | Create a second `Whatsapp Default` with `zone = TVG` | Rejected — `zone` is unique, and it is the record name |

### Group C — Missing / malformed data (edge cases)

| # | Scenario | Expected |
|---|---|---|
| **T-C1** | Lead with **no** `custom_zone` | ⚠️ **Error Log entry** `Zone is required`, no message. See FIND-1 — inconsistent with the skip-and-warn elsewhere |
| **T-C2** | Zone configured but `enabled = 0` | No message, no error. Silent by design |
| **T-C3** | Customer has `custom_enable_whatsapp_notifications` unticked | No message — customer preference wins over zone config |
| **T-C4** | Lead with no `mobile_no` and no `whatsapp_no` | No message, no crash. `clean_mobile_no` returns `None` and the handler returns |
| **T-C5** | Malformed mobile, e.g. `abc123` or `+971 5` | No message. Warning: `Rejecting invalid mobile number after normalisation` |
| **T-C6** | Mobile with formatting: `+971 (50) 123-4567` | **Sends.** Normalised to digits only |
| **T-C7** | Lead with no primary applicant row | Returns early, no message, no crash |
| **T-C8** | `Whatsapp Default` names a non-existent `whatsapp_account` | **Throws** `WhatsApp Account '<name>' was not found` and explicitly does **not** fall back. Deliberate |
| **T-C9** | Template record missing from `WhatsApp Templates` | Throws naming the template — no null-name payload reaches Meta |

### Group D — Rate limiting and retry (FEAT-003)

Current config: **3 per 30 seconds per recipient**, on account `Visaguy UAE`.

| # | Scenario | Steps | Expected |
|---|---|---|---|
| **T-D1** | Under the limit | Trigger 2 messages to one number within 30s | Both send immediately |
| **T-D2** | Exceed the limit | Trigger 4 messages to one number within 30s | First 3 send. The 4th creates a `WhatsApp Message` with **`custom_should_retry = 1`, `custom_rate_limited = 1`, and no `message_id`**. **Never dropped.** |
| **T-D3** | Deferred message is retried | After T-D2, run `bench --site visaguy execute waflo.waflo.doctype.wf_settings.wf_settings.schedule_retry_message` | The deferred message sends. `custom_retried_message` set on the original. **The retry must go out on the same `whatsapp_account`** |
| **T-D4** | Retry preserves FLOW button | Force a rate limit on a **feedback** message, then retry | The retried message still carries its FLOW button. `custom_is_flow` round-trips |
| **T-D5** | Window resets | Wait 30s after T-D2, send again | Sends immediately — the counter expired |
| **T-D6** | Separate budgets per recipient | Send 3 to number A, then 1 to number B | B's message sends — the key is `(account, mobile)` |
| **T-D7** | Account ceiling is inert | Confirm `max_sends_per_window` is blank on `WF Account Settings` | No account-level blocking. Blank means disabled |
| **T-D8** | Payment burst | Trigger a payment-received event (2 messages), then a form link within 30s | 3rd message defers. See FIND-2 — this is the realistic collision |

### Group E — Inbound and feedback

| # | Scenario | Expected |
|---|---|---|
| **T-E1** | Inbound message to the number | Default reply sent using `WF Account Settings.default_template`, **from the account the message arrived on** |
| **T-E2** | Inbound rate limited | Send 4+ inbound quickly | Later inbound messages marked `custom_rate_limited = 1`, no reply. Inbound **is** dropped, unlike outbound |
| **T-E3** | Feedback reply resolves by zone | Reply to a feedback flow message | Resolved via inbound `whatsapp_account` → `Whatsapp Default` → zone. Feedback recorded against the **correct zone**, not hardcoded TVG |
| **T-E4** | Feedback with unresolvable zone | Inbound flow reply on an account with no `Whatsapp Default` | Skipped with a warning. **Must not** default to TVG |
| **T-E5** | Flow engine stays off | Confirm `WF Settings.enable_flow_engine = 0` | Inbound goes to `send_default_message`. **Do not enable it** — the engine is untested (FEAT-004) |

### Group F — Regression on existing behaviour

| # | Scenario | Expected |
|---|---|---|
| **T-F1** | Lead form link | Correct `/form/<id>` button URL |
| **T-F2** | Process form link | Correct `/form/<process_form_id>` button URL |
| **T-F3** | Payment success | Invoice PDF as document header; link is publicly reachable |
| **T-F4** | Payment feedback | Image header + FLOW button; opens the Flow |
| **T-F5** | Completion feedback | Fires on `PF Process File` → `Documents Delivered`, reference type `CRM Lead`/`Lead` |
| **T-F6** | Error Log is quiet | After a normal send | **No** per-button debug entries, **no** Sales Invoice document dumps — both were removed |
| **T-F7** | Template language | Check the outgoing payload | Language comes from the template's `language_code`, not hardcoded `en` |

---

## Part 4 — How to observe

```bash
bench --site visaguy execute frappe.client.get_list --kwargs '{"doctype":"WhatsApp Message","filters":{"type":"Outgoing"},"fields":["name","to","template","whatsapp_account","message_id","custom_should_retry","custom_rate_limited","custom_is_flow"],"order_by":"creation desc","limit_page_length":10}'
```

Warnings go to `frappe.logger("whatsapp")` → `~/bench/logs/`. Errors go to the Error Log DocType.

```bash
tail -f ~/bench/logs/worker.error.log
```

## Part 5 — What this plan cannot prove

- **Real two-number sending.** T-A2 proves the code selects the right account; with both accounts sharing a `phone_id`, messages still leave from the same physical number. Only TASK-018 + real Qatar credentials prove true isolation.
- **Meta-side template rejection** when a template is not approved under the sending account's WABA — needs two real WABAs.
- **Concurrency.** T-D2 is sequential; the atomic `INCR` limiter is not exercised under genuine parallel workers.

## Part 6 — Reverting the test setup

1. Delete the `TVG Saudi` `Whatsapp Default` record.
2. Delete the `Test Zone B` `WhatsApp Account`.
3. Confirm `Visaguy UAE` still has `is_default_outgoing = 1` and `is_default_incoming = 1`.
4. Clear stale rate-limit counters if needed: `bench --site visaguy execute frappe.cache.delete_keys --kwargs '{"key":"waflo:rl:"}'`, or simply wait out the 30-second window.
5. Delete test `WhatsApp Message` rows if they would confuse later analysis.
