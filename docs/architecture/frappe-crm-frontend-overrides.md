---
title: Frappe CRM frontend overrides
status: living
created: 2026-10-31
updated: 2026-11-09
evidence_date: 2026-11-09
---

# Frappe CRM Frontend Overrides

Living restore log for VisaGuy patches in `visaguy_frappe_crm/frontend` after overlaying a newer `crm/frontend`.

This workspace is authoritative for **intent and restore steps**. The `visaguy_frappe_crm` git history is authoritative for **source**. Do not paste full Vue files here.

Mandatory update rule: [`.agents/rules/frappe-crm-frontend-overrides.md`](../../.agents/rules/frappe-crm-frontend-overrides.md). Update this file in the **same task** as any add, edit, delete, or re-apply under `visaguy_frappe_crm/frontend` (except `node_modules` / `dist`).

## How to update

When you change the Frappe CRM Vue overlay:

1. Read this file first.
2. Update **feature groups** if the product behaviour changed.
3. Add, change, or remove the matching **file inventory** entry. Do not leave a stale path.
4. Update **known gaps** if you close or add one.
5. Set frontmatter `updated` and `evidence_date`. Append a line to **Change log**.
6. Do not mark the implementation task complete until this file matches the source.

Required fields for every new or changed inventory entry:

| Field | What to record |
|---|---|
| Date and evidence | App, branch, HEAD, and what changed |
| Kind | `new file` / `edited upstream` / `build-path` |
| Paths | Relative to `visaguy_frappe_crm/frontend/` |
| Markers | Exact `Customization` / `Customizations` / `Customize` comment text, or **none** |
| Restore | Behaviour enough to re-patch after overlay (not a full diff) |
| Wiring | Backend methods, provide/inject, emits |
| Desktop vs mobile | Only if they differ |
| Verification | **present** / **source-wired** / **runtime-verified** |

Entry template (copy into the matching inventory section):

```markdown
#### `src/path/File.vue`

- **Date / evidence:** YYYY-MM-DD; `visaguy_frappe_crm` HEAD `…`; brief change
- **Kind:** edited upstream | new file | build-path
- **Markers:** `Customization: …` (or none)
- **Restore:** …
- **Wiring:** …
- **Desktop vs mobile:** …
- **Verification:** source-wired
```

Prefer new files under `src/components/custom/` and dedicated stores over editing upstream Vue. Every edit to an upstream file must have a marker comment.

## Purpose

Stock Frappe CRM does not cover several ERPNext Lead flows VisaGuy still needs: assign-on-create, duplicate-lead reason, send file-collection form, create process file, Desk links from child tables, zone-based mobile country code, Data-tab reload after those actions, and a trimmed nav.

The intended overlay sequence is:

1. Pull upstream into the `crm` `visaguy` branch.
2. Copy `crm/frontend` over `visaguy_frappe_crm/frontend`.
3. Restore the files and patches listed here (copy **new files** from git; re-patch **edited** files from Restore steps).
4. Rebuild the custom bundle and verify `/crm`.

## Evidence snapshot

Baseline comparison (2026-10-31) is from the **local bench**, not the remote `fasil-bench2` site.

| App | Path | Branch | HEAD | Remote |
|---|---|---|---|---|
| `crm` | `/home/fasil/Tridz/bench_v15/frappe-bench/apps/crm` | `visaguy` | `a2612ab` (`build(deps): bump frappeui to 0.1.119`) | `upstream` → `https://github.com/tridz-dev/frappe-crm.git` |
| `visaguy_frappe_crm` | `/home/fasil/Tridz/bench_v15/frappe-bench/apps/visaguy_frappe_crm` | `main` | `a2aa38b` (`Merge pull request #33 from tridz-dev/perms`) | `upstream` → `https://github.com/tridz-dev/visaguy_frappe_crm.git` |

Comparison: `diff -rq` on both `frontend/` trees, excluding `node_modules` and `dist`.

Verification labels:

- **present** — file or symbol exists in source.
- **source-wired** — import, provide/inject, emit, or API URL is evidenced in code.
- **configured-unverified** — bench/app config observed as names only; serving `/crm` from the custom bundle was not verified.
- **runtime-verified** — live `/crm` traffic or provider call confirmed.

`git ls-remote --symref upstream HEAD` on the `crm` clone reports default branch **`develop`**. A later merge should confirm whether maintainers want `develop` or `main` before pulling.

## How to restore after overlay

After copying `crm/frontend` onto `visaguy_frappe_crm/frontend`:

