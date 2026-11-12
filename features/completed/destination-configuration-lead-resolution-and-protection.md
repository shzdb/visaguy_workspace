---
id: FEAT-destination-configuration-lead-resolution-and-protection
title: Destination Configuration Lead Template Resolution and Change Protection
status: completed
priority: high
repositories:
  - visaguy_crm
  - visaguy_frappe_crm
owners:
  - fasil
depends_on: []
created: 2026-10-22
updated: 2026-10-22
---

# Destination Configuration Lead Template Resolution and Change Protection

## Summary

Provides dynamic, hierarchical resolution of File Templates and Process Templates on `Lead` (ERPNext) and `CRM Lead` (Frappe CRM) based on Destination, Zone, Visa Category, Visa Type, and Applicant Type. Introduces dynamic visa option filtering on lead forms, enforces missing-template validation, and protects existing File Collections and Process Files with an interactive confirmation dialog (`createDialog` in Frappe CRM, `frappe.confirm` in Desk) whenever an agent modifies the destination or visa configuration.

## User value

- **Accuracy**: Ensures leads resolve the exact File Template and Process Template tailored to the applicant's visa type and category (including Student Visa Type), eliminating manual template misassignments.
- **Safety**: Prevents accidental data loss. Changing a lead's destination after file collection or process files are created is a destructive operation (deleting previous files and regenerating new ones). The system warns agents before executing deletions, allowing them to cancel and revert fields safely.
- **Form link continuity**: When regenerating a File Collection due to an authorized destination change, the existing primary public form link is preserved in `custom_form_link` so applicant access is uninterrupted.
- **Consistency**: The same safeguards and dynamic filtering operate uniformly whether agents use Frappe CRM (`/crm`) or standard Frappe Desk (`/app`).

## Scope

### Included

1. **Template Resolution Engine** ([`visaguy_crm.server_scripts.template_resolver`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_crm/visaguy_crm/server_scripts/template_resolver.py)):
   - Dynamic resolution of File Templates (`resolve_lead_file_templates`) and Process Templates (`resolve_lead_process_templates`).
   - Resolution hierarchy:
     1. `Zone + Visa Category + Visa Type`
     2. `Destination + Visa Category + Visa Type`
     3. `Visa Category + Visa Type`
     4. `Destination + Visa Category`
     5. `Visa Category`
   - Child table lookup in `Destination Configuration.visa_categories` matching applicant types.
   - Comprehensive unit test suite (25/25 tests passing).

2. **Dynamic Visa Options & Applicant Types Filtering**:
   - `get_allowed_visa_options`, `get_allowed_visa_types`, and `get_allowed_applicant_types` whitelisted endpoints.
   - Client scripts filtering dropdown options in Frappe Desk ([`crm_lead_doctype.js`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_crm/visaguy_crm/public/js/doctype_js/crm_lead_doctype.js), [`lead_doctype.js`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_crm/visaguy_crm/public/js/doctype_js/lead_doctype.js)).

3. **Destination Change Protection & Confirmation Dialog**:
   - Backend `check_if_templates_are_same` endpoint comparing old vs new template resolutions.
   - If templates are identical: saves silently without regeneration.
   - If template is missing for any applicant type: blocks save, reverts fields, and shows error notification.
   - If templates differ: prompts user confirmation warning that existing File Collection and Process Files will be deleted.
   - Reverts dropdowns/inputs if user cancels or closes dialog; executes save and regeneration on user confirmation.
   - Frappe CRM Data Tab support ([`DataFields.vue`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_frappe_crm/frontend/src/components/Activities/DataFields.vue)) via `handleDocumentConfigurationSave`.
   - Frappe CRM Side Panel support ([`Lead.vue`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_frappe_crm/frontend/src/pages/Lead.vue), [`MobileLead.vue`](file:///home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_frappe_crm/frontend/src/pages/MobileLead.vue)) via `handleConfigurationChange` with `lastConfig` baseline tracking.
   - Frappe Desk support via `before_save` (`frappe.validated = false`), `frappe.confirm`, and `after_save` state refreshes.

4. **Regeneration & Form Link Preservation**:
   - `reset_and_regenerate_on_destination_change` in `visaguy_crm/server_scripts/lead/lead_hooks.py` preserves primary form link in `custom_form_link` across regeneration.

### Excluded

- Modifying core upstream apps (`crm` or `frappe`).
- Automated re-creation of downstream Process Files (agents manually recreate them under the new destination template).

## Tasks

- [x] [TASK-implement-destination-configuration-resolution-and-protection](file:///home/fasil/Tridz/visaguy_workspace/tasks/completed/implement-destination-configuration-resolution-and-protection.md)

## Acceptance Criteria

1. Changing destination or visa configuration on a lead with no files generated proceeds silently without prompts.
2. Changing destination to one that resolves to identical file templates saves silently without deleting or regenerating files.
3. Changing destination where any applicant type lacks a configured template raises a validation error, reverts the configuration, and blocks saving.
4. Changing destination where templates differ triggers a confirmation dialog on both Frappe CRM Data tab and Desk form view.
5. Cancelling the confirmation dialog leaves previous values intact without saving.
6. Confirming the dialog deletes old files, generates new File Collections, and preserves the public form link.
7. Unit test suite passes without regressions.
