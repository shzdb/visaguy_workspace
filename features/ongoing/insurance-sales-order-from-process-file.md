---
id: FEAT-insurance-sales-order-from-process-file
title: Insurance Sales Order from a process file
status: ongoing
priority: high
repositories: [visaguy_crm]
owners: ["fasil"]
depends_on: []
created: 2026-11-10
updated: 2026-11-12
---

# Insurance Sales Order from a process file

## Summary

An operations user creates one insurance Sales Order from a PF Process File. The insurance item and the convenience fee item come from TVG CRM Settings. The rate comes from the Lead zone price list. Quantity is 1.

## User value

The designated operations user can raise the insurance order without the lead consultant. The fee item is a setting. A rename of the Item does not require a code change.

## Scope

### Included

- Default Convenience Fee Item and Default Insurance Item on the Accounts tab of TVG CRM Settings.
- Payment paths read the fee item from that setting.
- Button Create Insurance Sales Order on PF Process File.
- Role Operations Invoice - TVG can read, write, create, and submit a Sales Order.
- The Lead and process-file buttons freeze the page while the Sales Order is created.

### Excluded

- A new Item record.
- A change to Send Payment Request.
- A second insurance order while the linked Sales Order is not cancelled.
- Use of the lead consultant as the sales person.

## Requirements

1. The fee item is TVG CRM Settings.default_convenience_fee_item. An empty value throws a clear message.
2. The insurance item is TVG CRM Settings.default_insurance_item. Quantity is 1. The rate is the Item Price on the Lead zone price list. Rate 0 is not used.
3. Company and sales person come from the Employee of PF Process File.custom_designated_to.
4. Only role Operations Invoice - TVG can use the button. The session user must be custom_designated_to.
5. The Sales Order reference stays Lead or CRM Lead so Send Payment Request still uses the Lead email.
6. Sales Order insert and the process-file save use the session user's permissions.

## Proposed design

One helper returns the fee item from TVG CRM Settings. The lead Sales Order, the Sales Invoice hook, the fee calculation, and the desk script call that helper. The desk script calls a whitelist. It does not read the settings form.

A whitelist on PF Process File builds one Sales Order with the same tax, mode of payment, and convenience charge helpers as the lead path. It inserts the order and stores the name on custom_insurance_sales_order.

The Employee must have an invoice company, sales person enabled, and a Zoho sales person id. The Lead must have a zone, a default price list, and a customer.

The caller also has Operations Associate or Operations Team Lead. Those roles can write PF Process File. The save of custom_insurance_sales_order uses that write permission.

## Tasks

- [ ] [TASK-create-insurance-sales-order-from-process-file](../../tasks/in-progress/create-insurance-sales-order-from-process-file.md)

## Acceptance criteria

- [x] The fee helper throws when Default Convenience Fee Item is empty.
- [x] A user without Operations Invoice - TVG cannot call the whitelist.
- [ ] The button is hidden when the linked Sales Order is not cancelled. The client rule is in source. A desk check is still open.
- [ ] The created Sales Order uses the designated user, the Lead customer, and the zone price list. The server checks exist. A live insert was not run.
- [ ] Submit still runs the existing Zoho item check.

## Dependencies

- TVG CRM Settings
- PF Process File fields custom_create_sales_order and custom_insurance_sales_order
- Role Operations Invoice - TVG
- Operations Associate or Operations Team Lead on the same user, for PF Process File write
- Item Convenience Fee for sites that already use that fee item

## Risks

- validate_zoho_compatibility runs on Sales Order before_submit. Insert does not run it. Submit throws when a Zoho Item ID is missing for the invoice company.
- The insurance item still needs an Item Price on the Lead zone price list. A missing price throws. That price row was not checked.
- Background workers keep the previous fee code until the next worker start. The live fee item is still Convenience Fee, so the fee row stays that Item until the setting changes.

## Open questions

None. The product decisions are closed.

## Completion notes

Bench code is in place on visaguy_crm. Git changes are unstaged. A live insurance Sales Order was not created. The task stays in progress.
