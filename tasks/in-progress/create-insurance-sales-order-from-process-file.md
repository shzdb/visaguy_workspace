---
id: TASK-create-insurance-sales-order-from-process-file
feature: FEAT-insurance-sales-order-from-process-file
title: Create an insurance Sales Order from a process file
status: in-progress
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - visaguy_crm/server_scripts/payment_from_lead/convenience_fee_calculation.py
  - visaguy_crm/server_scripts/payment_from_lead/prepare_sales_order_data.py
  - visaguy_crm/server_scripts/payment_from_lead/sales_order_hooks.py
  - visaguy_crm/server_scripts/payment_from_lead/sales_invoice_hooks.py
  - visaguy_crm/server_scripts/payment_from_lead/insurance_sales_order.py
  - visaguy_crm/public/js/payment_from_lead/auto_add_convenience_fee.js
  - visaguy_crm/public/js/payment_from_lead/generate_sales_order_for_lead.js
  - visaguy_crm/public/js/doctype_js/pf_process_file_doctype.js
  - visaguy_crm/visaguy_crm/doctype/tvg_crm_settings/tvg_crm_settings.json
  - visaguy_crm/visaguy_crm/custom/sales_order.json
  - visaguy_crm/hooks.py
  - visaguy_crm/fixtures/role.json
  - visaguy_crm/patches.txt
  - visaguy_crm/patches/set_default_convenience_fee_item.py
created: 2026-11-10
updated: 2026-11-12
---

# Create an insurance Sales Order from a process file

## Objective

Add an insurance Sales Order action on PF Process File. Read the convenience fee item from TVG CRM Settings.

## Context

The fee item code was the fixed string Convenience Fee. The insurance order must use one global item, the Lead zone price list, and the designated operations user. Role Operations Invoice - TVG is the only role for the button. The session user must be custom_designated_to.

The same user also has Operations Associate or Operations Team Lead. Those roles can write PF Process File.

## Inputs

- App visaguy_crm on the SSH bench, site visaguy.
- TVG CRM Settings fields default_convenience_fee_item and default_insurance_item.
- PF Process File fields custom_create_sales_order and custom_insurance_sales_order.
- Role Operations Invoice - TVG.

## Required behaviour

- One helper returns the fee item and throws when the setting is empty.
- Lead, Sales Order, Sales Invoice, and the desk fee script use that helper.
- The whitelist checks the role, the designated user, the Employee flags, the Lead, the insurance item, and the Item Price.
- The Sales Order insert and the process-file save check the session user's permissions. They do not set ignore_permissions.
- Operations Invoice - TVG has Sales Order read, write, create, and submit.
- The Lead button and the process-file button use frappe.call freeze. They do not open a progress dialog.

## Constraints

- Edit application code only on the SSH bench. Do not commit. Leave changes unstaged.
- Do not add a Custom DocPerm fixture. Put the Sales Order perm in custom/sales_order.json.
- Do not create a second role. Do not invent an Item.
- Do not change create_payment_request_and_submit.
- Do not revert unrelated dirty files.

## Expected changes

- Settings JSON gains the two Link fields on the Accounts tab.
- A patch sets Default Convenience Fee Item to Convenience Fee when the field is empty and that Item exists.
- Role fixture and hooks.py list Operations Invoice - TVG.
- custom/sales_order.json grants the role the same Sales Order rights as Consultant Invoice - TVG.
- New whitelist insurance_sales_order.create_insurance_sales_order.
- Process file client script shows the button only for the role, and hides it while the linked order is not cancelled.
- The desk fee script calls get_default_convenience_fee_item. It does not call get_single_value on TVG CRM Settings.
- generate_sales_order_for_lead.js and the process-file button use freeze.

## Validation

Checked on 2026-11-10, then updated on 2026-11-12. The task stays in progress.

- **present** Settings fields are in the DocType JSON and in tabDocField after migrate.
- **present** Role Operations Invoice - TVG is in role.json and in the database once.
- **source-wired** The fee helper is called from the lead builder, both item hooks, and the fee calculation.
- **source-wired** The desk bundle calls get_default_convenience_fee_item. The last build wrote visaguy_crm.bundle.EPF46EIC.js. The next build changes that name.
- **source-wired** The process file button and the Lead button call their whitelists with freeze and route to the Sales Order.
- **source-wired** insurance_sales_order.py has no ignore_permissions. insert, Sales Order save, and process-file save use the session user.
- **runtime-verified** default_convenience_fee_item is Convenience Fee.
- **runtime-verified** default_insurance_item is Travel Insurance fee 7 days. Checked on 2026-11-12.
- **runtime-verified** The helper throws ValidationError when the fee setting is empty. The live value was restored.
- **runtime-verified** The patch calls set_single_value with Convenience Fee when the setting is empty. The live row was not cleared.
- **runtime-verified** Guest is rejected with PermissionError. No Sales Order was created.
- **runtime-verified** Empty designated user, wrong user, missing Employee, non-lead reference, missing price list, empty insurance item, and missing Item Price each throw. An open linked order is rejected. A cancelled link is allowed.
- **runtime-verified** Custom DocPerm for Operations Invoice - TVG on Sales Order has read, write, create, submit, and cancel.
- **configured-unverified** The desk error for an empty Designated To was seen before the freeze change. The progress dialog stayed after that error was closed. The freeze change was not clicked again.
- bench --site visaguy migrate, bench build --app visaguy_crm, and bench --site visaguy clear-cache completed. Workers were not restarted on 2026-11-10.

## Definition of done

- [ ] A click on a real process file creates one insurance Sales Order and the file stores that name.
- [ ] Submit of that order runs the Zoho item check.
- [ ] A desk user who cannot read TVG CRM Settings can change the fee percent and the fee row still updates.
- [ ] An error on the Lead button and the process-file button clears the freeze and leaves no progress dialog.
- [x] Source, migrate, and the checks above are recorded.
- [x] Git changes on visaguy_crm are unstaged.