1. Copy the **new files** as-is from `visaguy_frappe_crm` git (do not reconstruct from memory).
2. Re-apply each **edited-file** behaviour. Search for the listed marker comments; they are the intended patch anchors.
3. Restore **build/path** retargeting so the bundle lands in `visaguy_frappe_crm`, not `crm`.
4. Run `yarn build` in `visaguy_frappe_crm/frontend`. `components.d.ts` should regenerate with the three custom components.
5. Do **not** treat the known-gap items as already implemented.

Do not confuse VisaGuy comments with upstream `setupCustomizations` / `setupListCustomizations` in `src/utils/index.js`. That helper is identical in `crm` and is not a VisaGuy patch.

## Marker convention

VisaGuy patches are marked with HTML/JS comments containing **Customization**, **Customizations**, or **Customize**.

**Dest-config field UX** (and new upstream edits going forward) wrap each edit with `#customization` at the start and `#end_customization` at the end:

- Script / JS: `// #customization` … `// #end_customization`
- Template: `<!-- #customization -->` … `<!-- #end_customization -->`

Older baseline patches often use a single `Customizations: …` line above the change and may omit an end marker. Some baseline patches have no marker (`MobileLead.vue` Convert hide, `NoteArea.vue` title color, ListViews `selectionsChanged`, `users.js` `userZone`). Restore those from the file entries below. New upstream edits must use the `#customization` / `#end_customization` pair.

## Change log

- **2026-11-09** — Applicant Type list when no visa pair is selected. `applicantTypeFilters` in `useDestinationConfiguration.js` uses `fallback_applicant_types` when a Destination Configuration exists, no pair matches, and none is the default. A selected pair still uses that configuration. Frontend rebuilt. Runtime-verified on CRM-LEAD-2026-23862 (France, zone TVG).
- **2026-11-06** — Destination-change fix on remote. `useDestinationConfiguration.js` exports `keepVisaPairOnNextChange` (revert keeps the restored pair) and ignores stale responses. `src/utils/leadDestinationChange.js` sends `old_zone` / `new_zone` to `check_if_templates_are_same` and restores `custom_zone` on revert, wrapped in `#customization` / `#end_customization`. Frontend rebuilt.
- **2026-11-04** — Workspace feature/task promoted to completed for dest-config field UX (remote **source-wired**, not runtime-verified). Related doc links updated.
- **2026-11-03** — Dest-config field UX **source-wired** on remote `fasil-bench2` (`visaguy_frappe_crm` branch `student-visa`, base HEAD `f16eba7`, uncommitted). Wrapped every frontend edit with `#customization` / `#end_customization`. Closed the dest-config known gap for this overlay log.
- **2026-10-31** — Seeded from the 2026-10-31 frontend-vs-`crm` diff. Promoted from research to this living architecture doc.

## Feature groups

These diffs exist to close ERPNext Lead gaps that stock Frappe CRM does not have.

### Assign on create

**source-wired.** Create-lead modal includes `CustomAssignTo`. After `CRM Lead` insert, the modal inserts a `ToDo` (`frappe.client.insert`) with `reference_type = CRM Lead`. Zone for country-code / assign UI comes from `users.js` `userZone` → `visaguy_frappe_crm.functions.apis.get_zone_details.get_zone_details`.

### Duplicate-lead reason

**source-wired.** Create modal navigates to the lead page with `?new_lead=true`. `DuplicateLeadDialog.vue` watches that query, calls `visaguy_frappe_crm.functions.apis.check_duplicate_lead.check_duplicate_lead`, and if another lead shares the mobile number, requires `custom_duplicate_reason` before the dialog can close.

### File collection / process file

**source-wired.** Pinia store `leadForm.js` calls `visaguy_crm` APIs:

- Send Form: `visaguy_crm.file_collection_from_lead.generate_file_collection_lead` with `{ doctype: "CRM Lead", lead_name }`. Requires lead `email`. Rendered on the applicant child table (`CRM Lead-custom_applicant_information`).
- Create Process File: `visaguy_crm.allocated_to_process_file.create_process_file`. Desktop header button shows only when `lead.data.status === 'Payment Confirmed'`.
- `FormSubmittingOverlay.vue` covers the page while `submitting` is true.

### Child-table links to Desk

**source-wired.** In `Grid.vue`, Link cells named `process_file` or `file_collection` are not autocomplete. They render as `<a target="_blank">` to `/app/pf-process-file/{id}` and `/app/ff-file-collection/{id}`. File-collection cells skip the generic read-only `FormControl`. Localhost origin is rewritten to `https://localhost:8080`.

