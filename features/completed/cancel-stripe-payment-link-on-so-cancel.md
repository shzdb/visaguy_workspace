---
id: FEAT-cancel-stripe-payment-link-on-so-cancel
title: Cancel Stripe Payment Links on Sales Order and Payment Request Cancellation
status: completed
priority: high
repositories: [visaguy_crm]
owners: ["fasil"]
depends_on: []
created: 2026-10-12
updated: 2026-10-13
---

# Cancel Stripe Payment Links on Sales Order and Payment Request Cancellation

## Summary

Automatic deactivation of Stripe Payment Links (`stripe.PaymentLink.modify(id, active=False)`) and expiration of open Stripe Checkout Sessions (`stripe.checkout.Session.expire(id)`) whenever a `Payment Request` or its linked `Sales Order` is cancelled in ERPNext.

## User value

Previously, when a `Payment Request` or `Sales Order` was cancelled, the Stripe link remained active in Stripe. Customers who held the URL could still pay for cancelled orders, which caused webhook errors (`Stripe Webhook - Payment for Cancelled Document`) and required manual accounting reconciliation. Deactivating the link on cancellation guarantees customers cannot pay on cancelled orders and immediately see an informative cancellation message on the Stripe hosted page.

## Scope

### Included

- Storing the created Stripe Payment Link ID (`plink_...`) or Checkout Session ID (`cs_...`) in `custom_stripe_payment_link_id` on `Payment Request` at creation time (`before_submit`).
- `on_cancel` hook on `Payment Request` to deactivate the Stripe Payment Link and expire open Checkout Sessions.
- `on_cancel` hook on `Sales Order` to find linked non-paid `Payment Request` records and deactivate their Stripe links.
- Idempotency within the same request (e.g., when a user clicks "Cancel All Documents" on a Sales Order, cancelling linked Payment Requests first and then the Sales Order).
- Fallback lookup by `metadata` (`reference_docname`, `sales_order_id`) or `url` for legacy `Payment Request` records created before `custom_stripe_payment_link_id` existed.
- Non-blocking error handling: Stripe network or API exceptions are logged and notified to the Accounts team via `log_stripe_error_and_notify` without blocking Frappe document cancellation.

### Excluded

- Cancelling already paid Payment Requests or Sales Orders with submitted Payment Entries (ERPNext core prevents cancellation of paid requests).
- Non-Stripe payment gateways (TotalPay, MyFatoorah handled via separate integration modules).

## Requirements

- Store Stripe Payment Link ID / Checkout Session ID in `Payment Request.custom_stripe_payment_link_id` (`Data`, `read_only=1`, `allow_on_submit=1`, `no_copy=1`, `hidden=1`).
- Deactivate Payment Links using `stripe.PaymentLink.modify(plink_id, active=False, inactive_message=...)`.
- Expire open Checkout Sessions using `stripe.checkout.Session.expire(session_id)`.
- Use `isinstance(frappe.flags.get("deactivated_stripe_prs"), set)` to safely manage request-level deactivation cache in `frappe.flags` (`frappe._dict`).
- Register `on_cancel` hooks under `Sales Order` and `Payment Request` in `visaguy_crm/hooks.py`.

## Tasks

- [x] [TASK-cancel-stripe-payment-link-on-so-cancel](file:///home/fasil/Tridz/visaguy_workspace/tasks/completed/cancel-stripe-payment-link-on-so-cancel.md)

## Acceptance criteria

- [x] Payment Request creation stores `custom_stripe_payment_link_id`.
- [x] Cancelling Payment Request deactivates the Stripe Payment Link and expires open sessions.
- [x] Cancelling Sales Order deactivates all associated Payment Request Stripe links.
- [x] Legacy Payment Requests without stored IDs resolve via metadata/URL fallback.
- [x] Both hooks running in a single "Cancel All" action do not call Stripe twice.
- [x] Stripe API failures log to Accounts and do not block ERPNext document cancellation.

## Dependencies

- `visaguy_crm` app
- `payments` app (`Stripe Settings` DocType)
- `stripe` Python SDK (`v10.12.0`) in bench virtualenv

## Completion notes

### Implementation Details

1. **`visaguy_crm/custom/payment_request.json`**:
   - Added `custom_stripe_payment_link_id` custom field under section `custom_payment_gateway__transaction_details`.
   - Exported and synced to site `visaguy`.

2. **`visaguy_crm/server_scripts/payment_from_lead/payment_request_hooks.py`**:
   - Updated `generate_payment_link` to store `doc.custom_stripe_payment_link_id = payment_link.id` (or `session.id`).
   - Added `cancel_stripe_payment_link(doc, method)` and `deactivate_stripe_payment_link_for_pr(pr_doc)`.
   - Implemented `_deactivate_payment_link_by_id`, `_expire_checkout_session_by_id`, and `_find_and_deactivate_by_metadata_or_url`.
   - Handled `frappe._dict` attribute lookup safely to prevent `TypeError: argument of type 'NoneType' is not iterable`.

3. **`visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py`**:
   - Added `cancel_associated_stripe_payment_links(doc, method)`.

4. **`visaguy_crm/hooks.py`**:
   - Registered `on_cancel` under `doc_events` for `Sales Order` and `Payment Request`.
