# ADR-006: Destination Configuration Template Resolution and Change Protection

## Status

Accepted

## Context

Visa application workflows generate `FF File Collection` and `PF Process File` records matching specific `Destination Configuration` templates. Each configuration defines templates mapped by Visa Category, Visa Type, and Applicant Type (e.g. Primary, Dependent, Student).

Previously:
1. Template resolution lacked fallback hierarchy, making it impossible to define granular configurations (such as Student Visa types) without duplicating broader rules.
2. Form fields offered static lists of visa types rather than options filtered by the chosen destination.
3. When an agent altered the destination or visa configuration on a lead where files had already been generated, backend hooks silently deleted the existing File Collections and Process Files and regenerated new ones without informing the agent.
4. In Frappe CRM's Vue SPA, lead details reside in the **Data Tab** (`DataFields.vue`), where edits are batched and saved via a manual "Save" button, while the Side Panel is used for quick profile attributes. Any safeguard had to intercept both the Data tab form submission and Desk form saves.

## Decision

1. **Centralize Template Resolution**: Implement `visaguy_crm.server_scripts.template_resolver` as the single authoritative resolver for File Templates and Process Templates across both `Lead` and `CRM Lead`.
2. **Apply 5-tier Fallback Hierarchy**:
   - `Zone + Visa Category + Visa Type`
   - `Destination + Visa Category + Visa Type`
   - `Visa Category + Visa Type`
   - `Destination + Visa Category`
   - `Visa Category`
3. **Dynamic Form Filtering**: Whitelist `get_allowed_visa_options`, `get_allowed_visa_types`, and `get_allowed_applicant_types` to filter available categories and types on destination selection.
4. **Enforce Missing Template Guard**: If a newly selected configuration lacks a template for any existing applicant type, reject save with an informative error toast and revert the selection.
5. **Intercept Destructive Destination Changes on All Interfaces**:
   - In Frappe CRM Data Tab ([`DataFields.vue`](file:///home/fasil/fasil-bench2/apps/visaguy_frappe_crm/frontend/src/components/Activities/DataFields.vue)): intercept `saveChanges` by comparing `data.doc` against `data.originalDoc`. If templates differ, display `createDialog`. Revert `data.doc` on Cancel; proceed with save on Proceed.
   - In Frappe CRM Side Panel ([`Lead.vue`](file:///home/fasil/fasil-bench2/apps/visaguy_frappe_crm/frontend/src/pages/Lead.vue)): maintain `lastConfig` baseline tracking to avoid in-place mutation race conditions.
   - In Frappe Desk ([`crm_lead_doctype.js`](file:///home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/public/js/doctype_js/crm_lead_doctype.js), [`lead_doctype.js`](file:///home/fasil/fasil-bench2/apps/visaguy_crm/visaguy_crm/public/js/doctype_js/lead_doctype.js)): halt `before_save` via `frappe.validated = false` and prompt via `frappe.confirm`. Revert on Cancel; set confirmed flag and save on Proceed.
6. **Form Link Preservation**: Store previous primary collection link in `CRM Lead.custom_form_link` during regeneration so applicants retain access without re-issuing links.

## Consequences

### Positive

- Prevents catastrophic accidental deletion of applicant documents and process files.
- Provides consistent user experience and safeguards across both Frappe CRM web interface and standard Desk views.
- Enables student visa workflows and granular visa configurations without breaking existing category-wide templates.
- Maintains 100% test coverage for template resolution rules.

### Negative

- Agents must re-create downstream Process Files manually after an intentional destination change, as process templates cannot be automatically mapped from different configurations.

## Alternatives considered

- **Backend-only throw without confirmation**: Would prevent all destination changes once files are generated, requiring administrator database intervention to change destinations.
- **Frontend-only modal in Lead.vue**: Failed in testing because Frappe CRM fields are placed in the Data tab (`DataFields.vue`) rather than the sidepanel, completely bypassing `Lead.vue` save events.
- **CRM Form Script (`CRM Form Script` DocType)**: Discarded because Frappe CRM's form script architecture only supports adding header action buttons and custom status options, with no lifecycle hooks for field edits or form validation.

## Revisit when

- Upstream Frappe CRM introduces native `before_save` form interceptor hooks across all tab layouts.
