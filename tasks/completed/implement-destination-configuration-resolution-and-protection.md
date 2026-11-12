---
id: TASK-implement-destination-configuration-resolution-and-protection
feature: FEAT-destination-configuration-lead-resolution-and-protection
title: Implement Destination Configuration Template Resolution and Change Protection
status: completed
repository: visaguy_crm
owners:
  - fasil
depends_on: []
expected_files:
  - visaguy_crm/server_scripts/template_resolver.py
  - visaguy_crm/server_scripts/lead/lead_hooks.py
  - visaguy_crm/file_collection_from_lead.py
  - visaguy_crm/allocated_to_process_file.py
  - visaguy_crm/public/js/doctype_js/crm_lead_doctype.js
  - visaguy_crm/public/js/doctype_js/lead_doctype.js
  - visaguy_crm/tests/test_template_resolution.py
  - visaguy_frappe_crm/frontend/src/utils/leadDestinationChange.js
  - visaguy_frappe_crm/frontend/src/components/Activities/DataFields.vue
  - visaguy_frappe_crm/frontend/src/pages/Lead.vue
  - visaguy_frappe_crm/frontend/src/pages/MobileLead.vue
  - visaguy_frappe_crm/frontend/src/utils/dialogs.jsx
created: 2026-10-22
updated: 2026-10-22
---

# Implement Destination Configuration Template Resolution and Change Protection

## Objective

Build a unified template resolution engine supporting granular visa options (including Student Visa Type), dynamically filter form options on Lead and CRM Lead, validate required templates, and prevent silent file regeneration during destination changes by adding confirmation dialogs across both Frappe CRM frontend and standard Frappe Desk.

## Context

Destination configurations configure File Templates and Process Templates per visa category, visa type, and applicant type (e.g. Primary, Dependent, Student). Previously, template resolution lacked fallback priority, option lists were static, and when an agent updated the destination on an existing lead, the backend hook (`reset_and_regenerate_on_destination_change`) deleted existing File Collections and Process Files silently without prompting. In Frappe CRM, fields live in the Data Tab (`DataFields.vue`), where edits save via an explicit "Save" button without going through sidepanel watchers.

## Inputs

- DocTypes: `Lead`, `CRM Lead`, `Destination Configuration`, `FF File Collection`, `PF Process File`
- Apps: `visaguy_crm`, `visaguy_frappe_crm`
- Verification standard: 25 automated unit tests + runtime browser and desk verification.

## Required Behaviour

1. **Hierarchical Template Resolution**:
   - `resolve_lead_file_templates(doc)` and `resolve_lead_process_templates(doc)` evaluate:
     1. `Zone + Visa Category + Visa Type`
     2. `Destination + Visa Category + Visa Type`
     3. `Visa Category + Visa Type`
     4. `Destination + Visa Category`
     5. `Visa Category`
   - Maps each applicant type from the child table to its corresponding file template.

2. **Template Comparison Endpoint**:
   - `check_if_templates_are_same(lead_name, doctype, old_destination, new_destination, ...)` returns:
     - `{"status": "missing_template", "missing_type": ...}` if new config lacks a template for any applicant type.
     - `True` if all templates are identical.
     - `False` if any template differs.

3. **Frontend Interception in Frappe CRM**:
   - In `DataFields.vue` (`saveChanges`): compares `data.doc` vs `data.originalDoc`. If destination/visa configuration changed and files exist, queries `check_if_templates_are_same`.
   - On missing template: halts save, reverts fields, displays error toast.
   - On identical templates: saves silently.
   - On differing templates: renders `createDialog` warning user of deletion. On Cancel, restores fields without saving. On Proceed, submits save and reloads lead.
   - In `Lead.vue` & `MobileLead.vue`: tracks `lastConfig` baseline to prevent in-place mutation race conditions in sidepanel controls.

4. **Desk Form Interception**:
   - In `crm_lead_doctype.js` and `lead_doctype.js`: `before_save` detects changes against `frm._last_*` baseline and halts save via `frappe.validated = false`.
   - Queries `check_if_templates_are_same` and prompts via `frappe.confirm`. Reverts fields on cancel; saves on proceed.
   - Updates `frm._last_*` and resets confirmed flag in `after_save`.

5. **Form Link Continuity**:
   - `reset_and_regenerate_on_destination_change` stores previous primary collection link in `doc.custom_form_link` so regenerated collections keep the existing link accessible.

## Validation

- **Unit tests**: `visaguy_crm/tests/test_template_resolution.py` ran with 25 passing test cases.
- **Frontend bundle**: Built cleanly via `yarn build && yarn copy-html-entry` with output verified in `www/crm.html`.
- **Desk scripts**: Verified present in Desk form `__js` bundle.

## Definition of Done

- All template resolution scenarios tested and passing.
- Destination change prompts confirmation modal before deleting/regenerating files.
- Cancel cleanly reverts inputs without saving.
- Form link preserved on regeneration.
- Redundant stub files removed.
