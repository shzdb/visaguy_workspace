# Waflo correctness — Phase 1 recon

Verified against local clone `ongoing/waflo-correctness/worktree`, branch `develop` @ `2167958816b55743c13a81fb94ce5673dd9834a3` (short `2167958`). Read-only; worktree left clean.

Spec: `features/ongoing/waflo-correctness/README.md` (FEAT-003).

---

## Summary counts

| Status | Count |
|--------|------:|
| STILL_PRESENT | 11 |
| ALREADY_FIXED | 0 |
| MISDESCRIBED | 0 |
| NEW_DEFECTS (not in spec) | 4 |

---

## D1 — `NameError` kills conversation creation

**Status: STILL_PRESENT**

| Spec claimed | Actual in this clone |
|---|---|
| `waflo/waflo/flow/processor.py:61` | `waflo/waflo/flow/processor.py:61` (unchanged) |

```61:62:waflo/waflo/flow/processor.py
            increment_rate_limit(doc.whatsapp_account, mobile_no)
            create_active_flow(flow, mobile_no, step, ref_doctype, ref_name)
```

`process_whatsapp_message(mobile_no, message_text, ref_doctype=None, ref_name=None)` has no `doc` in scope. Call raises `NameError` before `create_active_flow`.

Broad handler at lines 106–107 logs traceback under title **`WF Flow Critical Error`** (spec said `"WF Flow Error"` — title drift only; defect itself is accurate).

Correct call remains at `processor.py:151` inside `send_default_message(doc)`.

**Also true (reinforces D1):** `process_whatsapp_message` never receives `whatsapp_account`; `_process_incoming_whatsapp_message` drops it when calling at line 39. Fixing the NameError requires threading the account in, not only renaming a variable.

---

## D2 — Rate limiter never counts on flow paths

**Status: STILL_PRESENT**

`increment_rate_limit` call sites in this repo (definitions excluded):

| File:line | Context | Works? |
|---|---|---|
| `processor.py:61` | new-conversation path | No — `NameError` (D1) |
| `processor.py:151` | `send_default_message` | Yes — only when `enable_flow_engine` is off |

Continuing-conversation path (`processor.py:65–104`) sends templates at lines 85/91 and never calls `increment_rate_limit`.

With flow engine on: counter stays absent → `is_rate_limited` returns `False` at line 32 when cache empty → limiter inert. Spec accurate.

---

## D3 — Outbound template sends not rate limited

**Status: STILL_PRESENT**

`waflo/waflo/messaging/send.py` — `send_whatsapp_template` (lines 7–25) and `_send_whatsapp_template` (lines 28–114) perform no `is_rate_limited` / `increment_rate_limit` calls. Spec line reference to the function is accurate; no check exists anywhere in the send path.

---

## D4 — Check-then-act race

**Status: STILL_PRESENT**

`rate_limiting.py`:

- `is_rate_limited` (26–43): `get_value` → read `count` / `window_start` from dict
- `increment_rate_limit` (64–97): separate `get_value` → mutate dict → `set_value`

Compound dict via `set_value` / `get_value`. Non-atomic RMW. Spec accurate; `frappe.cache().incr` / `.expire` not used.

---

## D5 — Window TTL extended on every increment

**Status: STILL_PRESENT**

`increment_rate_limit` passes `expires_in_sec=window_seconds` on every `set_value` (lines 67–74, 81–88, 93–97), including mid-window increments. Explicit `window_start` comparison (lines 39, 80) compensates, so latent as described. Spec accurate.

---

## D6 — `WF Settings.limit_after` orphaned

**Status: STILL_PRESENT**

Declared in `waflo/waflo/doctype/wf_settings/wf_settings.json` field_order + fields (`fieldname: limit_after`, `fieldtype: Data`, no `options`).

Repo-wide grep for `limit_after`: **only** that JSON. No Python consumer. Spec accurate.

---

## D7 — No account-level or global ceiling

