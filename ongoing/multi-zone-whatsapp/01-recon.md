# Multi-zone WhatsApp — Phase 1 recon

Read-only. Verified 2026-08-07 against local clones:

| Repo | Branch | HEAD | Porcelain |
|------|--------|------|-----------|
| `waflo` | `feat/multi-zone-whatsapp` | `56899f2` | clean |
| `the_visaguy` | `feat/multi-zone-whatsapp` | `e690b5b` | clean |

Spec: `features/ongoing/multi-zone-whatsapp/README.md` (FEAT-002). M7/M8 deferred per STATE.md.

**Path note:** Actual send module is `waflo/waflo/waflo/messaging/send.py` (three `waflo` segments). Spec short form `waflo/waflo/messaging/send.py` maps to that file. Spec line numbers for M1–M4 are **stale** (pre–FEAT-003 rewrite); current lines below are authoritative.

---

## R1 — `send_whatsapp_template` / `_send_whatsapp_template` (current)

### Signatures

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
):
```

Neither accepts `whatsapp_account`.

### Full bodies (current file)

`send_whatsapp_template` (lines 14–63): if `queue`, `frappe.enqueue(_send_whatsapp_template, …, queue="short", is_async=True, enqueue_after_commit=True)` with kwargs `mobile`, `template_name`, `body_params`, `header_params`, `button_url_map`, `ref_doctype`, `ref_name`, `use_flow`, `rate_limit` only; else returns `_send_whatsapp_template(..., rate_limit=rate_limit)`.

`_send_whatsapp_template` (lines 66–217): resolves account → optional rate-limit deferral via `log_pending_retry_whatsapp_message` → builds Meta payload → `make_post_request` → `log_whatsapp_message` → increments rate limits → on exception logs and re-raises.

### Account resolution

**Line 77:** `whatsapp_account = get_whatsapp_account(account_type="outgoing")`  
Always the default outgoing account. No override path. Throws if missing (lines 78–82).

### Template language code in Meta payload

**Line 171:** `"language": {"code": "en"}` hard-coded inside `data["template"]`.  
(Spec M3 pointed at `:80` — that line no longer exists; language is at 171.)

### Loggers and account value passed

| Call | Lines | `whatsapp_account=` value |
|------|-------|---------------------------|
| `log_pending_retry_whatsapp_message(...)` | 94–104 | `account_name` where `account_name = whatsapp_account.name` (line 85) — i.e. resolved default outgoing name |
| `log_whatsapp_message(...)` | 185–196 | `whatsapp_account.name` — same resolved default |

Both loggers already take a `whatsapp_account` kwarg; they just always receive the default-outgoing resolution.

### Thread points for a new `whatsapp_account` parameter

Inside `send.py` only (5):

1. **`send_whatsapp_template` signature** — add optional `whatsapp_account=None`.
2. **`queue=True` enqueue branch** (lines 37–51) — pass `whatsapp_account=whatsapp_account` into `frappe.enqueue` kwargs (today any new kwarg is dropped silently — M2).
3. **`queue=False` direct call** (lines 53–63) — pass through to `_send_whatsapp_template`.
4. **`_send_whatsapp_template` signature** — add optional `whatsapp_account=None`.
5. **Resolution at line 77** — use supplied account when present; else `get_whatsapp_account(account_type="outgoing")`.

Logging / rate-limit sites already consume the local `whatsapp_account` doc / `.name`; they do not need a new parameter once resolution uses the threaded value. Language (M3) is a separate change at line 171 (read from account/settings, not from the new param itself unless that is the chosen source).

**Spec discrepancy:** M1 cites `send.py:7,28,29`. Current function defs are lines **14** and **66**; resolve is **77**.

---

## R2 — Callers of `send_whatsapp_template`

Live call sites only (definitions, `_send_*` internal, and test patches/mocks excluded). **Count = 10.**

### `the_visaguy` (5 live + 1 commented)

| File:line | Context | Can know zone/account today? |
|-----------|---------|------------------------------|
| `handlers/whatsapp_message.py:118` | `_send_lead_form_link` | **Yes zone** — `doc.custom_zone`; has `whatsapp_default` loaded. No account field on Default yet (M5). |
| `handlers/whatsapp_message.py:146` | `_send_process_form_link` | Same |
| `handlers/whatsapp_message.py:188` | `_send_payment_received` (Payment Success) | Same |
| `handlers/whatsapp_message.py:209` | `_send_payment_received` (Payment Feedback) | Same |
| `handlers/whatsapp_message.py:236` | `_send_process_file_documents_delivered` | **Yes zone** — `lead.custom_zone` + loaded `whatsapp_default` |
| `handlers/whatsapp_message.py:34` | commented `send_default_message` | Dead; used hard-coded `COMPANY` |

### `waflo` (5 live)

| File:line | Context | Can know zone/account today? |
|-----------|---------|------------------------------|
| `flow/processor.py:66` | new-conversation flow reply | **Yes account** — `whatsapp_account` arg already in `process_whatsapp_message`; **not passed** to send. No zone. |
| `flow/processor.py:104` | matched-step reply | Same |
| `flow/processor.py:119` | next-step reply | Same |
| `flow/processor.py:187` | `send_default_message` | **Yes account** — `doc.whatsapp_account`; used for WF Account Settings + rate limit; **not passed** to send (`queue=True`). |
| `messaging/retry_message.py:41` | `retry_message` | **Yes account** — WhatsApp Message carries `whatsapp_account`; `doc` dict is available; **not passed**. |

Tests call `_send_whatsapp_template` or `@patch(...send_whatsapp_template)` — not counted as production callers.

---

## R3 — `the_visaguy` WhatsApp config / handler sources

### `the_visaguy/handlers/whatsapp_message.py` (full)

```python
import frappe
from frappe.utils import get_url
from waflo.waflo.messaging.send import send_whatsapp_template
# Not recreating this function in the_visaguy app because it is used in frappe_notifier app
from frappe_notifier.utils.normalize_to_https import normalize_url_to_https
from frappe.utils.pdf import get_pdf
from frappe.utils.file_manager import save_file
from the_visaguy.communications.doctype.whatsapp_default.whatsapp_default import is_enabled