### Mobile country code

**source-wired.** On Field mount, if `mobile_no === ''` and `userZone.data.mobile_country_code` is set, prefills `mobile_no` from the session user's Zone.

### Data tab reload

**source-wired.** `Lead.vue` provides `registerReloadDataTab` and `reloadDataTab`. `DataFields.vue` registers `data.reload` on mount. Send Form and Create Process File call that callback. A deep watch on `data.doc` sets `data.isDirty` when the document diverges from `data.originalDoc` so sidebar edits re-enable Save.

### UI hide / nav trim

**source-wired.** Desktop lead page hides Convert to Deal (button + dialog), the email composer icon, and the Emails tab. Mobile lead page hides Convert only. Sidebars comment out Deals, Contacts, Organizations, Call Logs, and Email Templates. Desktop sidebar comments out `GettingStartedBanner`. Mobile `ViewControls` adds the desktop quick-filter row.

### Cosmetic

**present.** `NoteArea.vue` note title adds `text-ink-gray-9`.

### Dest-config field UX

**source-wired** on remote `fasil-bench2` (`visaguy_frappe_crm` `student-visa` @ `f16eba7` + uncommitted). Not yet in the local bench tree used for the 2026-10-31 baseline.

On CRM Lead Data tab: watch `custom_destination` + `custom_zone`. Call `the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_lead_destination_config_options` with `company = custom_zone`. Hide `custom_visa_category` / `custom_visa_type` when `has_config` is false. Filter and auto-fill from configs / default. Filter applicant `type` from the matching configuration, then the default. When neither exists, use `fallback_applicant_types` from Destination `file_template` for the zone. That fallback is **runtime-verified** on CRM-LEAD-2026-23862 (France, zone TVG, 2026-11-09). Nested `FieldLayout` (grid row modal) must pass `:doctype` and must **not** provide destConfig unless doctype is CRM Lead.

## File inventory

Paths below are relative to `visaguy_frappe_crm/frontend/` unless noted.

### New files (copy as-is after overlay)

These exist only in `visaguy_frappe_crm`. After overlay they will be missing; copy them back from git.

| File | Role |
|---|---|
| `src/components/custom/CustomAssignTo.vue` | User Link labelled Assign To; emits `update:modelValue`; avatars via `usersStore.getUser`. |
| `src/components/custom/DuplicateLeadDialog.vue` | Forced dialog on `new_lead=true` when `check_duplicate_lead` returns another lead id; writes `custom_duplicate_reason`; then strips the query param. `disableOutsideClickToClose` is true. |
| `src/components/custom/FormSubmittingOverlay.vue` | Full-screen overlay bound to `leadFormStore.submitting` / `loadingText`. |
| `src/stores/leadForm.js` | Pinia `lead-form` store: `sendForm`, `createProcessFile`, overlay state, toasts. |
| `src/constants.js` | Child-table field and Desk path names (see below). |
| `src/composables/useDestinationConfiguration.js` | Dest-config field UX composable (remote **source-wired**; markers wrap whole file). |

`src/constants.js` values **present**:

```js
APPLICANT_INFORMATION_FIELD_NAME = "CRM Lead-custom_applicant_information"
PROCESS_FILE_TABLE_FIELD_NAME = "process_file"
PROCESS_FILE_PATH_NAME = "pf-process-file"
FILE_COLLECTION_FIELD_NAME = "file_collection"
FILE_COLLECTION_PATH_NAME = "ff-file-collection"
```

`src/composables/useDestinationConfiguration.js` (**source-wired** on remote):

- **Markers:** `// #customization` at file start; `// #end_customization` at file end
- **Restore:** copy as-is from `visaguy_frappe_crm` git / remote working tree
- **Wiring:** `the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_lead_destination_config_options` with `{ destination: custom_destination, company: custom_zone }`; watches those two fields only; exposes `hasConfig`, filter computeds, and auto-fill side effects for visa category/type; ignores responses for a destination/zone that has since changed; exports `keepVisaPairOnNextChange(doc)` so a revert in `leadDestinationChange.js` keeps the restored pair instead of applying the default. `applicantTypeFilters` uses the matching configuration, then the default. When neither exists, it uses `fallback_applicant_types` (Destination `file_template` for the zone).
- **Related custom file (remote):** `src/utils/leadDestinationChange.js`. `handleDocumentConfigurationSave` sends `old_zone` / `new_zone`, and `revertConfigFields` restores `custom_zone` and calls `keepVisaPairOnNextChange` (markers `#customization` / `#end_customization`)