**Status: STILL_PRESENT**

Cache key is only `waflo:rl:{account}:{mobile_no}` (`rate_limiting.py:24`, `:61`). No account-total or global counter. Spec accurate (absence of capability).

---

## D8 — Error handler can mask original error

**Status: STILL_PRESENT**

```107:114:waflo/waflo/messaging/send.py
    except Exception as e:
        frappe.log_error("send_whatsapp_template", f"WhatsApp Send Error: {str(e)}")
        frappe.get_doc({
            "doctype": "WhatsApp Notification Log",
            "template": "Text Message",
            "meta_data": frappe.flags.integration_request.json(),
        }).insert(ignore_permissions=True)
        raise
```

Spec said `:112`; the `frappe.flags.integration_request.json()` call is at **line 112**. Pre-request failures → `AttributeError` inside handler. Spec accurate.

---

## D9 — Missing template not guarded

**Status: STILL_PRESENT**

`send.py:30`: `template_actual_name = frappe.db.get_value("WhatsApp Templates", template_name, "actual_name")` — no null check. Payload uses `"name": template_actual_name` at line 79. Spec accurate.

---

## D10 — Log spam in button loop

**Status: STILL_PRESENT**

`send.py:62` inside `for idx, (btn_key, btn_url) in enumerate(button_url_map.items())`:

```python
frappe.log_error("WhatsApp API URL AND INDEX", f"Body Params: {btn_url} \nData: {str(idx)}")
```

Spec accurate.

---

## D11 — `use_flow` collides with `button_url_map`

**Status: STILL_PRESENT**

`button_url_map` entries use `index: str(idx)` starting at `"0"` (lines 61–68). `use_flow` appends FLOW button at `index: "0"` (lines 71–72). Spec said `:71`; collision still present.

---

## R2 — Exact signatures and bodies

### `waflo/waflo/flow/rate_limiting.py` (entire file, 103 lines)

```python
import time
import frappe

def is_rate_limited(account, mobile_no):
    """
    Returns True if replies should be blocked for this user.
    """

    if not mobile_no or not account:
        return False

    settings = frappe.get_cached_doc("WF Account Settings", account)

    if not settings.enable_rate_limiting:
        return False

    max_replies = settings.max_replies_per_window
    window_seconds = settings.window_seconds

    if not max_replies or not window_seconds:
        return False

    cache = frappe.cache()
    cache_key = f"waflo:rl:{account}:{mobile_no}"

    data = cache.get_value(cache_key)

    now = int(time.time())

    if not data:
        # No activity yet → allow
        return False

    # Cache values are stored as dict
    count = data.get("count", 0)
    window_start = data.get("window_start", now)

    # Window expired → allow (will reset on increment)
    if now - window_start >= window_seconds:
        return False

    # Block only if limit already reached
    return count >= max_replies

def increment_rate_limit(account, mobile_no):
    """
    Increments reply counter after a successful send.
    """
    if not mobile_no or not account:
        return

    settings = frappe.get_cached_doc("WF Account Settings", account)

    if not settings.enable_rate_limiting:
        return

    max_replies = settings.max_replies_per_window
    window_seconds = settings.window_seconds

    cache = frappe.cache()
    cache_key = f"waflo:rl:{account}:{mobile_no}"

    now = int(time.time())
    data = cache.get_value(cache_key)
    if not data:
        # First reply → create window
        cache.set_value(
            cache_key,
            {
                "count": 1,
                "window_start": now
            },
            expires_in_sec=window_seconds
        )
        return
    count = data.get("count", 0)
    window_start = data.get("window_start", now)

    # Window expired → reset
    if now - window_start >= window_seconds:
        cache.set_value(
            cache_key,
            {
                "count": 1,
                "window_start": now
            },
            expires_in_sec=window_seconds
        )
        return

    # Increment within window
    data["count"] = count + 1
    cache.set_value(
        cache_key,
        data,
        expires_in_sec=window_seconds
    )

def set_message_rate_limited(message):
    if not message:
        return
    message.custom_rate_limited = 1
    message.save(ignore_permissions=True)
```