# TEMPLATE_NAME = "default_reply-en"
TEMP_FOLDER = "Home/tmp"
TEMP_HOST_NAME = "https://visaguy.erpcode.tridz.in"

#company hardcode for now
COMPANY = "TVG"

def get_host_name():
    # In codiad, use temp since hostname is localhost so pdf generation works
    # This mode is set custom in site_config.json
    if frappe.conf.mode == "development":
        return TEMP_HOST_NAME
    return normalize_url_to_https(get_url())

# def send_default_message(doc,method):
#     try:
#         if doc.type == "Incoming" and doc.content_type != "flow":
#             if not is_enabled(company=COMPANY):
#                 return
#             whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": COMPANY})
#             mobile_no=doc.get("from")
#             image_url=whatsapp_default.introduction_image
#             host_name=get_host_name()
#             helpline_number=whatsapp_default.helpline_number
#             send_whatsapp_template(
#                 mobile=mobile_no,
#                 template_name=TEMPLATE_NAME,
#                 header_params={
#                     "type":"image",
#                     "image":{
#                         "link":host_name+image_url
#                     }
#                 },
#                 body_params=[helpline_number],
#                 queue=True
#             )
#     except Exception as e:
#         frappe.log_error(f"Error sending default message: {e}")

# Triggered for Lead and CRM Lead.
def send_lead_updates(doc,method):
    previous=doc.get_doc_before_save()
    # if the doc is new
    if not previous:
        return
    is_lead_form_link_generated=doc.has_value_changed("custom_file_request_link_sent")
    is_process_form_link_generated=doc.has_value_changed("custom_process_file_created")
    is_payment_received=doc.has_value_changed("custom_payment_received")
    #if the form link is the field which is updated
    if not is_lead_form_link_generated and not is_process_form_link_generated and not is_payment_received:
        return
    if is_lead_form_link_generated:
        frappe.enqueue(
            method=_send_lead_form_link,
            queue='short',
            timeout=300,
            is_async=True,
            enqueue_after_commit=True,
            doc=doc
        )
    if is_process_form_link_generated:
        frappe.enqueue(
            method=_send_process_form_link,
            queue='short',
            timeout=300,
            is_async=True,
            enqueue_after_commit=True,
            doc=doc
        )
    if is_payment_received:
        frappe.enqueue(
            method=_send_payment_received,
            queue='short',
            timeout=300,
            is_async=True,
            enqueue_after_commit=True,
            doc=doc
        )