Backend methods those new files call (**source-wired**, not frontend files):

- `visaguy_frappe_crm.functions.apis.check_duplicate_lead.check_duplicate_lead`
- `visaguy_frappe_crm.functions.apis.get_zone_details.get_zone_details`
- `visaguy_crm.file_collection_from_lead.generate_file_collection_lead`
- `visaguy_crm.allocated_to_process_file.create_process_file`
- `frappe.client.insert` (ToDo)
- `the_visaguy.tvg_core.doctype.destination_configuration.destination_configuration.get_lead_destination_config_options` (dest-config field UX)

### Edited upstream files (re-patch after copy)

Each entry is the behaviour to restore, not a full diff.

#### `src/pages/Lead.vue`

**Intent:** Overlay, process-file action, hide Convert/email, duplicate dialog, Data-tab reload bus.

**Markers:** `Customizations: submitting form overlay`; `Customization: hide convert to deal and add create process file button`; `Customization: hide send an email`; `Customization: hide convert to deal`; `Customization: duplicate lead`; `Customizations: create process file button`; `Customizations : reload function which takes a callback from child to reload`; `Customizations: Hide email`.

**Restore:**

1. Render `<FormSubmittingOverlay/>` at the top of the template.
2. Comment out the Convert to Deal header button. Add:

   ```vue
   <Button
     :label="__('Create Process File')"
     variant="solid"
     v-if="lead.data.status==='Payment Confirmed'"
     @click="()=>createProcessFile(lead,callReloadDataTab)"
   />
   ```

3. Comment out the "Send an email" `Tooltip`/`Button` block in the sidebar actions.
4. Comment out the Convert to Deal `<Dialog>`.
5. Add `<DuplicateLeadDialog v-if="props.leadId" :leadId="props.leadId" />`.
6. Import `provide`, `FormSubmittingOverlay`, `leadFormStore`, `DuplicateLeadDialog`.
7. `const { createProcessFile } = leadFormStore()`.
8. Provide/inject reload:

   ```js
   const reloadDataTab = ref(null)
   const registerReloadDataTab = (fn) => { reloadDataTab.value = fn }
   provide('registerReloadDataTab', registerReloadDataTab)
   const callReloadDataTab = () => { if (reloadDataTab.value) reloadDataTab.value() }
   provide('reloadDataTab', callReloadDataTab)
   ```

9. Comment out the Emails entry in `tabs` (`name: 'Emails'`). Leave Activity, Comments, Data, Calls, Tasks, Notes, Attachments, WhatsApp.

#### `src/pages/MobileLead.vue`

**Intent:** Overlay + hide Convert only. Thinner than desktop: no process-file button, no duplicate dialog, Emails tab remains.

**Markers:** `Customizations: submitting form overlay` on the overlay. Convert hide has **no** marker.

**Restore:**

1. Render `<FormSubmittingOverlay/>` and import it.
2. Comment out the Convert header button and the Convert to Deal `<Dialog>`.
3. Do **not** add Create Process File, DuplicateLeadDialog, provide/inject, or Emails-tab hide unless a later task says so **and** this log is updated.

#### `src/pages/Leads.vue`

**Intent:** Forward list selection events to view controls.

**Markers:** none.

**Restore:** on the list view component:

```vue
@selectionsChanged="
  (selections) => viewControls.handleSelectionsChange(selections)
"
```

`handleSelectionsChange` is **not** defined on `ViewControls.vue` in this tree. Re-apply the emit wiring to match current source, but treat the handler as likely dead (see Known gaps).

#### `src/components/Modals/LeadModal.vue`

**Intent:** Assign-to on create + `new_lead` query for duplicate check.

**Markers:** `Customizations: added custom assign tos`; `Customizations: added custom assign to`; `Customizations: added custom assign to api`; `Customizations: passing new_lead query so as to detect new lead in details page for duplicate checking`; `Customizations: added custom assign to api call`.

**Restore:**

1. Footer row becomes `w-full flex items-end justify-between gap-2` with `<CustomAssignTo v-model="assignedTo" />` to the left of Create.
2. `const assignedTo = ref('')`.
3. `createTodo` resource: `frappe.client.insert` of a `ToDo` doc.
4. On lead `onSuccess`: if assign-to is set, `updateAssignToInTodo(data, assignedTo.value, data.lead_owner)` then `router.push({ name: 'Lead', params: { leadId: data.name }, query: { new_lead: 'true' } })`.
5. ToDo fields: `status: Open`, `description: Lead {name} assigned to {user}`, `assigned_by`, `reference_type: CRM Lead`, `reference_name`, `allocated_to`. Toast on error.
6. Current source uses `if (assignedTo)` (the ref object), which is always truthy. Prefer `if (assignedTo.value)` when re-applying.

