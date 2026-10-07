# ADR 004: Standard DocType Customizations via Export Customizations

**Date:** 2026-10-07  
**Status:** Accepted  

## Context

Historically, the project relied on `fixtures` defined in `hooks.py` to track `Custom DocPerm` records and other customizations applied to standard Frappe/ERPNext DocTypes across maintained apps (such as `visaguy_crm`, `visaguy_hrms`, `the_visaguy`, and `visaguy_frappe_crm`).

While fixtures work, they can lead to conflicts, bloated `fixtures/` directories, and complexity when managing granular permissions and custom fields across multiple custom apps. 

Frappe natively provides an **Export Customizations** feature (accessed via Customize Form -> Actions -> Export Customizations), which exports Custom Fields, Property Setters, and Custom Perms directly into JSON files within the app's `custom` directory.

## Decision

We will strictly use the Frappe native **Export Customizations** feature for tracking all modifications to standard DocTypes.

- **No more Custom DocPerm fixtures:** We will no longer use `fixtures` in `hooks.py` to export `Custom DocPerm` or other standard DocType customizations.
- **JSON files in `custom/`:** All custom permissions, property setters, and custom fields for standard DocTypes must be exported as JSON files into the `custom/` folder of the respective custom app.
- **Workflow:** Whenever a permission is added/changed, or a standard DocType is customized, the developer/agent must use the `Customize Form -> Actions -> Export Customizations` option in the Frappe UI to update the JSON files, which will then be committed to the application repository.

## Consequences

- **Cleaner Repositories:** The `fixtures/` directory will no longer be cluttered with `Custom DocPerm` CSV/JSON files.
- **Better Standard Alignment:** This aligns with Frappe's recommended native approach for tracking standard DocType customizations in custom apps.
- **Migration effort:** Existing fixtures for docperms have already been removed from `visaguy_crm`, `visaguy_hrms`, `the_visaguy`, and `visaguy_frappe_crm`, and replaced with exported JSON files. All future modifications must adhere to this new standard.