def send_process_file_updates(doc,method):
    previous=doc.get_doc_before_save()
    # if the doc is new
    if not previous:
        return
    workflow_state_changed=doc.has_value_changed("workflow_state")
    if workflow_state_changed and doc.workflow_state == "Documents Delivered" and doc.custom_reference_type in ["CRM Lead","Lead"]:
        frappe.enqueue(
            method=_send_process_file_documents_delivered,
            queue='short',
            timeout=300,
            is_async=True,
            enqueue_after_commit=True,
            doc=doc
        )

def _send_lead_form_link(doc):
    # Get the primary applicant
    primary_applicant=next((row for row in doc.custom_applicant_information if row.type == "Primary"), None)
    if not primary_applicant:
        return
    if primary_applicant.file_collection:
        form_id=frappe.get_value("FF File Collection",primary_applicant.file_collection,"form_id")
        if not is_enabled(company=doc.custom_zone,customer=doc.custom_customer_id):
            return
        whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": doc.custom_zone})
        lead_form_link_template = [x for x in whatsapp_default.event_template if x.event_type == "Lead Form"][0].template
        if not lead_form_link_template or not doc.mobile_no or not doc.first_name:
            return
        send_whatsapp_template(
            mobile=whatsapp_default.clean_mobile_no(doc.whatsapp_no or doc.mobile_no),
            template_name=lead_form_link_template,
            body_params=[doc.first_name],
            button_url_map={
                "0":f"/form/{form_id}"
            },
            ref_doctype=doc.doctype,
            ref_name=doc.name
        )

def _send_process_form_link(doc):
    # Get the primary applicant
    primary_applicant=next((row for row in doc.custom_applicant_information if row.type == "Primary"), None)
    if not primary_applicant:
        return
    if primary_applicant.process_file:
        process_form_id=frappe.get_value("FF File Collection",{
            "reference_name":primary_applicant.process_file,
        },"form_id")
        if not process_form_id:
            return
        if not is_enabled(company=doc.custom_zone,customer=doc.custom_customer_id):
            return
        whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": doc.custom_zone})
        process_form_link_template = [x for x in whatsapp_default.event_template if x.event_type == "Process Form"][0].template
        if not process_form_link_template or not doc.mobile_no or not doc.first_name:
            return
        send_whatsapp_template(
            mobile=whatsapp_default.clean_mobile_no(doc.whatsapp_no or doc.mobile_no),
            template_name=process_form_link_template,
            body_params=[doc.first_name,doc.custom_destination],
            button_url_map={
                "0":f"/form/{process_form_id}"
            },
            ref_doctype=doc.doctype,
            ref_name=doc.name
        )

def _send_payment_received(doc):
    if not is_enabled(company=doc.custom_zone,customer=doc.custom_customer_id):
        return
    whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": doc.custom_zone})
    sales_invoice = frappe.get_doc("Sales Invoice", {
        "custom_reference_doctype":doc.doctype,
        "custom_reference_doc_name":doc.name,
        "docstatus":1,
        "status":"Paid"
    })
    frappe.log_error("Sales invoice for sending in whatsapp message",sales_invoice)
    print_format=frappe.get_meta("Sales Invoice").default_print_format 
    if not sales_invoice or not print_format:
        return
    html = frappe.get_print(doctype="Sales Invoice", name=sales_invoice.name, print_format=print_format,as_pdf=False)
    pdf_data = get_pdf(html)
    file_doc = save_file(
        fname=f"Sales_Invoice_{sales_invoice.name}.pdf",
        content=pdf_data,
        dt="Sales Invoice",
        dn=sales_invoice.name,
        is_private=0,
        folder=TEMP_FOLDER
    )
    host_name=get_host_name()
    file_url = host_name + file_doc.file_url
    frappe.log_error("File url for sending in whatsapp message",file_url)
    payment_success_link_template = [x for x in whatsapp_default.event_template if x.event_type == "Payment Success"][0].template
    if not payment_success_link_template or not doc.mobile_no or not doc.first_name:
        return
    
    send_whatsapp_template(
        mobile=whatsapp_default.clean_mobile_no(doc.whatsapp_no or doc.mobile_no),
        template_name=payment_success_link_template,
        header_params={
                "type":"document",
                "document":{
                    "filename":f"Sales_Invoice_{sales_invoice.name}.pdf",
                    "link":file_url
                }
            },
        body_params=[doc.first_name],
        queue=False,
        ref_doctype=doc.doctype,
        ref_name=doc.name
    )
    # Delete the file using daily scheduler
    # Send payment feedback
    payment_feedback_template = [x for x in whatsapp_default.event_template if x.event_type == "Payment Feedback"][0].template
    payment_feedback_header_image = [x for x in whatsapp_default.feedback_defaults if x.feedback_type == "Payment Feedback"][0].header_image
    if not payment_feedback_template or not payment_feedback_header_image:
        return
    message_id=send_whatsapp_template(
        mobile=whatsapp_default.clean_mobile_no(doc.whatsapp_no or doc.mobile_no),
        template_name=payment_feedback_template,
        header_params={
            "type":"image",
            "image":{
                "link":host_name+payment_feedback_header_image
            }
        },
        body_params=[doc.first_name],
        use_flow=True,
        ref_doctype=doc.doctype,
        ref_name=doc.name
    )
    # log_whatsapp_message_map(message_id,doc.doctype,doc.name)

