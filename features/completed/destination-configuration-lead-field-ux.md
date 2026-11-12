---
id: FEAT-destination-configuration-lead-field-ux
title: Destination Configuration Lead Field UX
status: completed
priority: high
repositories:
  - the_visaguy
  - visaguy_crm
  - visaguy_frappe_crm
owners:
  - fasil
depends_on: []
created: 2026-10-28
updated: 2026-11-09
---

# Destination Configuration Lead Field UX

## Summary

Hide Visa Type and Visa Category on Lead (Desk) and CRM Lead (Frappe CRM Data tab) unless an active Destination Configuration exists for the lead's destination + `custom_zone` (matched to Destination Configuration `company`). Filter those lists to the configured pairs and auto-fill the default (`is_default`) pair. Filter applicant types from the matching configuration, then the default, then Destination `file_template` for the zone.

## User value

- Agents no longer see empty Visa Type / Visa Category dropdowns when a destination has no Destination Configuration for their zone.
- New leads start with the default visa category and type, so agents only change them when needed.
- Applicant types follow the selected Destination Configuration. When no configuration matches the visa pair and none is the default, the list uses Destination `file_template` for the lead zone. The same list is used when the destination has no Destination Configuration.

## Scope

### Included

- Shared whitelist API `get_lead_destination_config_options(destination, company)` on Destination Configuration.
- Desk Lead client script: hide/show, filter, auto-fill on `custom_destination` and `custom_zone` only.
- Frappe CRM Data tab Vue: same behaviour via a composable, Field/Grid/Link/GridRowModal wiring, `#customization` markers, and frontend rebuild.

### Excluded

- Visa centre RPA toggle, department auto-fetch, destination-change confirmation.
- Create Lead Quick Entry modal.
- Changing file-collection template resolution (still uses `Destination.file_template`).
- Re-exporting Lead / CRM Lead customizations or CRM Fields Layout (already done on site).

## Requirements

1. Lookup uses lead/CRM Lead `custom_zone` as Destination Configuration `company`. Never read `company` or `custom_company`.
2. API is called only when `custom_destination` or `custom_zone` changes (plus once on form load if both are already set).
3. Hide visa fields when no active dest-config exists; clear them. Show and filter when configs exist.
4. Auto-fill the `is_default` visa category + type on destination/zone change, or when current values are not in the allowed lists. Do not overwrite a valid saved pair on plain form load.
5. Applicant types come from the resolved dest-config `applicant_templates`; otherwise keep Destination.file_template.

## Proposed design

One whitelist API returns `has_config`, `configs` (category, type, is_default, applicant_types), `default`, and `fallback_applicant_types`. Desk JS and a Vue composable consume that payload. Frappe CRM Form Scripts cannot hide or filter fields, so the Data tab uses Vue provide/inject.

## Tasks

- [x] [TASK-implement-destination-configuration-lead-field-ux](../../tasks/completed/implement-destination-configuration-lead-field-ux.md)

## Acceptance criteria

1. Destination with no dest-config for that `custom_zone`: visa fields hidden on Desk and `/crm`; not an empty dropdown.
2. Destination with configs: fields visible; lists only those category/type pairs; default pair filled; agent can change to another allowed pair.
3. Changing `custom_destination` or `custom_zone` replaces invalid values with the new default (or clears if none). Lead `company` / `custom_company` must not trigger a fetch.
4. Applicant types follow the resolved dest config; destinations without dest-config keep the existing Destination.file_template filter.
5. Existing destination-change protection on Desk is unchanged.

## Dependencies

- Destination Configuration DocType in `the_visaguy`.
- Lead Desk form JS in `visaguy_crm`.
- Frappe CRM Data tab in `visaguy_frappe_crm`.

## Risks

