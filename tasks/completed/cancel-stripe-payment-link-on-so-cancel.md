---
id: TASK-cancel-stripe-payment-link-on-so-cancel
feature: FEAT-cancel-stripe-payment-link-on-so-cancel
title: Cancel Stripe Payment Links on Sales Order and Payment Request Cancellation
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - visaguy_crm/visaguy_crm/custom/payment_request.json
  - visaguy_crm/server_scripts/payment_from_lead/payment_request_hooks.py
  - visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py
  - visaguy_crm/hooks.py
created: 2026-10-12
updated: 2026-10-13
---

# Cancel Stripe Payment Links on Sales Order and Payment Request Cancellation

## Objective
Deactivate Stripe Payment Links (`stripe.PaymentLink.modify(id, active=False)`) and expire open Stripe Checkout Sessions (`stripe.checkout.Session.expire(id)`) when a `Payment Request` or its associated `Sales Order` is cancelled in ERPNext.

## Context
When a `Payment Request` is submitted in `visaguy_crm`, `generate_payment_link` creates either a Stripe Payment Link (`plink_...`) or a Stripe Checkout Session (`cs_...`, for `Visaguy Website Visa Order`) with metadata (`reference_docname`, `reference_doctype`, `sales_order_id`). Previously, cancelling the `Payment Request` or `Sales Order` left the link active in Stripe, allowing customers to pay against cancelled documents.

## Inputs
- DocTypes: `Payment Request`, `Sales Order`, `Payment Gateway`, `Stripe Settings`
- Stripe Python SDK (`stripe` v10.12.0)

## Required behaviour
- Store `payment_link.id` / `session.id` in `custom_stripe_payment_link_id` on `Payment Request` when `generate_payment_link` executes on `before_submit`.
- When a `Payment Request` is cancelled (`on_cancel`) or a `Sales Order` is cancelled (`on_cancel`), deactivate the associated Stripe Payment Link (`active=False`) and expire any open Checkout Sessions.
- For legacy `Payment Request` records without `custom_stripe_payment_link_id`, fall back to listing active Payment Links / open Checkout Sessions and matching `metadata` (`reference_docname` / `sales_order_id`) or `url`.
- Catch any Stripe API errors and log/notify Accounts via `log_stripe_error_and_notify` without blocking ERPNext document cancellation.

## Constraints
- Standard DocType field customization on `Payment Request` must be stored in `visaguy_crm/visaguy_crm/custom/payment_request.json` (not fixtures) per ADR-004.
- Must be idempotent when both `Payment Request.on_cancel` and `Sales Order.on_cancel` run in the same request ("Cancel All Documents").
- Use safe flag access (`isinstance(frappe.flags.get(...), set)`) to prevent `TypeError: argument of type 'NoneType' is not iterable` due to `frappe._dict` returning `None` instead of raising `AttributeError`.

## Expected changes
- `visaguy_crm/visaguy_crm/custom/payment_request.json`: Add `custom_stripe_payment_link_id` custom field.
- `visaguy_crm/server_scripts/payment_from_lead/payment_request_hooks.py`: Store `custom_stripe_payment_link_id` in `generate_payment_link` and add `cancel_stripe_payment_link` + `deactivate_stripe_payment_link_for_pr`.
- `visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py`: Add `cancel_associated_stripe_payment_links`.
- `visaguy_crm/hooks.py`: Register `on_cancel` doc_events for `Sales Order` and `Payment Request`.

## Validation
- `Payment Request-custom_stripe_payment_link_id` Custom Field synced and verified in site `visaguy` database.
- Unit/integration test suite passed covering:
  - Storing `payment_link.id` / `session.id` on creation.
  - Direct deactivation of `plink_...` and expiration of open Checkout Sessions.
  - Same-request idempotency (`frappe.flags.deactivated_stripe_prs`).
  - Fallback metadata/URL lookup for legacy Payment Requests.
  - Sales Order `on_cancel` locating and deactivating all linked Payment Requests.
  - Non-blocking error handling via `log_stripe_error_and_notify`.
- Live test against `ACC-PRQ-2026-01059` verified and cache cleared.

## Definition of done
- Changes deployed to `visaguy_crm`, field synced, automated tests passing, and documentation recorded in workspace.