### `send_whatsapp_template` / `_send_whatsapp_template` (`send.py`)

```python
def send_whatsapp_template(mobile, template_name, body_params=None, header_params=None, button_url_map=None, ref_doctype=None, ref_name=None,use_flow=False,queue=False):
    if queue:
        print("Sending WhatsApp template to queue")
        frappe.enqueue(
            _send_whatsapp_template,
            mobile=mobile,
            template_name=template_name,
            body_params=body_params,
            header_params=header_params,
            button_url_map=button_url_map,
            ref_doctype=ref_doctype,
            ref_name=ref_name,
            use_flow=use_flow,
            queue="short",
            is_async=True,
            enqueue_after_commit=True
        )
    else:
        return _send_whatsapp_template(mobile, template_name, body_params, header_params, button_url_map, ref_doctype, ref_name,use_flow)


def _send_whatsapp_template(mobile, template_name, body_params=None, header_params=None, button_url_map=None, ref_doctype=None, ref_name=None,use_flow=False):
    whatsapp_account = get_whatsapp_account(account_type="outgoing")
    template_actual_name = frappe.db.get_value("WhatsApp Templates", template_name, "actual_name")
    token = whatsapp_account.get_password("token")
    headers = {
        "Authorization": f"Bearer {token}",
        "Content-Type": "application/json"
    }

    components = []
    # Header is currently only one param, but whatsapp api expects it as an array
    if isinstance(header_params, str):
        header_params = json.loads(header_params)
    if header_params:
        components.append({
            "type": "header",
            "parameters": [{
                "type": header_params["type"],
                header_params["type"]: header_params[header_params["type"]]
            }]
        })
    if isinstance(body_params, str):
        body_params = json.loads(body_params)
    if body_params:
        components.append({
            "type": "body",
            "parameters": [{"type": "text", "text": str(p)} for p in body_params]
        })

    if isinstance(button_url_map, str):
        button_url_map = json.loads(button_url_map)
    if button_url_map:
        button_components = []
        for idx, (btn_key, btn_url) in enumerate(button_url_map.items()):
            frappe.log_error("WhatsApp API URL AND INDEX", f"Body Params: {btn_url} \nData: {str(idx)}")
            button_components.append({
                "type": "button",
                "sub_type": "url",
                "index": str(idx),
                "parameters": [{"type": "text", "text": btn_url}]
            })
        components.extend(button_components)
    
    if use_flow:
        components.append({"type": "button", "sub_type": "FLOW", "index": "0"})

    data = {
        "messaging_product": "whatsapp",
        "to": mobile,
        "type": "template",
        "template": {
            "name": template_actual_name,
            "language": {"code": "en"},
            "components": components
        }
    }

    # frappe.log_error("Whatsapp API Payload",data)

    try:
        response = make_post_request(
            f"{whatsapp_account.url}/{whatsapp_account.version}/{whatsapp_account.phone_id}/messages",
            headers=headers,
            data=json.dumps(data)
        )
        message_id = response["messages"][0]["id"]
        log_whatsapp_message(
            mobile_no=mobile, 
            template_name=template_name, 
            message_id=message_id, 
            body_params=body_params, 
            header_params=header_params, 
            button_components=button_url_map,
            ref_doctype=ref_doctype, 
            ref_name=ref_name, 
            whatsapp_account=whatsapp_account.name,
            is_flow=use_flow
        )
        return message_id
    except Exception as e:
        frappe.log_error("send_whatsapp_template", f"WhatsApp Send Error: {str(e)}")
        frappe.get_doc({
            "doctype": "WhatsApp Notification Log",
            "template": "Text Message",
            "meta_data": frappe.flags.integration_request.json(),
        }).insert(ignore_permissions=True)
        raise
```

