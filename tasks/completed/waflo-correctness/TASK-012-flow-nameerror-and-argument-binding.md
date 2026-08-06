---
id: TASK-012
feature: FEAT-003
title: Fix flow NameError and keyword-bind template sends
status: completed
repository: waflo
owners: []
depends_on: []
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Fix flow NameError and keyword-bind template sends

## Objective

Fix D1 and N1 — the two defects that make the conversational flow engine unusable.

## Required behaviour

- `process_whatsapp_message` must receive the WhatsApp account explicitly from its caller instead of referencing an unbound `doc`.
- `create_active_flow` must actually run, so a new conversation gets exactly one `WF Active Chat Flow`.
- Every `send_whatsapp_template` call in `processor.py` must use keyword arguments.

## Constraints

The `increment_rate_limit(doc.whatsapp_account, ...)` call in `send_default_message` is correct — `doc` is a parameter there — and must not be changed.

## Implementation evidence

`tridz-dev/waflo`, branch `feat/waflo-correctness`, commit **`3e2428a`** — *fix(flow): thread whatsapp account and keyword-bind template sends*.

- `process_whatsapp_message` gains `whatsapp_account=None` (defaulted, so external callers do not break); `_process_incoming_whatsapp_message` passes `doc.whatsapp_account`.
- All three `send_whatsapp_template` calls converted to keyword arguments.
- Files: `waflo/waflo/flow/processor.py`, `waflo/waflo/tests/test_process_whatsapp_message.py`.

### N1 severity, as found

The signature is `(mobile, template_name, body_params, header_params, button_url_map, ref_doctype, ref_name, ...)`. Calls passed `(mobile_no, template, value, button_url_map, ref_doctype, ref_name)`, so every argument after `value` landed one position early. Consequences traced through `_send_whatsapp_template`:

- step with buttons → `header_params["type"]` → `KeyError`, message never sent
- no buttons but a reference doctype → `json.loads("CRM Lead")` → `JSONDecodeError`, message never sent
- neither → sends, but `ref_name` is `None` so the message is not linked to its record

## Validation

Covered by `test_process_whatsapp_message.py` (3 tests). Full suite: 20/20 pass on the `visaguy` dev site @ `56899f2`.

## Deviations

Task A3 asked for the broad `except` to log a traceback. It already did (`frappe.log_error(frappe.get_traceback(), "WF Flow Critical Error")`) — the FEAT-003 text overstated this. No change made.

## Known limitations

Both defects sit on the **dormant flow-engine path** (`WF Settings.enable_flow_engine = 0` everywhere; the engine has never been tested). This task therefore unblocks [FEAT-004](../../../features/planned/whatsapp-flow-engine/README.md) rather than fixing a live production fault. See [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md).
