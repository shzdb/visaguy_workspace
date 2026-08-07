# Phase 3a — waflo account routing

Branch `feat/multi-zone-whatsapp`. Local commit only.

## New signatures

```python
def send_whatsapp_template(
	mobile,
	template_name,
	body_params=None,
	header_params=None,
	button_url_map=None,
	ref_doctype=None,
	ref_name=None,
	use_flow=False,
	queue=False,
	rate_limit=True,
	whatsapp_account=None,  # NEW — account NAME (str), end of signature
):
```

```python
def _send_whatsapp_template(
	mobile,
	template_name,
	body_params=None,
	header_params=None,
	button_url_map=None,
	ref_doctype=None,
	ref_name=None,
	use_flow=False,
	rate_limit=True,
	whatsapp_account=None,  # NEW
):
```

Existing callers that omit `whatsapp_account` keep default-outgoing behaviour.

## Threading points

| # | Location | Change |
|---|----------|--------|
| 1 | `send_whatsapp_template` signature | `whatsapp_account=None` at end |
| 2 | `queue=True` → `frappe.enqueue(...)` | **passes `whatsapp_account=whatsapp_account`** (verified by reading; without this, queued sends would silently drop the account) |
| 3 | `queue=False` direct call | passes `whatsapp_account=whatsapp_account` into `_send_whatsapp_template` |
| 4 | `_send_whatsapp_template` signature | `whatsapp_account=None` at end |
| 5 | Resolution block | named account → load that doc; else `get_whatsapp_account(account_type="outgoing")` |
| 6 | `log_pending_retry_whatsapp_message` / `log_whatsapp_message` | unchanged signatures; both receive `whatsapp_account.name` of the **resolved** account used for the send |
| 7 | `retry_message` | `whatsapp_account=doc.get("whatsapp_account")` |
| 8 | `process_whatsapp_message` (3 send sites) | `whatsapp_account=whatsapp_account` (existing param) |
| 9 | `send_default_message` | `whatsapp_account=doc.whatsapp_account` |

## Account name resolve / validate

When `whatsapp_account` is a non-empty string:

1. `frappe.db.exists("WhatsApp Account", account_name)`
2. If missing → `frappe.throw(...)` with a clear message that includes the name and states we refuse to fall back to the default outgoing account.
3. If present → `frappe.get_doc("WhatsApp Account", account_name)` and use that doc for token, URL, phone_id, logging, and rate-limit keys.

When omitted / `None`: identical to prior behaviour — `get_whatsapp_account(account_type="outgoing")`, throw if none configured.

## Language (M3)

After resolving `actual_name`:

```python
language_code = (
	frappe.db.get_value("WhatsApp Templates", template_name, "language_code") or "en"
)
```

Payload uses `"language": {"code": language_code}`. Hard-coded `"en"` removed.

## A5 — retry_message

`WhatsApp Message` already stores `whatsapp_account`. `retry_message` now passes `doc.get("whatsapp_account")` into `send_whatsapp_template`. A deferred Qatar message retries from the Qatar account, not the UAE default.

## A6 — processor inbound

- `process_whatsapp_message` already accepted `whatsapp_account`; all three `send_whatsapp_template` calls now pass it.
- Live path `send_default_message` (flow engine off) now passes `whatsapp_account=doc.whatsapp_account`.

## Tests (`waflo/waflo/tests/test_account_routing.py`)

| Test | Asserts |
|------|---------|
| `test_explicit_account_used_instead_of_default` | Named account loaded via exists/get_doc; `get_whatsapp_account` not called; POST URL uses that phone_id; `log_whatsapp_message` gets that account name |
| `test_unknown_account_fails_without_default_fallback` | Missing name throws (message mentions name + refuse fallback); default resolver and POST never called |
| `test_queue_enqueue_passes_whatsapp_account` | `frappe.enqueue` kwargs include `whatsapp_account`; `_send` not called synchronously |
| `test_retry_passes_stored_whatsapp_account` | `retry_message` forwards stored `whatsapp_account` to `send_whatsapp_template` |
| `test_send_default_message_passes_inbound_account` | Live default-reply path passes `doc.whatsapp_account` |
| `test_process_whatsapp_message_passes_inbound_account` | Flow new-conversation send gets the inbound account |
| `test_template_language_code_used_in_payload` | Meta payload language is template's `language_code` (`ar`) |
| `test_language_code_falls_back_to_en` | Empty/missing `language_code` → `"en"` |

Mocks: `frappe.cache()`, `make_post_request`, `frappe.enqueue`, account lookups (`exists`/`get_doc`/`get_whatsapp_account`). `FrappeTestCase`. Tests were **not** run via `bench`.

## Gates

- `python -m py_compile` on all modified `.py` → **pass**
- `queue=True` branch threads `whatsapp_account` → **yes** (read-verified)
- No conflict markers
- `git -C ../the_visaguy status --porcelain` → empty

## Uncertain

none
