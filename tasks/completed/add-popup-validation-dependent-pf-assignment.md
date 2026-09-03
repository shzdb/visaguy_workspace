---
id: TASK-add-popup-validation-dependent-pf-assignment
feature: null
title: Add Popup Validation for Dependent PF Assignment
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - allocated_to_process_file.py
  - pf_process_file_doctype.js
created: 2026-09-03
updated: 2026-09-03
---

# Add Popup Validation for Dependent PF Assignment

## Objective
Introduce a frontend confirmation popup when an Operations Manager assigns a Primary Process File that has dependent process files linked, prompting them to choose whether to assign the dependent files to the same consultant.

## Context
Previously, assigning a Primary PF Process File automatically assigned any linked dependent process files to the same consultant via a backend `after_insert` hook on the `ToDo` doctype (`visaguy_crm.allocated_to_process_file.allocated_user_to_process_file`). This silent auto-assignment did not allow the Operations Manager to opt-out.

## Inputs
- DocType: `PF Process File`
- Fields: `custom_dependent_details`, `custom_type`, `custom_designated_to`

## Required behaviour
- When a `ToDo` is created (assignment) for a Primary PF Process File, check if there are unassigned dependent process files.
- If unassigned dependents exist, emit a realtime event `pf_prompt_dependent_assign` back to the user instead of automatically assigning them.
- A frontend listener catches the event and displays a confirmation dialog with the consultant's name in bold: *"There are dependent process files linked to {process_file}. Do you want to assign them to the same consultant **{allocated_to}**?"*
- If confirmed, trigger a backend whitelist method `assign_dependent_process_files` to perform the dependent assignment manually.

## Expected changes
- `visaguy_crm/visaguy_crm/allocated_to_process_file.py`: Updated `allocated_user_to_process_file` to use `frappe.publish_realtime` instead of direct assignment, and added `@frappe.whitelist()` method `assign_dependent_process_files`.
- `visaguy_crm/public/js/doctype_js/pf_process_file_doctype.js`: Appended a realtime listener for `pf_prompt_dependent_assign` to handle the `frappe.confirm` dialog and backend callback.

## Validation
- Verified the backend event publication.
- Verified the frontend dialog triggers on the correct event.
- Verified the explicit manual assignment works after user confirmation.

## Definition of done
- The Python and JavaScript code in the remote `visaguy_crm` application is updated, pushed to `upstream/main`, and `bench clear-cache` is executed.
