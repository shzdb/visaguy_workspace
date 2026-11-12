---
id: TASK-implement-team-head-payment-received-raven-notification
feature: FEAT-team-head-payment-received-raven-notification
title: Implement Team Head Payment-Received Raven Notification
status: completed
repository: visaguy_raven
owners: []
depends_on: []
expected_files:
  - visaguy_raven/functions/send_payment_received.py
  - visaguy_raven/hooks.py
created: 2026-10-28
updated: 2026-10-28
---

# Implement Team Head Payment-Received Raven Notification

## Objective

Create a `Payment Entry` `on_submit` Raven notification in `visaguy_raven` that
tells the Team Head of `custom_sales_person` that payment was received, but only
for Receive entries allocated against a Sales Invoice.

## Context

Team Heads need an immediate Accounts-bot DM when a sales person's invoice is
paid. Existing Payment Entry Raven handling only covers refund approval workflow
transitions on `on_update`.

Recipient resolution already exists for credit notes:
`get_team_head_for_sales_person` looks up the sales person's Employee Group and
returns `custom_team_head`. Team Heads themselves are not in the member table,
so payment-received also treats `custom_team_head` as a recipient.

## Inputs

- `Payment Entry.payment_type` — must be `Receive`.
- `Payment Entry.references` — at least one row with `reference_doctype == "Sales Invoice"`.
- `Payment Entry.custom_sales_person` — User link used to find the Team Head.
- `Payment Entry.custom_reference_doctype` / `custom_reference_doc_name` —
  Lead or CRM Lead the payment was made against; included in the message
  when set. Not Sales Invoice references.
- `get_team_head_for_sales_person` in `send_credit_note.py`.
- `send_accounts_notify` helper.

## Required behaviour

1. `on_submit` calls `notify_team_head_payment_received(doc, method)`.
2. Return early unless:
   - `docstatus == 1`
   - `payment_type == "Receive"`
   - at least one Sales Invoice reference
   - `custom_sales_person` is set
3. Enqueue `_notify_team_head_payment_received` with `enqueue_after_commit=True`.
4. Worker resolves Team Head via `resolve_team_head_for_sales_person`:
   if the sales person is `Employee Group.custom_team_head`, notify them
   (Team Heads are not in the member table); otherwise use
   `get_team_head_for_sales_person`. Then send one Accounts-bot DM.
5. Message format:
   `Payment received: {paid_amount} {currency} from {party_name}. Payment Entry {name}. Against {custom_reference_doctype} {custom_reference_doc_name}.`
   The Against clause is the Lead / CRM Lead on the Payment Entry custom
   fields, not the Sales Invoice rows in `references`. Omit Against when
   those fields are empty.

## Constraints

- Implement on existing branch `team-head-payment`.
- Must use existing `send_accounts_notify` — no new bot.
- Reuse `get_team_head_for_sales_person`; do not change that lookup.
- Do not change `send_refund.py` or Payment Entry `on_update`.
- Leave git changes unstaged; do not commit unless asked.

## Expected changes

- **[NEW]** `visaguy_raven/functions/send_payment_received.py`
- **[MODIFY]** `visaguy_raven/hooks.py` — add `Payment Entry.on_submit`

## Validation

- Syntax-check passed: `ast.parse()` on
  `visaguy_raven/functions/send_payment_received.py` — functions
  `notify_team_head_payment_received`, `_notify_team_head_payment_received`,
  and `resolve_team_head_for_sales_person` parsed; imports
  `send_accounts_notify` and `get_team_head_for_sales_person`.
- Hook wiring verified in `visaguy_raven/hooks.py`:
  `Payment Entry.on_update` still points at `refund_approval_wf`;
  `on_submit` points at `notify_team_head_payment_received`.
- Logic: Receive-only (Pay/refunds excluded by type), Sales Invoice
  `references` required as trigger only, `custom_sales_person` required,
  `enqueue_after_commit=True`. Message Against clause uses Lead / CRM Lead.
  Team Head who is the sales person is resolved via
  `Employee Group.custom_team_head` before member-table lookup.
- Requester confirmed behaviour ("all good"). Live Raven delivery not
  separately runtime-verified.

## Definition of done

- [x] New handler created and registered on `on_submit`.
- [x] Recipient is the sales person's Team Head, including when the
      sales person is the Team Head (not in the Employee Group member list).
- [x] Sales Invoice Receive filter applied.
- [x] Message includes Lead / CRM Lead reference doctype and name.
- [x] Syntax and hook wiring verified.
- [x] Feature and task documents recorded in workspace.
- [x] Requester confirmed behaviour.
