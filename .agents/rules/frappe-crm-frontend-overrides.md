# Frappe CRM Frontend Overrides

Mandatory when adding, editing, deleting, or re-applying anything under `visaguy_frappe_crm/frontend`, except `node_modules` and `dist`.

Living log: [`docs/architecture/frappe-crm-frontend-overrides.md`](../../docs/architecture/frappe-crm-frontend-overrides.md).

This workspace does not contain that frontend tree. The rule still applies when CRM frontend work is planned, implemented, or recorded from this workspace.

## Required steps

1. **Read the log first.** Do not patch Vue from memory.
2. **Update the log in the same task.** Add, change, or remove the matching inventory entry; refresh feature groups and known gaps if behaviour changed. Do not leave the log stale.
3. **Do not mark the task complete** until the log matches the source.
4. **Prefer new files** under `src/components/custom/` and dedicated stores over editing upstream Vue.
5. **Mark every upstream edit** with an HTML/JS comment containing `Customization`, `Customizations`, or `Customize`.
6. **After overlay of `crm/frontend`**, restore from the log. Copy new files from `visaguy_frappe_crm` git; do not reconstruct them from memory or from this workspace.
7. **Do not claim** destination-change protection (`leadDestinationChange.js`, `handleDocumentConfigurationSave`, `handleConfigurationChange`) or dest-config field UX (`useDestinationConfiguration.js`) unless those files or symbols are **source-wired** in the log.

## What to record

Each log entry must include: date and evidence (app HEAD / what changed); kind (`new file` / `edited upstream` / `build-path`); paths relative to `visaguy_frappe_crm/frontend/`; marker comment text or none; restore behaviour; backend methods or provide/inject/emits; desktop vs mobile if they differ; verification label (`present` / `source-wired` / `runtime-verified`).

Do not paste full Vue files into the workspace. Git in `visaguy_frappe_crm` is authoritative for source.