### `process_whatsapp_message` / `create_active_flow` / `send_default_message` (`processor.py`)

```python
def process_whatsapp_message(mobile_no, message_text, ref_doctype=None, ref_name=None):
    try:
        active = frappe.get_all("WF Active Chat Flow", filters={
            "whatsapp_number": mobile_no,
            "is_active": 1
        }, limit=1)

        if not active:
            flow = frappe.get_doc("WF Message Flow", {"default_flow": 1})
            if not flow:
                return

            step = get_step_by_name(flow, flow.initial_step_name)
            if not step:
                return

            context_doc = frappe.get_doc(ref_doctype, ref_name) if ref_doctype and ref_name else None
            value = eval_template_params(step.template_parameter_map, context_doc) if step.template_parameter_map else ""
            button_url_map = eval_button_url_map(step.button_url_map,context_doc) if step.button_url_map else ""
            send_whatsapp_template(mobile_no, step.message_template, value,button_url_map, ref_doctype, ref_name)
            increment_rate_limit(doc.whatsapp_account, mobile_no)
            create_active_flow(flow, mobile_no, step, ref_doctype, ref_name)
            return

        active_doc = frappe.get_doc("WF Active Chat Flow", active[0].name)
        flow = frappe.get_doc("WF Message Flow", active_doc.flow)
        current_step = get_step_by_name(flow, active_doc.current_step_name)

        if not current_step:
            frappe.log_error(f"Current step '{active_doc.current_step_name}' not found in flow '{flow.name}'", "WF Flow Error")
            return

        matched_step = match_step(flow, current_step, message_text)

        if not matched_step:
            matched_step = get_step_by_name(flow, current_step.fallback_step_name)
            if not matched_step:
                return

        context_doc = frappe.get_doc(active_doc.reference_doctype, active_doc.reference_name)
        value = eval_template_params(matched_step.template_parameter_map, context_doc) if matched_step.template_parameter_map else ""
        button_url_map = eval_button_url_map(matched_step.button_url_map,context_doc) if matched_step.button_url_map else ""

        if matched_step.message_template:
            send_whatsapp_template(mobile_no, matched_step.message_template, value,button_url_map, ref_doctype, ref_name)
        else:
            matched_step = get_step_by_name(flow, matched_step.next_step_name)
            if matched_step and matched_step.message_template:
                value = eval_template_params(matched_step.template_parameter_map, context_doc) if matched_step.template_parameter_map else ""
                button_url_map = eval_button_url_map(matched_step.button_url_map,context_doc) if matched_step.button_url_map else ""
                send_whatsapp_template(mobile_no, matched_step.message_template, value, button_url_map, ref_doctype, ref_name)

        if matched_step.update_field_status:
            update_target_status(
                doctype=active_doc.reference_doctype,
                name=active_doc.reference_name,
                fieldname=matched_step.target_fieldname,
                value=matched_step.target_value
            )

        active_doc.current_step_name = matched_step.step_name
        active_doc.last_message = message_text
        active_doc.last_activity = now_datetime()
        active_doc.save()

    except Exception as e:
        frappe.log_error(frappe.get_traceback(), "WF Flow Critical Error")

def create_active_flow(flow, mobile_no, step, ref_doctype=None, ref_name=None):
    try:
        settings = frappe.get_single("WF Settings")
        timeout = settings.inactive_timeout or 60
        frappe.get_doc({
            "doctype": "WF Active Chat Flow",
            "whatsapp_number": mobile_no,
            "flow": flow.name,
            "current_step_name": step.step_name,
            "last_message": "",
            "last_activity": now_datetime(),
            "timeout_minutes": timeout,
            "is_active": 1,
            "reference_doctype": ref_doctype,
            "reference_name": ref_name
        }).insert(ignore_permissions=True)
    except Exception as e:
        frappe.log_error(f"Failed to create WF Active Chat Flow: {e}", "WF Flow Init")

def send_default_message(doc):
    try:
        if doc.type != "Incoming" or doc.content_type == "flow" or not doc.whatsapp_account:
            return
        wf_account_settings = frappe.get_doc("WF Account Settings", {"whatsapp_account": doc.whatsapp_account})
        if not wf_account_settings or not wf_account_settings.is_active or not wf_account_settings.default_template:
            return
        header_params = {}
        if wf_account_settings.header_type == "Image":
            header_params["type"] = "image"
            header_params["image"] = {"link": get_host_name() + wf_account_settings.header_image}
        elif wf_account_settings.header_type == "Video":
            header_params["type"] = "video"
            header_params["video"] = wf_account_settings.header_video
        mobile_no = doc.get("from")
        body_params = wf_account_settings.body_parameters.split(",") if wf_account_settings.body_parameters else []
        send_whatsapp_template(
            mobile=mobile_no,
            template_name=wf_account_settings.default_template,
            header_params=header_params,
            body_params=body_params,
            queue=True
        )
        increment_rate_limit(doc.whatsapp_account, mobile_no)
    except Exception as e:
        frappe.log_error(f"Failed to send default message: {e}", "WF Flow Error")
```

