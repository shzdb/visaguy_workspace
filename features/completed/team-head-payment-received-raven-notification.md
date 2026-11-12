---
id: FEAT-team-head-payment-received-raven-notification
title: Team Head Payment-Received Raven Notification
status: completed
priority: medium
repositories: [visaguy_raven]
owners: []
depends_on: []
created: 2026-10-28
updated: 2026-10-28
---

# Team Head Payment-Received Raven Notification

## Summary

When a Receive Payment Entry allocated against a Sales Invoice is submitted,
send an Accounts-bot Raven DM to the Team Head of the payment's sales person
saying that payment was received.

## User value

Team Heads are notified immediately when a payment is received against an
invoice for one of their sales people, without having to watch Payment Entry
lists or wait for a later accounts workflow.

## Scope

### Included

- `Payment Entry` `on_submit` handler in `visaguy_raven`.
- Recipient: Team Head of `custom_sales_person`. If the sales person is
  themselves an Employee Group `custom_team_head` (not listed in the member
  table), notify them. Otherwise resolve via group membership, same helper
  as credit-note notifications.
- Trigger only when `payment_type == "Receive"` and at least one `references`
  row is a Sales Invoice.
- Message includes amount, party, Payment Entry name, and the Lead / CRM Lead
  from `custom_reference_doctype` / `custom_reference_doc_name` when set.
  Sales Invoice rows on `references` are the trigger filter only; they are
  not listed in the message.
- Uses the existing Accounts bot (`send_accounts_notify`).

### Excluded

- Pay / Internal Transfer Payment Entries (refunds are Pay-type).
- Unallocated payments and wallet top-ups (no Sales Invoice reference).
- Broadcasting to every user with the Team Head role for the invoice company.
- New Raven Bot or Raven Document Notification records.
- `custom_is_return_invoice_refund` filter (redundant once Receive-only).

## Requirements

- Skip when `custom_sales_person` is empty or no Team Head is found
  (neither as `custom_team_head` nor as a group member).
- Enqueue the send with `enqueue_after_commit=True`.
- Do not change refund `on_update` handling or the credit-note Team Head lookup.

## Proposed design

See Completion Notes for the implemented architecture.

## Tasks

- [x] TASK-implement-team-head-payment-received-raven-notification

## Acceptance criteria

- [x] Receive PE with a Sales Invoice reference and `custom_sales_person` set
      notifies that sales person's Team Head.
- [x] Message includes paid amount, currency, party, Payment Entry name, and
      the Lead / CRM Lead (`custom_reference_doctype` /
      `custom_reference_doc_name`).
- [x] Receive PE with no Sales Invoice references does not notify.
- [x] Receive PE with no `custom_sales_person` does not notify.
- [x] Pay-type PE (including refunds) does not send this notification.
- [x] Existing refund-approval Raven path still fires on workflow `on_update`.
- [x] When the sales person is themselves the Team Head, they receive the DM.

## Dependencies

- `visaguy_raven` — Accounts bot and `send_accounts_notify`.
- `get_team_head_for_sales_person` in `visaguy_raven/functions/send_credit_note.py`.
- `Payment Entry.custom_sales_person`, `custom_reference_doctype`,
  `custom_reference_doc_name` (custom fields from `visaguy_crm`).
- Employee Group `custom_team_head`.

## Risks

- If the sales person is neither a `custom_team_head` nor a member of an
  Employee Group with a Team Head, the notification is silently skipped.

## Open questions

None — confirmed during implementation.

## Completion notes

### Implementation

New handler in `visaguy_raven`; existing Payment Entry refund `on_update` left
unchanged.

**`visaguy_raven/functions/send_payment_received.py`**

| Function | Role |
|---|---|
| `notify_team_head_payment_received(doc, method)` | `on_submit` entry-point. Returns unless `docstatus == 1`, `payment_type == "Receive"`, at least one Sales Invoice in `references`, and `custom_sales_person` is set. Enqueues the worker with `enqueue_after_commit=True`. |
| `_notify_team_head_payment_received(...)` | Queued worker. Resolves Team Head and sends one Accounts-bot DM. |
| `resolve_team_head_for_sales_person(sales_person)` | If the sales person is `Employee Group.custom_team_head`, return them. Otherwise use `get_team_head_for_sales_person`. |
| `_has_sales_invoice_reference(doc)` | True when any `references` row is a Sales Invoice. |

**Notification text:**
> Payment received: {paid_amount} {currency} from {party_name}. Payment Entry {name}. Against {custom_reference_doctype} {custom_reference_doc_name}.

The Against clause is omitted when the Lead / CRM Lead custom fields are empty.

**`visaguy_raven/hooks.py`** — Payment Entry events:

```python
"Payment Entry": {
    "on_update": "visaguy_raven.functions.send_refund.refund_approval_wf",
    "on_submit": "visaguy_raven.functions.send_payment_received.notify_team_head_payment_received",
},
```

### Verification

- Syntax-check and hook wiring: **source-wired**.
- Behaviour confirmed by requester (Receive + Sales Invoice, Lead/CRM Lead in
  message, Team Head including self-as-head, Pay/refunds excluded): **user-confirmed**.
- Live provider delivery: not separately runtime-verified.

### Repository

- **Repository:** `visaguy_raven`
- **Branch:** `team-head-payment`
- Uncommitted at workspace update (new handler + `hooks.py` `on_submit`).
