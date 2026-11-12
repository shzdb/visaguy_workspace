---
id: TASK-implement-destination-configuration-lead-field-ux
feature: FEAT-destination-configuration-lead-field-ux
title: Implement Destination Configuration Lead Field UX
status: completed
repository: the_visaguy
owners:
  - fasil
depends_on: []
expected_files:
  - the_visaguy/tvg_core/doctype/destination_configuration/destination_configuration.py
  - visaguy_crm/public/js/doctype_js/lead_doctype.js
  - visaguy_frappe_crm/frontend/src/composables/useDestinationConfiguration.js
  - visaguy_frappe_crm/frontend/src/components/FieldLayout/FieldLayout.vue
  - visaguy_frappe_crm/frontend/src/components/FieldLayout/Field.vue
  - visaguy_frappe_crm/frontend/src/components/Controls/Grid.vue
  - visaguy_frappe_crm/frontend/src/components/Controls/GridRowModal.vue
  - visaguy_frappe_crm/frontend/src/components/Controls/Link.vue
created: 2026-10-28
updated: 2026-11-09
---

# Implement Destination Configuration Lead Field UX

## Objective

Hide, filter, and auto-fill Visa Type / Visa Category on Desk Lead and Frappe CRM Data tab from Destination Configuration for destination + `custom_zone`. Filter applicant types from the matching configuration, then the default, then Destination `file_template` for the zone.

## Context

Visa fields currently appear as soon as a destination is selected. When no Destination Configuration exists for that destination and zone, agents see empty lists. Frappe CRM does not run Desk client scripts; CRM Form Scripts cannot hide or filter fields.

## Inputs

- DocTypes: Lead, CRM Lead, Destination Configuration, Applicant Type, Visa Category, Visa Type
- Apps: `the_visaguy`, `visaguy_crm`, `visaguy_frappe_crm`
- Lookup: `custom_zone` of the lead is Destination Configuration `company`
- Implementation target: remote bench `/home/fasil/fasil-bench2` on `code.tridz.in:2203`, site `visaguy`

## Required behaviour

1. Whitelist `get_lead_destination_config_options(destination, company)` returning `has_config`, `configs`, `default`, and `fallback_applicant_types`.
2. Desk: call only from `custom_destination` / `custom_zone` (and once on load if both are set). Hide visa fields without config; filter and auto-fill with config.
3. CRM Data tab: composable watches `custom_destination` + `custom_zone`; Field/Grid apply visibility and filters; Link reloads when filters change; GridRowModal passes `:doctype` so nested FieldLayout does not wrongly provide dest-config.
4. Applicant types: use the configuration that matches the selected visa pair. If none matches, use the default configuration. If there is no default, use `fallback_applicant_types` from Destination `file_template` for the zone. This applies when a Destination Configuration exists and when it does not.

## Constraints

- Do not use `company` or `custom_company`.
- Do not re-export Lead / CRM Lead customizations or CRM Fields Layout.
- Do not change `get_visa_types`.
- Do not modify destination-change protection.
- Apply on remote bench; keep local bench app trees free of these patches (workspace docs only).

## Expected changes

- `the_visaguy/.../destination_configuration.py`: new whitelist method.
- `visaguy_crm/.../lead_doctype.js`: hide/filter/auto-fill.
- `visaguy_frappe_crm` Vue: composable + FieldLayout/Field/Grid/GridRowModal/Link + `#customization` markers + rebuild.
- Workspace: feature/task completion + [`docs/architecture/frappe-crm-frontend-overrides.md`](../../docs/architecture/frappe-crm-frontend-overrides.md).

## Validation

- **source-wired** (remote `fasil-bench2`, checked 2026-11-04):
  - `get_lead_destination_config_options` present in `destination_configuration.py`.
  - Desk `lead_doctype.js` calls that method.
  - `useDestinationConfiguration.js` present; FieldLayout/Field/Grid/Link/GridRowModal contain `#customization` / `#end_customization` markers.
  - Built asset `FieldLayout-d9fcdcf8.js` includes the API method name; `crm.html` copy step ran.
- `bench --site visaguy clear-cache` succeeded; `frappe serve` listening on port 8000 after restart.
- Browser/runtime check of the original hide, filter, and auto-fill flow: **not** done on 2026-11-04 (**not** runtime-verified then).
- Local bench copies of the same app files were restored/removed after remote apply.
- **2026-11-09 runtime-verified** on CRM-LEAD-2026-23862 (France, zone TVG). No visa pair was selected and France / TVG has no default configuration. The applicant Type list showed Primary, Child, Spouse, and Secondary. Student / E-Visa limited the list to Primary. Desk `apply_applicant_types_from_dest_config` and CRM `applicantTypeFilters` both use `fallback_applicant_types` in that case. The user confirmed the dropdown. Frontend rebuilt (`FieldLayout-f776cf69.js`). Cache cleared.

## Definition of done

- Shared API, Desk JS, and CRM Data tab all use destination + `custom_zone`.
- Frontend bundle rebuilt on remote.
- Frontend edits marked with `#customization` / `#end_customization`.
- Workspace feature and this task describe the implemented behaviour and evidence labels.
- Overlay restore log lists the new/edited frontend files.