---

## R3 — Call sites

### `is_rate_limited`

| Location | Line | Notes |
|---|---:|---|
| `waflo/waflo/flow/rate_limiting.py` | 4 | definition |
| `waflo/waflo/flow/processor.py` | 9 | import |
| `waflo/waflo/flow/processor.py` | 25 | call in `_process_incoming_whatsapp_message` |

No callers outside `waflo` in this repo (repo is the `waflo` app only).

### `increment_rate_limit`

| Location | Line | Notes |
|---|---:|---|
| `waflo/waflo/flow/rate_limiting.py` | 45 | definition |
| `waflo/waflo/flow/processor.py` | 9 | import |
| `waflo/waflo/flow/processor.py` | 61 | call (broken — D1) |
| `waflo/waflo/flow/processor.py` | 151 | call in `send_default_message` |

### `set_message_rate_limited`

| Location | Line | Notes |
|---|---:|---|
| `waflo/waflo/flow/rate_limiting.py` | 99 | definition |
| `waflo/waflo/flow/processor.py` | 9 | import |
| `waflo/waflo/flow/processor.py` | 27 | call when rate limited |

### `send_whatsapp_template`

| Location | Line | Notes |
|---|---:|---|
| `waflo/waflo/messaging/send.py` | 7 | definition |
| `waflo/waflo/messaging/send.py` | 108 | string in `log_error` title only |
| `waflo/waflo/messaging/retry_message.py` | 3 | import |
| `waflo/waflo/messaging/retry_message.py` | 32 | call (keyword args) |
| `waflo/waflo/flow/processor.py` | 7 | import |
| `waflo/waflo/flow/processor.py` | 60 | call (positional — see N1) |
| `waflo/waflo/flow/processor.py` | 85 | call (positional — see N1) |
| `waflo/waflo/flow/processor.py` | 91 | call (positional — see N1) |
| `waflo/waflo/flow/processor.py` | 144 | call (keyword args, `queue=True`) |

`_send_whatsapp_template` is only invoked from `send_whatsapp_template` (lines 11, 25).

No call sites outside the `waflo` package exist in this repository.

Hook wiring: `waflo/hooks.py:143` → `waflo.waflo.flow.processor.process_incoming_whatsapp_message` (doc_events path into the flow engine).

---

## R4 — Test setup

| Item | Finding |
|---|---|
| Top-level `tests/` directory | **No** |
| `conftest.py` / pytest config | **No** |
| `tox.ini` / pytest in `pyproject.toml` | **No** |
| Test files | Four Frappe scaffold stubs only |

Files:

- `waflo/waflo/doctype/wf_settings/test_wf_settings.py`
- `waflo/waflo/doctype/wf_account_settings/test_wf_account_settings.py`
- `waflo/waflo/doctype/wf_message_flow/test_wf_message_flow.py`
- `waflo/waflo/doctype/wf_active_chat_flow/test_wf_active_chat_flow.py`