#### `src/components/Activities/DataFields.vue`

**Intent:** Register Data-tab reload; dirty-watch so sidebar edits re-enable Save.

**Markers:** `Customizations: import inject, onMounted`; `Customizations: Register reload function with parent (Lead.vue) using the same pattern`.

**Restore:**

1. Import `watch, inject, onMounted` from vue (keep `ref`).
2. `inject('registerReloadDataTab', null)` and on mount register `() => data.reload()`.
3. Deep `watch` on `() => data.doc`: if both old and new exist, set `data.isDirty` from `JSON.stringify(newValue) !== JSON.stringify(data.originalDoc)`; if dirty, set `data.save.loading = false`.

This file does **not** contain `handleDocumentConfigurationSave` or destination-change protection.

#### `src/components/FieldLayout/Field.vue`

**Intent:** Send Form on applicant table; empty mobile number gets zone country code; dest-config visa/applicant Link filters and hide.

**Markers:** `Customizations: for send form button`; `Customizations: appending country code in mobile number field value`; nearby `custimizations: sendForm api from store` (typo in source). Dest-config blocks: `#customization` / `#end_customization` around `inject('destinationConfiguration')`, visa/applicant filter assignment, and visa hide in `isFieldVisible`.

**Restore:**

1. Wrap Table `Grid` in a `div`. If `field.name === APPLICANT_INFORMATION_FIELD_NAME`, add `<Button class="mt-2" @click="()=>sendForm(data, reloadLeadData)">Send Form</Button>`.
2. Import `onMounted`, `APPLICANT_INFORMATION_FIELD_NAME`, `leadFormStore`. `const { sendForm } = leadFormStore()`. `const reloadLeadData = inject('reloadDataTab', () => {})`.
3. `const { userZone } = usersStore()`. On mount, if `data.value.mobile_no === ''` and `userZone?.data?.mobile_country_code`, set `data.value.mobile_no` to that code.
4. Dest-config: `inject('destinationConfiguration', null)`. In the field computed, override Link filters for `custom_visa_category`, `custom_visa_type`, and applicant `type`. In `isFieldVisible`, return false for visa category/type when `!destConfig.hasConfig.value`.

#### `src/components/FieldLayout/FieldLayout.vue`

- **Date / evidence:** 2026-11-03; remote `visaguy_frappe_crm` `student-visa` @ `f16eba7` + uncommitted; dest-config provide
- **Kind:** edited upstream
- **Markers:** `#customization` / `#end_customization` around `useDestinationConfiguration` import and the CRM Lead `provide('destinationConfiguration', …)` block
- **Restore:** Import composable. When `props.doctype === 'CRM Lead'`, call `useDestinationConfiguration(computed(() => props.data), computed(() => true))` and `provide('destinationConfiguration', destConfig)`. Do not provide for nested non–CRM Lead layouts.
- **Wiring:** provide → Field / Grid inject; composable → `get_lead_destination_config_options`
- **Desktop vs mobile:** same Data tab path
- **Verification:** source-wired

#### `src/components/Controls/Link.vue`

- **Date / evidence:** 2026-11-03; remote dest-config filter reload
- **Kind:** edited upstream
- **Markers:** `#customization` / `#end_customization` around filters `watchDebounced` and the filters equality check inside `reload`
- **Restore:** Debounced watch on `JSON.stringify(props.filters || {})` calling `reload('')`. In `reload`, also require filters JSON equality before short-circuiting.
- **Wiring:** used by Field/Grid Link cells when dest-config filters change
- **Verification:** source-wired

#### `src/components/Controls/GridRowModal.vue`

- **Date / evidence:** 2026-11-03; remote; pass doctype into nested FieldLayout
- **Kind:** edited upstream
- **Markers:** `<!-- #customization -->` / `<!-- #end_customization -->` around the `FieldLayout` with `:doctype="doctype"`
- **Restore:** `<FieldLayout v-if="tabs.data" :tabs="tabs.data" :data="data" :doctype="doctype" />` so nested layout does not default to CRM Lead / destConfig for applicant rows.
- **Wiring:** `doctype` prop already on GridRowModal
- **Verification:** source-wired

#### `src/components/Controls/Grid.vue`

**Intent:** File collection read-only; process-file / file-collection open Desk, not Link autocomplete; dest-config applicant type filters in grid cells.

