---
id: TASK-fix-fileflo-mandatory-file-validation-and-submit-hang
feature: FEAT-fileflo-mandatory-file-validation-and-submission
title: Fix FileFlo Mandatory File Validation and Infinite Submit Hang
status: completed
repository: fileflo
owners: ["fasil"]
depends_on: []
expected_files:
  - fileflo/form/src/components/DocForm.vue
  - fileflo/form/src/main.js
created: 2026-10-26
updated: 2026-10-27
---

# Fix FileFlo Mandatory File Validation and Infinite Submit Hang

## Objective

Fix two intertwined issues in the FileFlo document collection form (`DocForm.vue`):
1. Resolve the infinite loading spinner hang on the submit button when mandatory files are attached.
2. Restore missing mandatory file validation when submitting empty mandatory fields (both inline FormKit red error and modal dialog).
3. Preserve partial draft saving via the Save button and `Ctrl+S` (commit `7336480`).

## Context

When an applicant accesses `/form/<link_id>`, `DocForm.vue` dynamically renders file inputs using `@formkit/vue`. For mandatory file rows (`doc.mandatory === 1`), missing files failed to show validation feedback, while attached files caused the submit button to hang in a permanent loading state. This occurred because FormKit native file inputs skip custom rules on empty values unless prefixed with `+`, FormKit's node store retained stale `rule_mandatoryDoc` blocking messages across native file selections, and `submitTab()` used fragile asynchronous callback structures.

## Inputs

- `DocForm.vue` in `fileflo/form/src/components/`
- `main.js` in `fileflo/form/src/`
- `data_collection.py` in `fileflo` & `visaguy_crm` override (`data_collecting_form.py`)
- Headless Chrome CDP automation script (`verify_all.js`)

## Required behaviour

- When Submit is clicked with empty mandatory files:
  - FormKit renders inline red error: `<document.file_name> is required.`.
  - A modal dialog appears with title `Validation Error` listing each missing document.
  - The form submission is aborted; no `add_form_data` request is made.
  - Submit button resets to clickable state without hanging.
- When Submit is clicked with all mandatory files attached:
  - All rules evaluate cleanly (0 blocking messages).
  - Submit button submits the form via `add_form_data` with `form_submitted: 1`.
  - On HTTP 200, a `Success` modal dialog is shown (`Documents Successfully updated.`).
- When Save is clicked:
  - Form calls `add_form_data` with `form_submitted: 0`.
  - Skips required document checks (preserving commit `7336480`).
- When conditional documents are hidden (`evaluateConditions` returns false):
  - Do not flag them as missing in `getMissingMandatoryDocs()` or `isDocumentMandatory()`.

## Constraints

- Scope is strictly mandatory FILE validation; do not alter InfoForm/information field validation.
- Changes must remain unstaged in git for review per project rules.
- Retain commit `7336480` features: `canSave`, `checkRequired: false`, and `serverMessage()` error formatting.

## Expected changes

- `fileflo/form/src/components/DocForm.vue`:
  - Set `:validation="validateForm(document)"` with `+mandatoryDoc` rule.
  - Implement `mandatoryDoc(node)` custom rule function.
  - Synchronize FormKit reactivity in `handleFileChange()` and `removeFile()`.
  - Add `@click="onBeforeSubmit"` to walk form nodes and show `Validation Error` modal.
  - Factor in `evaluateConditions` for conditional documents.
  - Refactor `submitTab()` to use `async/await` and remove broken `onError` callback.
- `fileflo/form/src/main.js`:
  - Register `clearStrayValidatingPlugin` to clear orphaned `validating` messages.

## Validation

- Tested with automated CDP test suite (`verify_all.js`) on live remote bench (`https://visaguy-fsl.code.tridz.in`):
  - **Test 1 (Empty submit)**: Modal dialog appeared with "Validation Error"; inline red FormKit errors rendered; 0 calls to `add_form_data`; submit button restored.
  - **Test 2 (Save draft)**: Saved partial form via `add_form_data` (`form_submitted: 0`); HTTP 200 returned.
  - **Test 3 (Attach & submit)**: Files uploaded (HTTP 200); inline errors cleared; `add_form_data` posted (`form_submitted: 1`); HTTP 200 returned; "Success" dialog displayed; submit button restored.

## Definition of done

- Fix implemented in `DocForm.vue` and `main.js`.
- Frontend built locally and on remote bench with cache cleared.
- 100% automated test pass rate verified on remote bench.
- ADR-007, feature, and task documentation recorded in workspace.