Each: `from frappe.tests.utils import FrappeTestCase` + empty `class Test…(FrappeTestCase): pass`.

**Framework:** Frappe’s built-in test runner (`bench run-tests` / `FrappeTestCase`). No real assertions for flow, rate limiting, or send. Scaffold only → treat as **tests exist but zero coverage**.

---

## R5 — DocType fields

### `WF Account Settings` (`wf_account_settings.json`)

| fieldname | fieldtype | options |
|---|---|---|
| whatsapp_account | Link | WhatsApp Account |
| is_active | Check | — |
| default_reply_tab | Tab Break | — |
| default_template | Link | WhatsApp Templates |
| header_type | Select | `\nImage\nDocument\nVideo\nLocation` |
| header_image | Attach Image | — |
| header_attachment | Attach | — |
| header_text | Data | — |
| body_parameters | Small Text | — |
| rate_limiting_tab | Tab Break | — |
| enable_rate_limiting | Check | — |
| max_replies_per_window | Int | — |
| window_seconds | Int | — |

No `limit_after` on this DocType. Rate-limit knobs that Python reads: `enable_rate_limiting`, `max_replies_per_window`, `window_seconds` (via `rate_limiting.py`).

### `WF Settings` (`wf_settings.json`) — Single

| fieldname | fieldtype | options |
|---|---|---|
| flow_tab | Tab Break | — |
| enable_flow_engine | Check | — |
| inactive_timeout | Int | — |
| rate_limiting_tab | Tab Break | — |
| **limit_after** | **Data** | — |
| retry_tab | Tab Break | — |
| retry_enabled_template | Table MultiSelect | WF WhatsApp Templates |
| retry_error_codes | Small Text | — |

**`limit_after`:** present on `WF Settings` as `Data`. **No Python consumer** in this clone (grep hits JSON only).

---

## R6 — New defects (not in FEAT-003)

### N1 — Positional-arg shuffle on flow sends (critical)

`send_whatsapp_template(mobile, template_name, body_params=None, header_params=None, button_url_map=None, ref_doctype=None, ref_name=None, …)`

Calls at `processor.py:60`, `:85`, `:91`:

```python
send_whatsapp_template(mobile_no, step.message_template, value, button_url_map, ref_doctype, ref_name)
```

Fourth positional is **`header_params`**, not `button_url_map`. Effect: buttons passed as header; `ref_doctype` used as `button_url_map`; `ref_name` used as `ref_doctype`; `ref_name` left `None`. `send_default_message` and `retry_message` use keywords and are fine.

### N2 — Continuing path assumes non-null reference doc

`processor.py:80`:

```python
context_doc = frappe.get_doc(active_doc.reference_doctype, active_doc.reference_name)
```

`create_active_flow` allows `ref_doctype`/`ref_name` to be `None` (lines 122–123). Continuing message then raises inside the broad except → step advance/send can fail after an active flow was created without refs.

### N3 — `increment_rate_limit` ignores empty max/window

`is_rate_limited` returns `False` when `max_replies` or `window_seconds` is falsy (lines 20–21). `increment_rate_limit` has no equivalent guard after `enable_rate_limiting`; it still `set_value(..., expires_in_sec=window_seconds)` with a possibly null/zero TTL. Check and increment disagree when limiting is “enabled” but incomplete.

### N4 — `send_default_message` reads nonexistent `header_video`

`processor.py:140–141`: when `header_type == "Video"`, code uses `wf_account_settings.header_video`. `WF Account Settings` defines `header_attachment` (and `header_image` / `header_text`), not `header_video`. Video default replies raise / fail inside the function’s except.

---

## Gate check

`git status --porcelain` in the clone: empty (no local edits). This report lives at `ongoing/waflo-correctness/01-recon.md` (outside the clone).
