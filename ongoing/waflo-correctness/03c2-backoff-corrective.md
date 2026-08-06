# 03c2 — Backoff corrective

## Removed

- `import time` and all `time.sleep` usage from `waflo/waflo/messaging/send.py`
- `_rate_limit_backoff_seconds`
- `RATE_LIMIT_MAX_RETRIES` and `_rate_limit_attempt` / `_rate_limit_delay` re-enqueue machinery
- Worker sleep + `frappe.enqueue(..., timeout=...)` used as a false delay primitive

## Record-creation approach

Chose a **sibling** helper `log_pending_retry_whatsapp_message` in `logs.py` rather than extending `log_whatsapp_message`.

Why: `log_whatsapp_message` is the post-success path and requires a real Meta `message_id`. A rate-limited send never reached the API, so there is no id; fabricating one would corrupt webhook correlation. A sibling keeps the success contract intact, omits `message_id`, sets `custom_should_retry=1`, leaves `custom_retried_message` unset, and shares `_serialize_template_fields` so payload encoding matches successful logs. Also sets `custom_rate_limited=1` as a diagnostic marker (same custom field used on inbound suppressions).

Hourly `schedule_retry_message` (unchanged) picks these up; natural bound remains `custom_retried_message: None`.

## Field-name verification checklist

Fields written for reconstruct / retry flag, verified against `retry_message.py` reads and WhatsApp Message DocType (`custom/whatsapp_message.json` field_order + custom_fields):

- [x] `to` — retry_message reads; in DocType field_order
- [x] `template` — retry_message reads; in DocType field_order
- [x] `body_param` — retry_message reads; in DocType field_order
- [x] `template_header_parameters` — retry_message reads; in DocType field_order
- [x] `buttons` — retry_message reads; in DocType field_order
- [x] `reference_doctype` — retry_message reads; in DocType field_order
- [x] `reference_name` — retry_message reads; in DocType field_order
- [x] `custom_is_flow` — retry_message reads; custom field
- [x] `custom_should_retry` — set to `1` for `schedule_retry_message` filter; custom field
- [x] `custom_retried_message` — intentionally **unset** (omitted from insert) so the hourly filter includes the row once

Also written (not required by retry_message, consistent with success log): `use_template`, `template_parameters`, `message_type`, `type`, `whatsapp_account`, `custom_rate_limited`.

No fabricated `message_id`.

## Tests now assert

Updated `test_outbound_rate_limit.py`:

1. **`test_rate_limited_transactional_send_persists_pending_retry`** — rate-limited transactional send creates a WhatsApp Message with `custom_should_retry=1`, all reconstruct fields populated, no `message_id` / no `custom_retried_message`, `make_post_request` not called, `enqueue` not called. Mocks `frappe.cache()` and `make_post_request`.
2. **`test_outbound_path_enforces_account_ceiling`** — account ceiling hit → same pending-retry persist, no API call, no enqueue (no sleep).
3. **`test_flow_path_rate_limit_false_does_not_double_increment`** — unchanged intent (rate_limit=False skips gates/increments).
4. **Removed** `test_retry_bound_is_respected` (competing counter / max re-queue attempts) and all `time.sleep` patches.

Account-ceiling unit tests for `is_account_rate_limited` / `increment_account_rate_limit` unchanged.

## Gates

- `grep -rn "time.sleep\|import time" waflo/waflo/messaging/send.py` → empty
- `python -m py_compile` on modified `.py` files → pass
- No conflict markers