**Markers:** `Customizations: to not use this field for file collection, file collection is read only`; `Customizations: to hide process file autocomplete dropdown`; `Customizations: field for click to open file`; `Customizations: base url to redirect to desk`. Dest-config: `#customization` / `#end_customization` around `inject` import, `destinationConfiguration` inject, and `getFieldObj` applicant-type filter body.

**Restore:**

1. Import `FILE_COLLECTION_FIELD_NAME`, `FILE_COLLECTION_PATH_NAME`, `PROCESS_FILE_PATH_NAME`, `PROCESS_FILE_TABLE_FIELD_NAME` from `../../constants`.
2. Read-only `FormControl` condition adds `&& field.fieldname !== FILE_COLLECTION_FIELD_NAME`.
3. `Link` renders only when `fieldtype === 'Link'` **and** the field is not `process_file` or `file_collection`.
4. Else-if those two Link fields: `<a>` with `getUrl(field.fieldname, row[field.fieldname])`, `target="_blank"`, disabled pointer when empty.
5. `getUrl`: `window.location.origin`; if origin ends with `localhost`, use `https://localhost:8080`; path `/app/{ff-file-collection|pf-process-file}/{DocId}`.
6. Dest-config: import `inject` from vue; `inject('destinationConfiguration', null)`; in `getFieldObj`, when field is applicant `type`, set `filters` from `destConfig.applicantTypeFilters.value`.

#### `src/components/ViewControls.vue`

**Intent:** Show quick filters in the mobile toolbar (desktop already has them).

**Marker:** `Customizations: quick filters in mobile view`.

**Restore:** inside the `v-if="isMobileView"` block, above the existing toolbar, add a horizontal `quickFilterList` row of `QuickFilterField` calling `applyQuickFilter`. `quickFilterList` and `applyQuickFilter` already exist later in this file; do not re-implement them.

#### `src/components/Layouts/AppSidebar.vue`

**Intent:** Hide Getting Started; drop unused nav items.

**Marker:** `Customize: Hide Getting Started` (banner only). Nav comments have no marker.

**Restore:**

1. Comment out `<GettingStartedBanner v-if="!isOnboardingStepsCompleted" … />`. The following Help `SidebarLink` still has `v-else` (orphan; see Known gaps). Re-apply as currently written unless a later fix lands.
2. Comment out links: Deals, Contacts, Organizations, Call Logs, Email Templates. Keep Leads, Notes, Tasks.

#### `src/components/Mobile/MobileSidebar.vue`

**Intent:** Same nav trim as desktop. No Getting Started banner change.

**Markers:** none.

**Restore:** comment out Deals, Contacts, Organizations, Call Logs, Email Templates. Keep Leads, Notes, Tasks.

#### `src/stores/users.js`

**Intent:** Load session zone for country code / assign UI.

**Markers:** none.

**Restore:**

```js
const userZone = createResource({
  url: "visaguy_frappe_crm.functions.apis.get_zone_details.get_zone_details",
  cache: "userZone",
  auto: true,
})
```

Export `userZone` from the store. Current source also imports unused `createDocumentResource`; the resource itself uses `createResource`.

#### `src/components/ListViews/*.vue` except `ListRows.vue`

**Intent:** Emit `selectionsChanged` for `Leads.vue`. Same patch on every list view even though only Leads forwards it.

**Markers:** none. Incidental: files lose the trailing newline after `</script>`.

**Files:** `CallLogsListView.vue`, `ContactsListView.vue`, `DealsListView.vue`, `EmailTemplatesListView.vue`, `LeadsListView.vue`, `OrganizationsListView.vue`, `TasksListView.vue`.

**Restore on each:**

1. On the root list component: `@update:selections="$emit('selectionsChanged', Array.from($event || []))"`.
2. Add `'selectionsChanged'` to `defineEmits`.

`ListRows.vue` is identical to `crm`; do not patch it.

#### `src/components/Activities/NoteArea.vue`

**Intent:** Title contrast only.

**Markers:** none.

**Restore:** change the title div from `truncate text-lg font-medium` to `truncate text-lg font-medium text-ink-gray-9`.

### Build / path files (must re-apply; not product features)

Copying `crm/frontend` will retarget the Vite app back at the `crm` app. Restore these so the bundle belongs to `visaguy_frappe_crm`.

#### `package.json`

Scripts **present**:

```json
"build": "vite build --base=/assets/visaguy_frappe_crm/frontend/ && yarn copy-html-entry",
"copy-html-entry": "cp ../visaguy_frappe_crm/public/frontend/index.html ../visaguy_frappe_crm/www/crm.html"
```

