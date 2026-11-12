---
id: FEAT-lead-so-convenience-fee-conversion-factor
title: Set UOM conversion factor when Generate Sales Order adds Convenience Fee
status: completed
priority: high
repositories: [visaguy_crm]
owners: ["fasil"]
depends_on: []
created: 2026-10-29
updated: 2026-10-29
---

# Set UOM conversion factor when Generate Sales Order adds Convenience Fee

## Summary

Generate Sales Order from Lead failed with `MandatoryError: conversion_factor` on Sales Order Item **Convenience Fee** for some leads. The Item master was valid (`stock_uom = Nos`, UOM conversion `1`). The Lead generator copied Destination items, called `set_missing_values()`, then the Sales Order `before_save` hook appended Convenience Fee **after** that fill. Destinations that already listed Convenience Fee succeeded; destinations that did not got a new row without `conversion_factor`.

## User value

Consultants can Generate Sales Order from any Lead whose Destination does not already include Convenience Fee, without the popup `Sales Order Item Row #N: Value missing for: UOM Conversion Factor`.

## Scope

### Included

- Set `stock_uom` and `conversion_factor` when `add_convenience_fee_item` appends Convenience Fee on Sales Order.
- Backfill `conversion_factor` if Convenience Fee is already on the document but the factor is empty.
- Set `stock_uom` / `conversion_factor` on Destination items built by `prepare_sales_order_data`.
- Same fields when Sales Invoice `add_convenience_fee_item` appends Convenience Fee.

### Excluded

- Changing Destination item lists to always include Convenience Fee.
- Changing the Item master or UOM Conversion Detail for Convenience Fee.
- Manual Sales Order form entry (client `item_code` already calls `get_item_details`).

## Requirements

1. Programmatic Sales Order insert from Lead must not fail mandatory `conversion_factor` on Convenience Fee.
2. If Destination already includes Convenience Fee, keep a single row and still fill a missing factor.
3. Sales Invoice convenience-fee append must include `conversion_factor`.

## Proposed design

ERPNext `Sales Order Item.conversion_factor` is `reqd`. `set_missing_values()` fills it only for rows that already exist. The Lead button inserts immediately, so a `before_save` append is too late. Set `uom`, `stock_uom`, and `conversion_factor` on the appended dict (and on Destination item dicts). Resolve the factor via `erpnext.stock.get_item_details.get_conversion_factor`.

## Tasks

- [x] [TASK-fix-lead-so-convenience-fee-conversion-factor](../../tasks/completed/fix-lead-so-convenience-fee-conversion-factor.md)

## Acceptance criteria

- [x] Convenience Fee appended in Sales Order `before_save` includes `stock_uom` and `conversion_factor`.
- [x] Destination items from `prepare_sales_order_data` include `stock_uom` and `conversion_factor`.
- [x] Sales Invoice convenience-fee append includes `conversion_factor`.
- [ ] Generate Sales Order click on a live failing Lead (Destination without Convenience Fee) was not re-run after the remote patch.

## Dependencies

- `visaguy_crm` payment-from-lead scripts
- ERPNext `Sales Order Item` mandatory `conversion_factor`
- Item `Convenience Fee` and Mode of Payment convenience charges

## Risks

- Remote `visaguy_crm` changes are unstaged and not committed. A pull or reset on that app will drop the fix.
- `frappe serve` workers may still hold the old module until a process restart if the file watcher did not reload.

## Open questions

None.

## Completion notes

Implemented on the remote bench `visaguy_crm` app (`/home/fasil/fasil-bench2/apps/visaguy_crm`). Local `/home/fasil/Tridz/bench_v15` copies of these files were reverted. Changes left unstaged; not committed.

1. **`visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py`** (`add_convenience_fee_item`):
   - Append sets `stock_uom` and `conversion_factor` from `get_conversion_factor`.
   - Existing Convenience Fee rows with an empty factor are backfilled.

2. **`visaguy_crm/server_scripts/payment_from_lead/prepare_sales_order_data.py`**:
   - Destination item dicts include `stock_uom` and `conversion_factor: 1` (UOM is stock UOM).

3. **`visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py`**:
   - Append copies `stock_uom` and `conversion_factor` from `get_item_details`.

4. **Validation**: live traceback `SAL-ORD-2026-06374` **runtime-verified** the bug. Remote patch is **source-wired** (git diff + Python parse). `bench --site visaguy clear-cache` ran. Post-fix Generate Sales Order click was not runtime-verified.
