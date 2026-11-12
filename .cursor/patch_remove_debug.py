from pathlib import Path

# --- sales_invoice_hooks ---
p2 = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py")
t2 = p2.read_text()
start = t2.find("def _agent_dbg")
end = t2.find("ALLOWED_DOCTYPES")
if start == -1 or end == -1:
    raise SystemExit("hooks _agent_dbg block missing")
t2 = t2[:start] + t2[end:]

old = '''        item_exists = False
        for item in doc.items:
            if item.item_code == fee_item_code:
                item_exists = True
                break
        # #region agent log
        _before_count = len(doc.items or [])
        _before_codes = [i.item_code for i in (doc.items or [])]
        if _before_count == 0 or not item_exists:
            _agent_dbg("H5", "sales_invoice_hooks.py:add_convenience_fee_item", "convenience fee hook on SI", {
                "before_count": _before_count,
                "before_codes": _before_codes,
                "will_append": bool(_before_count and not item_exists),
                "skipped_empty": _before_count == 0,
                "owner": doc.owner,
                "is_new": doc.is_new(),
            }, run_id="post-fix")
        # #endregion
        if not doc.items:
            return
        
        if not item_exists:'''
new = '''        if not doc.items:
            return

        item_exists = False
        for item in doc.items:
            if item.item_code == fee_item_code:
                item_exists = True
                break
        
        if not item_exists:'''
if old not in t2:
    raise SystemExit("hooks convenience debug needle missing")
t2 = t2.replace(old, new, 1)
p2.write_text(t2)
print("cleaned sales_invoice_hooks.py")

# --- stripe webhook ---
p = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/stripe_payment_webhook.py")
text = p.read_text()
text = text.replace("from frappe.utils import today\n", "from frappe.utils import today, flt\n", 1)

start = text.find("def _agent_dbg")
end = text.find("def log_stripe_error_and_notify")
if start == -1 or end == -1:
    raise SystemExit("webhook _agent_dbg block missing")
text = text[:start] + text[end:]

old = '''    event_type = data.get("type")
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
new = '''    event_type = data.get("type")

    if event_type == "checkout.session.completed":'''
if old not in text:
    raise SystemExit("event_type debug needle missing")
text = text.replace(old, new, 1)

old = '''    pr_name = frappe.db.get_value(
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

    if not pr_name:
        if _any_pr and _any_pr.get("status") == "Paid":
            # #region agent log
            _agent_dbg("H4", "stripe_payment_webhook.py:_handle_charge_updated", "skip charge.updated; PR already Paid", {
                "pi_suffix": str(payment_intent or "")[-8:],
            }, run_id="post-fix")
            # #endregion
            return
        # checkout.session.completed may not have arrived yet — retry via Redis
        _handle_charge_updated_retry(payment_intent, data)
        return
'''
new = '''    pr_name = frappe.db.get_value(
        "Payment Request",
        {"custom_stripe_payment_intent": payment_intent, "status": ["!=", "Paid"]},
        "name"
    )

    if not pr_name:
        paid_pr = frappe.db.get_value(
            "Payment Request",
            {"custom_stripe_payment_intent": payment_intent, "status": "Paid"},
            "name",
        )
        if paid_pr:
            return
        # checkout.session.completed may not have arrived yet — retry via Redis
        _handle_charge_updated_retry(payment_intent, data)
        return
'''
if old not in text:
    raise SystemExit("charge.updated lookup needle missing")
text = text.replace(old, new, 1)

old = '''        accounts = get_stripe_accounts_for_company(so.company)

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
        }, run_id="post-fix")
        # #endregion
        if not si.items:
            existing = _existing_submitted_invoice_for_so(so.name)
            # #region agent log
            _agent_dbg("H3", "stripe_payment_webhook.py:_process_stripe_payment:skip_empty", "not inserting empty mapped SI", {
                "has_existing_si": bool(existing),
                "existing_outstanding": (existing or {}).get("outstanding_amount"),
            }, run_id="post-fix")
            # #endregion
            if not existing:
                log_stripe_error_and_notify(
                    "Stripe Webhook - No billable items",
                    f"Sales Order {so.name} has no unbilled items and no submitted Sales Invoice to pay.",
                    doc=so,
                )
                return {"status": "error"}
            si = frappe.get_doc("Sales Invoice", existing["name"])
            if _flt(si.outstanding_amount) <= 0:
                so.db_set("status", "Completed")
                frappe.db.commit()
                return {"status": "success", "invoice": si.name, "payment_entry": None, "skipped_duplicate": True}
        else:
            si.debit_to = accounts["debit_to"]
            si.insert()
            si.submit()
'''
new = '''        accounts = get_stripe_accounts_for_company(so.company)

        si = make_sales_invoice(so.name)
        if not si.items:
            existing = _existing_submitted_invoice_for_so(so.name)
            if not existing:
                log_stripe_error_and_notify(
                    "Stripe Webhook - No billable items",
                    f"Sales Order {so.name} has no unbilled items and no submitted Sales Invoice to pay.",
                    doc=so,
                )
                return {"status": "error"}
            si = frappe.get_doc("Sales Invoice", existing["name"])
            if flt(si.outstanding_amount) <= 0:
                so.db_set("status", "Completed")
                frappe.db.commit()
                return {"status": "success", "invoice": si.name, "payment_entry": None, "skipped_duplicate": True}
        else:
            si.debit_to = accounts["debit_to"]
            si.insert()
            si.submit()
'''
if old not in text:
    raise SystemExit("process_stripe_payment debug needle missing")
text = text.replace(old, new, 1)

old = '''        if paid_pr:
            # #region agent log
            _agent_dbg("H4", "stripe_payment_webhook.py:retry_charge_updated", "skip retry; PR already Paid", {
                "pi_suffix": str(payment_intent or "")[-8:],
            }, run_id="post-fix")
            # #endregion
            return
'''
new = '''        if paid_pr:
            return
'''
if old not in text:
    raise SystemExit("retry paid debug needle missing")
text = text.replace(old, new, 1)

if "_agent_dbg" in text:
    raise SystemExit("webhook still has _agent_dbg")
p.write_text(text)
print("cleaned stripe_payment_webhook.py")