def _send_process_file_documents_delivered(doc):
    lead=frappe.get_doc(doc.custom_reference_type,doc.custom_reference_name)
    if not is_enabled(company=lead.custom_zone,customer=lead.custom_customer_id):
        return
    whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": lead.custom_zone})
    host_name=get_host_name()
    # Send process file documents delivered feedback
    completion_feedback_template = [x for x in whatsapp_default.event_template if x.event_type == "Completion Feedback"][0].template
    completion_feedback_header_image = [x for x in whatsapp_default.feedback_defaults if x.feedback_type == "Completion Feedback"][0].header_image
    if not completion_feedback_template or not lead.mobile_no or not lead.first_name:
        return
    message_id=send_whatsapp_template(
        mobile=whatsapp_default.clean_mobile_no(lead.whatsapp_no or lead.mobile_no),
        template_name=completion_feedback_template,
        body_params=[lead.first_name],
        header_params={
            "type":"image",
            "image":{
                "link":host_name+completion_feedback_header_image
            }
        },
        use_flow=True,
        ref_doctype=lead.doctype,
        ref_name=lead.name
    )
    # print("message_id",message_id)
    # log_whatsapp_message_map(message_id,lead.doctype,lead.name)```

### `whatsapp_default.py` (full)

```1:21:the_visaguy/the_visaguy/communications/doctype/whatsapp_default/whatsapp_default.py
# Copyright (c) 2025, Shahzad Bin Shahjahan and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class WhatsappDefault(Document):
	def clean_mobile_no(self,mobile_no):
		return mobile_no.replace("+", "")


def is_enabled(company,customer=None):
	customer_whatsapp_preference = True
	if not company:
		frappe.throw("Company is required")
	is_company_allowed = frappe.db.exists("Whatsapp Default", {"company": company, "enabled": 1})
	if not customer:
		return is_company_allowed
	customer_whatsapp_preference = frappe.db.get_value("Customer", customer, "custom_enable_whatsapp_notifications")
	return is_company_allowed and customer_whatsapp_preference
```

No `validate`. No `whatsapp_account` field usage.

### DocType field lists

#### `whatsapp_default.json` — DocType `Whatsapp Default`

- **autoname:** `field:company`
- **istable:** no (parent)
- **naming_rule:** By fieldname

| fieldname | fieldtype | options |
|-----------|-----------|---------|
| settings_tab | Tab Break | |
| company | Link | Company (reqd, unique) |
| enabled | Check | default 0 |
| introduction_tab | Tab Break | |
| introduction_section | Section Break | |
| introduction_image | Attach Image | reqd |
| helpline_number | Data | reqd |
| templates_tab | Tab Break | |
| event_template | Table | WhatsApp Default Templates |
| feedback_tab | Tab Break | |
| feedback_defaults | Table | Whatsapp Feedback Defaults |

#### `whatsapp_default_templates.json` — DocType `WhatsApp Default Templates`

- **autoname:** (none)
- **istable:** `1`