- CRM Link filters will stay stale unless `Link.vue` watches `filters` (addressed in this feature).
- Repo custom JSON may still show old `depends_on`; site customizations are authoritative and must not be re-exported in this task.
- Implementation lives on remote `fasil-bench2` only; local bench trees were reverted. Promote to local/git before the next CRM frontend overlay on another bench.

## Open questions

None.

## Completion notes

Implemented on remote bench `fasil-bench2` (site `visaguy`, URL `https://visaguy-fsl.code.tridz.in`), 2026-10-29 through 2026-11-03:

- **source-wired** — API `get_lead_destination_config_options` on Destination Configuration (`the_visaguy`).
- **source-wired** — Desk Lead JS hide/filter/auto-fill on `custom_destination` / `custom_zone` (`visaguy_crm` `lead_doctype.js`).
- **source-wired** — Frappe CRM Data tab: `useDestinationConfiguration.js` + FieldLayout provide, Field/Grid/Link/GridRowModal wiring; each frontend edit wrapped with `#customization` / `#end_customization`.
- Frontend rebuilt on remote (`FieldLayout-d9fcdcf8.js` contains the API name; `crm.html` copied). Cache cleared; `frappe serve` restarted on port 8000.
- Local bench app copies of these changes were reverted so the work stays on the server.
- Overlay restore log updated: [`docs/architecture/frappe-crm-frontend-overrides.md`](../../docs/architecture/frappe-crm-frontend-overrides.md).
- Browser/runtime verification of dest-config presence against live lead data was **not** completed (**not** runtime-verified).

2026-11-06 fix — false "no File Template for applicant type Primary" when destination changes after files exist (for example France → Canada):

- **Cause:** the clients already clear or default the visa pair for the new destination. `resolve_lead_file_templates` used `visa_category_override or lead.custom_visa_category`, so an explicit `""` fell back to the saved France pair. Canada has no Destination Configuration for that pair, so the check reported Primary as missing.
- **Fix (no new helper):** the resolver respects an explicit `""` override (`None` still means "use the lead value"). `check_if_templates_are_same` accepts `old_zone` / `new_zone`. Without them, a zone change that autofills a new visa pair was checked against the old zone. `reset_and_regenerate_on_destination_change` passes `""` for empty old values so it does not compare against the new values.
- **Clients:** Desk Lead `before_save` now also checks visa changes, sends zone and visa values, and restores destination/zone/visa on cancel or missing template without dest-config autofill replacing the restored pair. Desk CRM Lead and the CRM Data tab (`leadDestinationChange.js`) send zone and restore zone. The composable keeps a valid restored pair after a revert and ignores stale dest-config responses.
- **Evidence:** `visaguy_crm.tests.test_template_resolution`, 27/27 pass (2 new regression tests). Live data `CRM-LEAD-2026-23584`: France → Canada with a cleared pair returns "templates differ" (confirm dialog). Zone TVG Saudi → TVG with the default pair returns "same". A stale France pair on Canada still returns `missing_template`. **source-wired**; browser flow not runtime-verified.
- The CRM side panel has no destination, zone, or visa fields, so it does not hit this path.

2026-11-09 fix — empty applicant Type list when a Destination Configuration exists, none is the default, and no visa pair is selected (France / TVG on CRM-LEAD-2026-23862):

- **Cause:** Desk Lead and the CRM Data tab used only the matching configuration or the default. Both were absent, so the Type filter matched nothing. France `file_template` for TVG still had Primary, Child, Spouse, and Secondary.
- **Fix:** when `has_config` is true but no configuration matches and there is no default, use `fallback_applicant_types`. A selected pair still uses that configuration. Changed `apply_applicant_types_from_dest_config` in `lead_doctype.js` and `applicantTypeFilters` in `useDestinationConfiguration.js`.
- **Evidence:** runtime-verified on CRM-LEAD-2026-23862. With visa fields cleared, the Type list shows Primary, Child, Spouse, and Secondary. Student / E-Visa limits the list to Primary. The user confirmed the dropdown.
