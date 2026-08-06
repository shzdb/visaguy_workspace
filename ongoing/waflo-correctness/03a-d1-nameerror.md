# Phase 3a — D1 NameError + N1 keyword args

Branch: `feat/waflo-correctness` (off `develop` @ `2167958`).
Scope: `processor.py` + regression tests only. No push. No bench runs.

---

## What changed and why

### A1 — D1 NameError (`doc` unbound in `process_whatsapp_message`)

`increment_rate_limit(doc.whatsapp_account, mobile_no)` referenced `doc`, which is not a parameter of `process_whatsapp_message` and is not otherwise bound. The `NameError` was swallowed by the broad `except Exception`, so `create_active_flow(...)` never ran for new conversations.

**Fix:** thread the WhatsApp account in from the caller:

- `_process_incoming_whatsapp_message` already has `doc` and therefore `doc.whatsapp_account`.
- Added parameter `whatsapp_account=None` to `process_whatsapp_message`.
- Replaced `increment_rate_limit(doc.whatsapp_account, mobile_no)` with `increment_rate_limit(whatsapp_account, mobile_no)`.

`send_default_message(doc)` was **not** changed — there `doc` is a real parameter and the call is correct (policy / recon R6).

### A2 — N1 positional shuffle on `send_whatsapp_template`

Signature:

```
send_whatsapp_template(mobile, template_name, body_params=None, header_params=None,
                       button_url_map=None, ref_doctype=None, ref_name=None,
                       use_flow=False, queue=False)
```

Positional calls `(mobile_no, template, value, button_url_map, ref_doctype, ref_name)` put `button_url_map` into `header_params`, `ref_doctype` into `button_url_map`, `ref_name` into `ref_doctype`, and dropped `ref_name`.

**Fix:** every flow-driven call in `processor.py` now uses keyword arguments for everything after `template_name` (`body_params=`, `button_url_map=`, `ref_doctype=`, `ref_name=`). Three call sites updated (new-conversation + two continuing-conversation paths). The already-keyword `send_default_message` call was left alone.

### A3 — Visible failures / traceback logging

In this clone, the handler was **already**:

```python
except Exception as e:
    frappe.log_error(frappe.get_traceback(), "WF Flow Critical Error")
```

No edit required to satisfy A3. Title kept as `WF Flow Critical Error`. Try block not narrowed (out of scope).

### A4 / A5 — Regression tests

Added package `waflo/waflo/tests/` with `FrappeTestCase` tests. Outbound send mocked at `send_whatsapp_template` (higher than `make_post_request`); no network. Tests were **not** executed (`bench run-tests` unavailable — no site).

---

## New signature

```python
def process_whatsapp_message(
    mobile_no,
    message_text,
    ref_doctype=None,
    ref_name=None,
    whatsapp_account=None,
):
```

Default `whatsapp_account=None` preserves external callers. Repo search found only one production caller: `_process_incoming_whatsapp_message` in the same file.

---

## Call sites updated

| Location | Change |
|---|---|
| `_process_incoming_whatsapp_message` → `process_whatsapp_message(...)` | Passes `whatsapp_account=doc.whatsapp_account` |
| New-conversation path → `send_whatsapp_template` | Keyword args after template name; `increment_rate_limit(whatsapp_account, mobile_no)` |
| Continuing path (has template) → `send_whatsapp_template` | Keyword args |
| Continuing path (next-step template) → `send_whatsapp_template` | Keyword args |
| `send_default_message` → `increment_rate_limit(doc.whatsapp_account, ...)` | **Unchanged** (correct) |
| `send_default_message` → `send_whatsapp_template(...)` | **Unchanged** (already keywords) |

No other `process_whatsapp_message` callers in the repo.

---

## What the tests assert

**File:** `waflo/waflo/tests/test_process_whatsapp_message.py`

1. **`TestProcessWhatsappMessageD1.test_new_conversation_creates_one_active_flow_and_sends_template_once`**
   - No active flow (`get_all` → `[]`).
   - After `process_whatsapp_message(..., whatsapp_account=...)`:
     - `create_active_flow` called exactly once with flow, mobile, step, refs.
     - `send_whatsapp_template` called exactly once.
     - `increment_rate_limit` called once with the threaded account and mobile.

2. **`TestProcessWhatsappMessageN1.test_send_whatsapp_template_receives_button_and_ref_as_kwargs`**
   - New-conversation path with evaluated `button_url_map` and refs.
   - Asserts `send_whatsapp_template` kwargs: `body_params`, `button_url_map`, `ref_doctype`, `ref_name` bound correctly; not shifted into `header_params`.

Also added empty `waflo/waflo/tests/__init__.py` so the package is importable.

---

## Gates

| Gate | Result |
|---|---|
| `python -m py_compile` on modified `.py` files | **pass** |
| No `doc.` inside `process_whatsapp_message` | **pass** (remaining `doc.` hits are in `_process_incoming_whatsapp_message` / `send_default_message`) |
| No conflict markers | **pass** |
| Diff only `processor.py` + new tests | **pass** |

---

## Uncertainties

- **A3 already satisfied in tree** — task text said handler logged `str(e)`; recon/clone already used `frappe.get_traceback()`. Left unchanged; if a later phase expected a whitespace/comment touch, none was made.
- **Tests not runtime-verified** — no site for `bench run-tests`. Assertions are static/mock-based only.
- **`whatsapp_account=None` default** — if an external caller still invokes without the new kwarg, `increment_rate_limit` no-ops when account is falsy (existing limiter behaviour); flow creation still proceeds. Only in-repo caller was updated.
- Empty `button_url_map` path still passes `""` (pre-existing); keyword binding is correct either way.
