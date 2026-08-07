# Phase 3c — Handler wiring and robustness

Branch: `feat/multi-zone-whatsapp`. Repo: `the_visaguy/` only. `waflo/` untouched.

## C1 — `whatsapp_account` wiring

**SEND_CALLS_WIRED = 5** (all live `send_whatsapp_template` calls in `handlers/whatsapp_message.py`):

| Function | Event |
|----------|-------|
| `_send_lead_form_link` | Lead Form |
| `_send_process_form_link` | Process Form |
| `_send_payment_received` | Payment Success |
| `_send_payment_received` | Payment Feedback |
| `_send_process_file_documents_delivered` | Completion Feedback |

Each passes `whatsapp_account=whatsapp_default.whatsapp_account`. Dead commented `send_default_message` block removed (C5), so it is not counted.

## C2 — Safe lookup helper (M10)

```python
def _find_child_row(rows, fieldname, value):
	"""Return the first child row where fieldname == value, or None."""
	for row in rows or []:
		if getattr(row, fieldname, None) == value:
			return row
	return None
```

Wrappers:

- `_get_event_template(whatsapp_default, event_type, zone)` → template string or `None` + warning
- `_get_feedback_default(whatsapp_default, feedback_type, zone)` → child row or `None` + warning

**INDEX_SITES_FIXED = 7** (5 `event_template` + 2 `feedback_defaults`). No `[0]` indexing remains.

## Warning messages added

| Source | Message |
|--------|---------|
| `_get_whatsapp_default` (no zone) | `Skipping WhatsApp send: document has no zone` |
| `_get_whatsapp_default` (missing record) | `Skipping WhatsApp send: no Whatsapp Default configured for zone '{zone}'` |
| `_get_event_template` | `Skipping WhatsApp send: zone '{zone}' has no event template for '{event_type}'` |
| `_get_feedback_default` | `Skipping WhatsApp send: zone '{zone}' has no feedback default for '{feedback_type}'` |
| `get_host_name` (dev, missing config) | `whatsapp_dev_host_name missing from site_config; falling back to get_url()` |
| `clean_mobile_no` | `Rejecting invalid mobile number after normalisation: {mobile_no!r}` |
| `_resolve_zone_for_feedback` / `receive_feedback` | `Skipping feedback receive: could not resolve zone from whatsapp_account=… or referenced lead` |
| `receive_feedback` (no WD for zone) | `Skipping feedback receive: no Whatsapp Default for zone '{zone}'` |

All via `frappe.logger("whatsapp").warning(...)` — not silent skips.

## C3 — Guarded `Whatsapp Default` lookups (M11)

`_get_whatsapp_default(zone)` uses `frappe.db.exists` then `get_doc`. Missing → warn + return `None`. No cross-zone substitution. All 4 former bare `get_doc` sites use this helper.

## C4 — Sales Invoice existence (M12)

`frappe.db.exists("Sales Invoice", {…})` then `get_doc` by name. The old `if not sales_invoice` path is reachable for real misses.

## C5 / C7 — Dead code / noisy logs removed

- Removed `COMPANY = "TVG"` and the commented `send_default_message` block from `whatsapp_message.py`.
- Removed per-payment `frappe.log_error` for the Sales Invoice Document and `file_url`.

## C6 — Host configuration (M14)

`TEMP_HOST_NAME` hardcode removed. In `frappe.conf.mode == "development"`, host comes from site config key `whatsapp_dev_host_name`. If unset, warns and falls back to `get_url()` (same non-dev path).

## C8 — `clean_mobile_no` (M16)

Strips `+`, spaces, dashes, parentheses. Returns `None` (and warns) if result is empty, non-digits, shorter than 8, or longer than 15. No country-code rewriting. Callers skip send when cleaned mobile is falsy.

## C9 — Zone-aware feedback (F1)

`_resolve_zone_for_feedback(doc)` order:

1. `doc.whatsapp_account` → `Whatsapp Default` with matching `whatsapp_account` → `zone`
2. Else `reply_to_message_id` → outbound `WhatsApp Message` → Lead/CRM Lead `custom_zone`

Then `parent = Whatsapp Default.name` for that zone (autoname is `field:zone`). Feedback Defaults looked up with that parent. If neither resolves → skip + warn. **No TVG default.**

## Tests (`the_visaguy/tests/test_whatsapp_handlers.py`)

| Test | Asserts |
|------|---------|
| `test_send_passes_zone_whatsapp_account` | `_send_lead_form_link` calls `send_whatsapp_template` with `whatsapp_account="WA-Qatar"` and cleaned mobile |
| `test_missing_event_template_logs_and_skips` | `_get_event_template` returns `None`, warns naming zone + event, does not raise |
| `test_missing_whatsapp_default_logs_and_skips` | `_get_whatsapp_default` returns `None`, warns naming zone, does not raise |
| `test_resolves_zone_from_inbound_whatsapp_account` | Account → zone lookup |
| `test_feedback_uses_zone_b_parent_not_tvg` | `Whatsapp Feedback Defaults` parent is `TVG Qatar`, not `TVG` |
| `test_strips_spaces_dashes_parentheses_and_plus` | Formatting chars stripped |
| `test_rejects_obviously_invalid` | Non-digit / too-short / empty → `None` |

`send_whatsapp_template` is mocked — no network. Tests are written; **not claimed to pass** under `bench`.

## Uncertain

- Site config key name `whatsapp_dev_host_name` is new; operators must set it in development `site_config.json` (replaces the removed hardcode).
- `clean_mobile_no` length bounds (8–15) are conservative E.164-ish guesses; may need tuning if real numbers fall outside.
- Feedback zone fallback only considers Lead / CRM Lead references (not other doctypes).