| fieldname | fieldtype | options |
|-----------|-----------|---------|
| event_type | Select | `Lead Form` / `Payment Success` / `Process Form` / `Visa Completion` / `Payment Feedback` / `Completion Feedback` (reqd) |
| template | Link | WhatsApp Templates (reqd) |

#### `whatsapp_feedback_defaults.json` — DocType `Whatsapp Feedback Defaults`

- **autoname:** (none)
- **istable:** `1`

| fieldname | fieldtype | options |
|-----------|-----------|---------|
| feedback_type | Select | `Payment Feedback` / `Completion Feedback` (reqd) |
| feedback_template | Link | Quality Feedback Template (reqd) |
| header_image | Attach Image | reqd |

---

## R4 — `Whatsapp Default` lookups and `is_enabled`

### Live `frappe.get_doc("Whatsapp Default", …)` — **4 sites** (not 5)

| File:line | Key expression |
|-----------|----------------|
| `handlers/whatsapp_message.py:114` | `{"company": doc.custom_zone}` |
| `handlers/whatsapp_message.py:142` | `{"company": doc.custom_zone}` |
| `handlers/whatsapp_message.py:160` | `{"company": doc.custom_zone}` |
| `handlers/whatsapp_message.py:229` | `{"company": lead.custom_zone}` |

Commented fifth: `:29` `{"company": COMPANY}` inside dead `send_default_message`.

### Live `is_enabled(...)` call sites — **4**

| File:line | Key passed as `company=` |
|-----------|--------------------------|
| `handlers/whatsapp_message.py:112` | `doc.custom_zone` |
| `handlers/whatsapp_message.py:140` | `doc.custom_zone` |
| `handlers/whatsapp_message.py:158` | `doc.custom_zone` |
| `handlers/whatsapp_message.py:227` | `lead.custom_zone` |

### `is_enabled` definition lookup

| File:line | Expression |
|-----------|------------|
| `communications/doctype/whatsapp_default/whatsapp_default.py:17` | `frappe.db.exists("Whatsapp Default", {"company": company, "enabled": 1})` |

### Spec claim vs code

- Spec summary / M6: **“five lookup sites”** → **FALSE**. Live `get_doc` lookups = **4**. M11’s “4 sites” matches code.
- “plus `is_enabled`” → function exists; 4 callers + 1 internal `exists`. Callers already pass a zone value under the misnamed `company=` kwarg.

**LOOKUP_SITES (live get_doc) = 4.**

---

## R5 — `[x for x in …][0]` over `event_template` / `feedback_defaults`

**7 sites** (spec claimed 6). All in `handlers/whatsapp_message.py`:

| Line | Child table | Filter |
|------|-------------|--------|
| 115 | `event_template` | `event_type == "Lead Form"` |
| 143 | `event_template` | `event_type == "Process Form"` |
| 184 | `event_template` | `event_type == "Payment Success"` |
| 205 | `event_template` | `event_type == "Payment Feedback"` |
| 206 | `feedback_defaults` | `feedback_type == "Payment Feedback"` |
| 232 | `event_template` | `event_type == "Completion Feedback"` |
| 233 | `feedback_defaults` | `feedback_type == "Completion Feedback"` |

Breakdown: **5** `event_template` + **2** `feedback_defaults`.

Spec summary text counted only `event_template` with `event_type` and claimed six; M10 lists six call-site slots but the payment path alone has **three** `[0]` indexings (184, 205, 206). **INDEX_SITES = 7.**

---

## R6 — Other `custom_zone` / `custom_company` / `Whatsapp Default` references

Outside `handlers/whatsapp_message.py`:

| Location | What |
|----------|------|
| `handlers/receive_feedback.py:9,18–22` | Hard-coded `COMPANY = "TVG"`; looks up `Whatsapp Feedback Defaults` with `parenttype="Whatsapp Default"`, `parent=COMPANY` |
| `hooks.py:156–173` | Doc events wire `send_lead_updates` / `send_process_file_updates`; commented `send_default_message`; `receive_feedback` on WhatsApp Message |
| `communications/doctype/whatsapp_default/whatsapp_default.py` | `is_enabled` + DocType class |
| `communications/doctype/whatsapp_default/whatsapp_default.json` | DocType def |
| `communications/doctype/whatsapp_default/whatsapp_default.js` | Commented empty form handler only |
| `communications/doctype/whatsapp_default/test_whatsapp_default.py` | Empty `FrappeTestCase` stub |
| `fixtures/insights_query.json` | Two Insight scripts SQL-joining `tabWhatsapp Feedback Defaults` / `tabWhatsApp Default Templates` (comments mention Whatsapp Default) |
| `tvg_crm/doctype/raw_lead/raw_lead.py:14,56–57` | Employee `custom_zone`; sets `crm_lead.custom_company` / `custom_zone` |
| `setup.py:12` | Employee `custom_zone` |
| `integrations/crm_lead.py:30` | `company=doc.custom_zone` passed into conversion-event enqueue (Zone value into a `company` kwarg — separate Zone/Company confusion, not WhatsApp send) |

