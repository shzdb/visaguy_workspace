from pathlib import Path

# --- sales_invoice_hooks: do not append Convenience Fee onto an empty SI ---
p2 = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py")
t2 = p2.read_text()
old = '''        if _before_count == 0 or not item_exists:
            _agent_dbg("H5", "sales_invoice_hooks.py:add_convenience_fee_item", "convenience fee hook on SI", {
                "before_count": _before_count,
                "before_codes": _before_codes,
                "will_append": not item_exists,
                "owner": doc.owner,
                "is_new": doc.is_new(),
            })
        # #endregion
        
        if not item_exists:'''
new = '''        if _before_count == 0 or not item_exists:
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
if old not in t2:
    raise SystemExit("sales_invoice_hooks needle missing")
t2 = t2.replace(old, new, 1)
p2.write_text(t2)
print("patched sales_invoice_hooks.py")

# --- stripe webhook ---
p = Path("/home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/server_scripts/payment_from_lead/stripe_payment_webhook.py")
text = p.read_text()

old = '''    if not pr_name:
        # checkout.session.completed may not have arrived yet — retry via Redis
        _handle_charge_updated_retry(payment_intent, data)
        return
'''
new = '''    if not pr_name:
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
if old not in text:
    raise SystemExit("charge.updated unpaid-miss needle missing")
text = text.replace(old, new, 1)

old = '''        si = make_sales_invoice(so.name)
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
        si.submit()
'''
new = '''        si = make_sales_invoice(so.name)
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
if old not in text:
    raise SystemExit("make_sales_invoice insert needle missing")
text = text.replace(old, new, 1)

old = '''    pr_name = frappe.db.get_value(
        "Payment Request",
        {"custom_stripe_payment_intent": payment_intent, "status": ["!=", "Paid"]},
        "name"
    )

    if not pr_name:
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
            # #region agent log
            _agent_dbg("H4", "stripe_payment_webhook.py:retry_charge_updated", "skip retry; PR already Paid", {
                "pi_suffix": str(payment_intent or "")[-8:],
            }, run_id="post-fix")
            # #endregion
            return
        _handle_charge_updated_retry(payment_intent, data)
        return
'''
if old not in text:
    raise SystemExit("retry unpaid-miss needle missing")
text = text.replace(old, new, 1)

helper_fn = '''
def _existing_submitted_invoice_for_so(so_name):
    rows = frappe.db.sql(
        """
        SELECT si.name, si.outstanding_amount
        FROM `tabSales Invoice` si
        INNER JOIN `tabSales Invoice Item` sii ON sii.parent = si.name
        WHERE sii.sales_order = %s AND si.docstatus = 1 AND IFNULL(si.is_return, 0) = 0
        GROUP BY si.name
        ORDER BY si.creation DESC
        LIMIT 1
        """,
        so_name,
        as_dict=True,
    )
    return rows[0] if rows else None


'''
needle = "def get_stripe_accounts_for_company(company):\n"
if helper_fn.strip() not in text:
    if needle not in text:
        raise SystemExit("helper insert needle missing")
    text = text.replace(needle, helper_fn + needle, 1)

p.write_text(text)
print("patched stripe_payment_webhook.py")
