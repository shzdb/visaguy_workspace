---
id: TASK-fix-lead-so-convenience-fee-conversion-factor
feature: FEAT-lead-so-convenience-fee-conversion-factor
title: Fix missing UOM conversion factor on Lead Generate Sales Order
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py
  - visaguy_crm/server_scripts/payment_from_lead/prepare_sales_order_data.py
  - visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py
created: 2026-10-29
updated: 2026-10-29
---

# Fix missing UOM conversion factor on Lead Generate Sales Order

## Objective

Stop Generate Sales Order from Lead from failing mandatory `conversion_factor` when Convenience Fee is added as an extra Sales Order row.

## Context

Live insert failed:

`frappe.exceptions.MandatoryError: [Sales Order, SAL-ORD-2026-06374]: conversion_factor`

Popup: `Sales Order Item Row #5: Value missing for: UOM Conversion Factor` (row 5 was Convenience Fee).

The Item JSON already had `uoms: [{uom: Nos, conversion_factor: 1}]`. The Lead path copies Destination items, runs `set_missing_values()`, then `so.insert()`. Sales Order `before_save` `add_convenience_fee_item` runs during insert. If the Destination does not already list Convenience Fee, the hook appends it too late, without `conversion_factor`. Leads whose Destination already includes Convenience Fee succeed because `set_missing_values()` filled the factor. Manual Sales Order entry does not hit this path.

## Inputs

- Remote app: `visaguy_crm` on `fasil@code.tridz.in:2203` at `/home/fasil/fasil-bench2/apps/visaguy_crm`
- Whitelist: `prepare_and_create_sales_order`
- Hook: `visaguy_crm.server_scripts.payment_from_lead.sales_order_hooks.add_convenience_fee_item` on Sales Order `before_save`

## Required behaviour

- When appending Convenience Fee on Sales Order, set `uom`, `stock_uom`, and `conversion_factor`.
- If Convenience Fee already exists but `conversion_factor` is empty, set it.
- Destination items built for the generated Sales Order include `stock_uom` and `conversion_factor`.
- Sales Invoice convenience-fee append includes `conversion_factor`.

## Constraints

- Implement over SSH on the remote bench. Do not leave this fix in local `/home/fasil/Tridz/bench_v15`.
- Leave git changes unstaged. Do not commit or push unless asked.
- Do not change Item master data or Destination item lists.

## Expected changes

- `sales_order_hooks.py`: set conversion factor on append and backfill existing Convenience Fee rows.
- `prepare_sales_order_data.py`: set `stock_uom` and `conversion_factor` on Destination items.
- `sales_invoice_hooks.py`: copy `stock_uom` and `conversion_factor` from `get_item_details`.

## Validation

- Live traceback on site `visaguy` **runtime-verified** the missing-factor failure (`SAL-ORD-2026-06374`, row 5 Convenience Fee).
- Remote files patched and Python-parsed (**source-wired**). Git diff confirmed the three files.
- `bench --site visaguy clear-cache` succeeded.
- Generate Sales Order was not re-clicked on a failing Lead after the patch.

## Definition of done

- Remote `visaguy_crm` payment-from-lead scripts set `conversion_factor` on Convenience Fee.
- Local bench copies of those files remain unmodified for this fix.
- Workspace feature and this task document exist and stay aligned.