No patches reference `Whatsapp Default` / `custom_zone`. No JS beyond the stub.

---

## R7 — Patch conventions

### `the_visaguy`

- **`the_visaguy/the_visaguy/patches.txt` exists.**
- Contents: `[pre_model_sync]` (empty aside from comments); `[post_model_sync]` lists `the_visaguy.patches.enable_whatsapp_in_customer`.
- Modules live flat under `the_visaguy/the_visaguy/patches/` (e.g. `enable_whatsapp_in_customer.py` with `execute()`). No `v1_0` package.

### `waflo`

- **`waflo/waflo/patches.txt` exists.**
- Contents: `[pre_model_sync]` empty; `[post_model_sync]` lists `waflo.patches.v1_0.remove_obsolete_wf_settings_field`.
- Modules live under `waflo/waflo/patches/v1_0/` (versioned package + `execute()`).

Zone rekey migration should follow each app’s existing pattern (`the_visaguy.patches.<name>` flat; `waflo` not needed for Whatsapp Default).

---

## R8 — Tests in `the_visaguy`

| Path | Framework | Exercises WhatsApp handlers? |
|------|-----------|------------------------------|
| `communications/doctype/whatsapp_default/test_whatsapp_default.py` | `frappe.tests.utils.FrappeTestCase` | **No** — empty `pass` |
| `feedback/doctype/feedback_*/test_*.py` (2) | same | No |
| `tvg_core/doctype/*/test_*.py` (3) | same | No |
| `tvg_crm/doctype/raw_lead/test_raw_lead.py` | same | No |

**TESTS_EXIST = yes** (stubs only). **No test exercises WhatsApp handlers or send path.**

(`waflo` has real tests under `waflo/waflo/waflo/tests/` for send/retry/rate-limit — out of R8 scope.)

---

## R9 — Additional defects / landmines (not in M1–M19)

1. **`receive_feedback.py` hard-codes `COMPANY = "TVG"`** and resolves feedback templates with `parent=COMPANY`. Non-TVG zones’ inbound flow feedback will look up the wrong (or missing) child rows. Spec never lists this file.
2. **`retry_message` drops `whatsapp_account`.** Stored WhatsApp Message has `whatsapp_account`, but retry always re-resolves default outgoing. After multi-account, Qatar deferred/manual retries would resend from UAE.
3. **Flow / default-reply account mismatch in `processor.py`.** Inbound `doc.whatsapp_account` is used for rate-limit increments and WF Account Settings, but `send_whatsapp_template` always sends via default outgoing. Replies can debit the wrong limiter and leave from the wrong number once a second account exists.
4. **`Visa Completion` is in `event_type` Select options and in feature scope (“four auto message types”), but no handler sends it.** Only Lead Form, Process Form, Payment Success, Payment Feedback, Completion Feedback are wired. Completion Feedback ≠ Visa Completion.

### Spec/code count discrepancies (not code bugs, recorded for triage)

- Lookup sites: spec 5 → code **4** live `get_doc`.
- Index sites: spec 6 → code **7**.
- `send.py` line refs in M1–M4 are pre–FEAT-003.

---

## Gate check

```
git -C waflo status --porcelain     → (empty)
git -C the_visaguy status --porcelain → (empty)
```

No files in either clone were modified. This report is the only write.

---

## Summary counts

| Metric | Value |
|--------|------:|
| LOOKUP_SITES (live get_doc) | 4 |
| INDEX_SITES | 7 |
| SEND_CALLERS (live) | 10 |
| THREAD_POINTS (in send.py) | 5 |
| NEW_ISSUES | 4 |
| TESTS_EXIST | yes |