Upstream `crm` uses `/assets/crm/frontend/` and `../crm/www/crm.html`.

#### `vite.config.js`

Upstream `frappeui({ buildConfig: { indexHtmlPath: '../crm/www/crm.html', emptyOutDir: true, sourcemap: true } })`. Current visaguy file **drops** that `buildConfig` and sets top-level:

```js
build: {
  outDir: '../visaguy_frappe_crm/public/frontend',
  emptyOutDir: true,
  commonjsOptions: { include: [/tailwind.config.js/, /node_modules/] },
  sourcemap: true,
}
```

Re-apply that `build` block and do **not** restore `crm` `buildConfig` unless you also retarget `indexHtmlPath` to visaguy.

PWA `start_url` is still `/crm`. Manifest icon `src` values still point at `/assets/crm/manifest/…` in both trees; visaguy did not retarget them.

#### `.gitignore`

Append `dev-dist/*` after `*.local`.

#### `components.d.ts`

Do not hand-edit as product code. After `yarn build` (or the unplugin that generates this file), confirm these entries exist:

- `CustomAssignTo` → `./src/components/custom/CustomAssignTo.vue`
- `DuplicateLeadDialog` → `./src/components/custom/DuplicateLeadDialog.vue`
- `FormSubmittingOverlay` → `./src/components/custom/FormSubmittingOverlay.vue`

### Diff inventory vs `crm/frontend`

`diff -rq` (excluding `node_modules`, `dist`) reported exactly on 2026-10-31:

**Only in visaguy:** `src/components/custom/`, `src/constants.js`, `src/stores/leadForm.js`.

**Differ:** `components.d.ts`, `.gitignore`, `package.json`, `vite.config.js`, `src/pages/{Lead,MobileLead,Leads}.vue`, `src/components/Activities/{DataFields,NoteArea}.vue`, `src/components/Controls/Grid.vue`, `src/components/FieldLayout/Field.vue`, `src/components/Layouts/AppSidebar.vue`, `src/components/Mobile/MobileSidebar.vue`, `src/components/Modals/LeadModal.vue`, `src/components/ViewControls.vue`, `src/stores/users.js`, and the seven ListViews listed above.

No other `frontend/` files differed in that snapshot. If a later overlay or patch changes the set, update this inventory.

## Known gaps (do not treat as done)

### Destination-change protection is not in this frontend diff

[`features/completed/destination-configuration-lead-resolution-and-protection.md`](../../features/completed/destination-configuration-lead-resolution-and-protection.md) claims Frappe CRM support via `leadDestinationChange.js`, `handleDocumentConfigurationSave` (`DataFields.vue`), and `handleConfigurationChange` (`Lead.vue` / `MobileLead.vue`).

In the 2026-10-31 comparison those symbols are **absent**. `src/utils/leadDestinationChange.js` does not exist in either tree. `src/utils/dialogs.jsx` is **identical** to `crm`. Current `DataFields.vue` / `Lead.vue` diffs are reload, overlay, Convert hide, process file, and duplicate dialog only.

[`docs/product/capabilities.md`](../product/capabilities.md) still cites `leadDestinationChange.js` as evidence. That claim is **not** supported by the current frontend-vs-`crm` diff. Backend template resolution in `visaguy_crm` is out of scope for this log.

Do not claim destination-change protection in Frappe CRM until those files/symbols are **source-wired** here.

### Dest-config field UX — remote only (not in local 2026-10-31 baseline)

**source-wired** on remote `fasil-bench2` (`visaguy_frappe_crm` `student-visa` @ `f16eba7` + uncommitted). See Feature groups → Dest-config field UX and the inventory entries for `useDestinationConfiguration.js`, `FieldLayout.vue`, `Field.vue`, `Grid.vue`, `Link.vue`, `GridRowModal.vue`.

Local bench `visaguy_frappe_crm` used for the 2026-10-31 baseline still lacks these symbols. Do not claim local parity until the same files are present there or this log’s evidence snapshot is refreshed from remote/git.

### `Leads.vue` selection wiring is likely dead

`Leads.vue` calls `viewControls.handleSelectionsChange`. That function **does not exist** in `ViewControls.vue` (only that one call site in the visaguy frontend). Re-applying the emit without a handler will not restore a working feature.

### `AppSidebar.vue` orphan `v-else`

Commenting out `GettingStartedBanner` (`v-if="!isOnboardingStepsCompleted"`) leaves the Help `SidebarLink` on `v-else`. Help therefore never renders, because the `v-if` is gone. Re-apply as-is only to match current source; fixing the `v-else` is a separate change.

