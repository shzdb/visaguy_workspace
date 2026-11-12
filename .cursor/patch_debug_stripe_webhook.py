from pathlib import Path

helper = '''
def _agent_dbg(hypothesis_id, location, message, data, run_id="pre-fix"):
    # #region agent log
    try:
        import json, time
        payload = {
            "sessionId": "e83f56",
            "runId": run_id,
            "hypothesisId": hypothesis_id,
            "location": location,
            "message": message,
            "data": data,
            "timestamp": int(time.time() * 1000),
        }
        line = json.dumps(payload, default=str) + "\\n"
        for p in ("/tmp/debug-e83f56.log", "/home/fasil/fasil-bench2/logs/debug-e83f56.log"):
            try:
                with open(p, "a") as f:
                    f.write(line)
            except Exception:
                pass
        try:
            import urllib.request
            req = urllib.request.Request(
                "http://127.0.0.1:7526/ingest/1413fac7-959f-47f9-877d-24d1d21ee60a",
                data=json.dumps(payload, default=str).encode(),
                headers={"Content-Type": "application/json", "X-Debug-Session-Id": "e83f56"},
                method="POST",
            )
            urllib.request.urlopen(req, timeout=0.4)
        except Exception:
            pass
    except Exception:
        pass
    # #endregion
'''

p = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/stripe_payment_webhook.py")
text = p.read_text()
if "_agent_dbg" not in text:
    needle = "from visaguy_raven.functions.send_bot_message import send_accounts_notify\n"
    if needle not in text:
        raise SystemExit("stripe import needle missing")
    text = text.replace(needle, needle + helper, 1)

    old = '''    event_type = data.get("type")

    if event_type == "checkout.session.completed":'''
    new = '''    event_type = data.get("type")
    # #region agent log
    _obj = (data.get("data") or {}).get("object") or {}
    _agent_dbg("H1", "stripe_payment_webhook.py:update_payment_status", "incoming stripe event", {
        "event_type": event_type,
        "has_balance_tx": bool(_obj.get("balance_transaction")),
        "pi_suffix": str(_obj.get("payment_intent") or "")[-8:],
        "charge_status": _obj.get("status"),
    })
    # #endregion

    if event_type == "checkout.session.completed":'''
    if old not in text:
        raise SystemExit("event_type needle missing")
    text = text.replace(old, new, 1)

    old = '''    pr_name = frappe.db.get_value(
        "Payment Request",
        {"custom_stripe_payment_intent": payment_intent, "status": ["!=", "Paid"]},
        "name"
    )

    if not pr_name:'''
    new = '''    pr_name = frappe.db.get_value(
        "Payment Request",
        {"custom_stripe_payment_intent": payment_intent, "status": ["!=", "Paid"]},
        "name"
    )
    # #region agent log
    _any_pr = frappe.db.get_value("Payment Request", {"custom_stripe_payment_intent": payment_intent}, ["name", "status", "docstatus"], as_dict=True)
    _agent_dbg("H1", "stripe_payment_webhook.py:_handle_charge_updated", "charge.updated PR lookup", {
        "unpaid_pr_found": bool(pr_name),
        "any_pr_status": (_any_pr or {}).get("status"),
        "any_pr_docstatus": (_any_pr or {}).get("docstatus"),
        "will_retry": not bool(pr_name),
        "has_balance_tx": bool(obj.get("balance_transaction")),
        "pi_suffix": str(payment_intent or "")[-8:],
    })
    # #endregion

    if not pr_name:'''
    if old not in text:
        raise SystemExit("pr_name needle missing")
    text = text.replace(old, new, 1)

    old = '''        accounts = get_stripe_accounts_for_company(so.company)

        si = make_sales_invoice(so.name)
        si.debit_to = accounts["debit_to"]
        si.insert()
        si.submit()'''
    new = '''        accounts = get_stripe_accounts_for_company(so.company)

        # #region agent log
        from frappe.utils import flt as _flt
        _unbilled = sum(1 for i in so.items if _flt(i.billed_amt) < _flt(i.amount))
        _existing_si = frappe.db.sql(
            """SELECT COUNT(DISTINCT si.name) FROM `tabSales Invoice` si
               INNER JOIN `tabSales Invoice Item` sii ON sii.parent=si.name
               WHERE sii.sales_order=%s AND si.docstatus=1""",
            so.name,
        )[0][0]
        _agent_dbg("H2", "stripe_payment_webhook.py:_process_stripe_payment:before_make", "SO billed state before make_sales_invoice", {
            "so_per_billed": so.per_billed,
            "so_status": so.status,
            "so_docstatus": so.docstatus,
            "so_item_count": len(so.items or []),
            "unbilled_item_count": _unbilled,
            "existing_submitted_si_count": _existing_si,
            "pr_status": pr.status,
        })
        # #endregion

        si = make_sales_invoice(so.name)
        # #region agent log
        _agent_dbg("H2", "stripe_payment_webhook.py:_process_stripe_payment:after_make", "mapped SI from SO", {
            "mapped_item_count": len(si.items or []),
            "mapped_codes": [i.item_code for i in (si.items or [])],
            "has_so_link": any(bool(i.sales_order) for i in (si.items or [])),
            "conv_pct": si.get("custom_convenience_charge_percentage"),
            "conv_fixed": si.get("custom_convenience_charge_fixed_amount"),
        })
        # #endregion
        si.debit_to = accounts["debit_to"]
        si.insert()
        si.submit()'''
    if old not in text:
        raise SystemExit("make_sales_invoice needle missing")
    text = text.replace(old, new, 1)
    p.write_text(text)
    print("patched stripe_payment_webhook.py")
else:
    print("stripe already patched")

p2 = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py")
t2 = p2.read_text()
if "_agent_dbg" not in t2:
    t2 = t2.replace("import frappe\n", "import frappe\n" + helper, 1)
    old = '''def add_convenience_fee_item(doc, method):
    if doc.is_return:
        return
    if doc.custom_convenience_charge_percentage or doc.custom_convenience_charge_fixed_amount:
        item_exists = False
        for item in doc.items:
            if item.item_code == "Convenience Fee":
                item_exists = True
                break
        
        if not item_exists:'''
    new = '''def add_convenience_fee_item(doc, method):
    if doc.is_return:
        return
    if doc.custom_convenience_charge_percentage or doc.custom_convenience_charge_fixed_amount:
        item_exists = False
        for item in doc.items:
            if item.item_code == "Convenience Fee":
                item_exists = True
                break
        # #region agent log
        _before_count = len(doc.items or [])
        _before_codes = [i.item_code for i in (doc.items or [])]
        if _before_count == 0 or not item_exists:
            _agent_dbg("H5", "sales_invoice_hooks.py:add_convenience_fee_item", "convenience fee hook on SI", {
                "before_count": _before_count,
                "before_codes": _before_codes,
                "will_append": not item_exists,
                "owner": doc.owner,
                "is_new": doc.is_new(),
            })
        # #endregion
        
        if not item_exists:'''
    if old not in t2:
        raise SystemExit("add_convenience_fee needle missing")
    t2 = t2.replace(old, new, 1)
    p2.write_text(t2)
    print("patched sales_invoice_hooks.py")
else:
    print("hooks already patched")
