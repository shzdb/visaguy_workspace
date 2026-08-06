# 03e — Retry loss corrective

Branch: `feat/waflo-correctness`  
Defect: deferred `retry_message` looked up `{"message_id": None}`, linked an arbitrary
pending row, set `custom_retried_message` on the original → permanently excluded from
`schedule_retry_message` → silent transactional message loss.

---

## Y1 — Loss vs duplicate reasoning

When `send_whatsapp_template` is rate-limited it returns `None` and, by design, inserts a
**new** pending `WhatsApp Message` (no `message_id`, `custom_should_retry=1`).

If `retry_message` then:

| Action | Loss? | Duplicate? |
|--------|-------|------------|
| Set `custom_retried_message` via `{"message_id": None}` lookup | **Yes** (wrong row / original excluded forever) | maybe |
| Leave original eligible **and** leave the new sibling eligible | No | **Yes** (two rows in the hourly pool) |
| Leave original eligible **and** suppress the sibling from *this* defer | No | No |

**Choice:** leave the original eligible (`custom_retried_message` unset) so it stays in
`{"custom_should_retry": 1, "custom_retried_message": None}`. Suppress the sibling created
by this deferred attempt (`custom_should_retry=0` via `frappe.flags.waflo_deferred_pending_message`
side channel from `_send_whatsapp_template`). That keeps exactly one retriable row for the
logical message.

If sibling cleanup fails, prefer **not losing**: original remains retriable (duplicate risk
only if the sibling also stays eligible — logged, not fatal).

Never run `{"message_id": None}` lookup. Return `None` cleanly so
`schedule_retry_message`'s loop continues.

---

## Y4 — Round-trip table

`schedule_retry_message` loads the full doc via `frappe.get_doc(...).as_dict()` before
calling `retry_message`. Fields written by `log_pending_retry_whatsapp_message` and read
back by `retry_message`:

| Concern | Written as (log_pending) | Read back as (retry_message → send kwarg) | Match? |
|---------|--------------------------|-------------------------------------------|--------|
| body params | `body_param` (+ `template_parameters`) | `doc["body_param"]` → `body_params` | yes |
| header params | `template_header_parameters` | `doc["template_header_parameters"]` → `header_params` | yes |
| button_url_map (dynamic URL buttons) | `buttons` | `doc["buttons"]` → `button_url_map` | yes |
| use_flow (FLOW button) | `custom_is_flow` | `doc["custom_is_flow"]` → `use_flow` | yes |
| reference doctype | `reference_doctype` | `doc["reference_doctype"]` → `ref_doctype` | yes |
| reference name | `reference_name` | `doc["reference_name"]` → `ref_name` | yes |

No round-trip fix required — field names already align.

---

## Tests (`waflo/waflo/tests/test_retry_message.py`)

| Test | Asserts |
|------|---------|
| `test_deferred_retry_does_not_set_custom_retried_message` | Deferred send → no `custom_retried_message` write; original still `custom_should_retry=1` / `custom_retried_message=None`; sibling suppressed; no null `message_id` lookup |
| `test_successful_retry_links_original_to_new_message` | Successful send still links original → new via `custom_retried_message` / `custom_retried_from_message` |
| `test_successful_send_without_logged_row_leaves_original_eligible` | Truthy `message_id` but missing row → log + return; original not linked |
| `test_no_outgoing_account_raises_clear_error` | `get_whatsapp_account` → None raises clear "outgoing WhatsApp account" error (not AttributeError) |
| `test_round_trip_preserves_use_flow_and_button_url_map` | `retry_message` passes `use_flow`, `button_url_map`, body/header/ref kwargs from stored fields |

Mocks: `frappe` (incl. cache/flags), `send_whatsapp_template` / `make_post_request` /
`get_whatsapp_account` as appropriate. `FrappeTestCase` base.

---

## Also fixed

- **Y2:** Guard `get_value` miss after successful send — log and leave original eligible.
- **Y3:** Guard missing outgoing WhatsApp account before `.name` access.
- **`log_pending_retry_whatsapp_message`:** returns inserted doc name (for sibling side channel).