### Mobile lead page is a thinner customization

| Behaviour | Desktop `Lead.vue` | Mobile `MobileLead.vue` |
|---|---|---|
| Form overlay | yes | yes |
| Hide Convert | yes (button + dialog) | yes (button + dialog) |
| Create Process File | yes, status-gated | no |
| DuplicateLeadDialog | yes | no |
| Hide email composer | yes | no (composer block not present the same way) |
| Hide Emails tab | yes | **no** — Emails tab still listed |
| provide/inject Data-tab reload | yes | no |

Send Form still lives in `Field.vue`, so the Data tab on mobile can send a form, but without the parent reload bus `inject('reloadDataTab', () => {})` is a no-op.

### `/crm` serving is not verified here

Local `sites/apps.txt` lists `visaguy_frappe_crm` **before** `crm`. `crm/hooks.py` has:

```python
website_route_rules = [
    {"from_route": "/crm/<path:app_path>", "to_route": "crm"},
]
```

`visaguy_frappe_crm` hooks have **no** `website_route_rules`. Both apps ship `www/crm.html`; only `crm` has `www/crm.py`. Which HTML/bundle actually serves `/crm` is **configured-unverified**. Confirm after rebuild; do not assume the custom app wins because it is listed first.

### Other implementation notes (not product features)

- `LeadModal.vue` `if (assignedTo)` is always true (ref object). Empty assign-to still attempts ToDo insert.
- `users.js` imports unused `createDocumentResource`.
- ListViews trailing-newline and a blank line in `ViewControls.vue` are incidental.
- Vite PWA icons still use `/assets/crm/manifest/…`.

## Future re-apply procedure

Documented so an overlay task can run it. Do not run these steps unless a task authorizes them.

1. **Confirm the upstream default branch** on `tridz-dev/frappe-crm`. This clone’s remote HEAD is `develop`. If maintainers want `main`, confirm that ref exists before merging.
2. **Commit or branch** `visaguy_frappe_crm` so the current `frontend/` (especially the five new files) is recoverable from git.
3. **In `crm`:** fetch; merge the chosen branch into `visaguy`; resolve conflicts. Do not copy frontend until `visaguy` contains the intended upstream.
4. **Copy** `crm/frontend` over `visaguy_frappe_crm/frontend` (exclude `node_modules` / `dist` if copying a dirty tree).
5. **Restore from this log:**
   - Copy the five new files from git (three under `src/components/custom/`, `src/stores/leadForm.js`, `src/constants.js`).
   - Re-patch every edited upstream file using the Restore steps and marker comments.
   - Retarget `package.json` and `vite.config.js`; append `dev-dist/*` to `.gitignore`.
6. **Build:** `yarn build` in `visaguy_frappe_crm/frontend`. Confirm `public/frontend` and `www/crm.html` updated, and `components.d.ts` lists the three custom components.
7. **Verify on `/crm`:** create lead with Assign To; duplicate dialog + reason when mobile matches; Send Form on applicant table; Create Process File when status is Payment Confirmed; overlay during submit; grid Desk links for process file and file collection; Data tab refresh; Convert/Emails hidden on desktop; nav trim.

Do not expect destination-change protection to appear after this restore; it is not in the current frontend diff. Dest-config field UX is **source-wired** on remote only — copy `useDestinationConfiguration.js` and re-patch the marked `#customization` blocks when restoring that site or when promoting to the local baseline.

## Related workspace documents

- [`customizations.md`](customizations.md) — CRM layering (`crm` / `visaguy_crm` / `visaguy_frappe_crm`) and a pointer to this overlay log.
- [`.agents/rules/frappe-crm-frontend-overrides.md`](../../.agents/rules/frappe-crm-frontend-overrides.md) — mandatory update rule.
- [`features/completed/destination-configuration-lead-resolution-and-protection.md`](../../features/completed/destination-configuration-lead-resolution-and-protection.md) — frontend protection claimed, **not** in this diff.
- [`features/completed/destination-configuration-lead-field-ux.md`](../../features/completed/destination-configuration-lead-field-ux.md) — dest-config field UX. Applicant Type fallback is **runtime-verified** (2026-11-09, CRM-LEAD-2026-23862). The rest is **source-wired** on remote (see Feature groups).
- [`tasks/completed/implement-destination-configuration-lead-field-ux.md`](../../tasks/completed/implement-destination-configuration-lead-field-ux.md) — implementation evidence for dest-config field UX.
