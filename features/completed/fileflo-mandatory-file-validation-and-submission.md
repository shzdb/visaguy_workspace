---
id: FEAT-fileflo-mandatory-file-validation-and-submission
title: Mandatory File Validation and Submission Flow in FileFlo Document Collection
status: completed
priority: high
repositories: [fileflo, visaguy_crm]
owners: ["fasil"]
depends_on: []
created: 2026-10-26
updated: 2026-10-27
---

# Mandatory File Validation and Submission Flow in FileFlo Document Collection

## Summary

Enforces mandatory file validation (inline FormKit error messages and cross-tab modal dialog) when submitting FileFlo guest forms, resolves an infinite loading spinner hang when submitting forms with attachments, and preserves partial draft saving without mandatory field constraints.

## User value

Applicants filling out visa document collection forms (`/form/<link_id>`) receive immediate and unambiguous feedback if mandatory documents are missing: both directly under the file input and in a summarized modal dialog. When all required files are provided, the form submits cleanly and provides immediate confirmation without hanging on an indefinite loading spinner. Applicants can also save partial drafts at any time without being forced to attach all documents.

## Scope

### Included

- **Mandatory File Validation Feedback**:
  - Inline FormKit error message under each missing mandatory file input (`<file_name> is required.`).
  - Pre-submit check across all applicant tabs generating a unified `Validation Error` modal dialog listing all missing files.
  - Aborting the `add_form_data` submission API call when mandatory documents are missing.
- **Infinite Loading Spinner Resolution**:
  - Preventing FormKit nodes from retaining stale `rule_mandatoryDoc` blocking messages when files are attached via native file dialogs.
  - FormKit plugin (`clearStrayValidatingPlugin`) in `main.js` to clear orphaned `validating: true` ledger entries.
  - Refactoring `submitTab()` to use clean `async/await` execution instead of fragile asynchronous `submitContext` callbacks.
- **Draft Save Preservation**:
  - Preserving partial draft saves via the **Save** button and `Ctrl+S` (`form_submitted: 0`) without enforcing mandatory checks (commit `7336480`).
- **Edge Case Robustness**:
  - Factoring in document conditions (`evaluateConditions`) so conditionally hidden documents are not reported as missing.
  - Escaping special characters and apostrophes in document names (e.g., *"Driver's License"*) in DOM selectors.
  - Safeguarding file format validation and error message parsing.

### Excluded

- Information form field validation alterations (InfoForm validation remains governed by `validationUtil.js`).
- Modifying backend document generation schemas or template resolution rules.

## Requirements

1. If a mandatory file input has no files attached and the applicant clicks **Submit**:
   - The form submission must be blocked.
   - FormKit must render an inline red error under the input.
   - A modal dialog titled `Validation Error` must list all missing mandatory documents.
   - The `add_form_data` endpoint must not be invoked.
   - The submit button must reset to its clickable state (`disabled: false`, label `"Submit"`).
2. If mandatory files are attached and **Submit** is clicked:
   - FormKit must evaluate all rules as valid with 0 blocking messages.
   - `add_form_data` must be called with `form_submitted: 1`.
   - On HTTP 200, a modal dialog titled `Success` must display `Documents Successfully updated.`.
   - The submit button must not hang.
3. If **Save** is clicked with missing mandatory documents:
   - `validateCurrentTab({ checkRequired: false })` must run.
   - `add_form_data` must be called with `form_submitted: 0` and return HTTP 200.

## Tasks

- [x] [TASK-fix-fileflo-mandatory-file-validation-and-submit-hang](file:///home/fasil/Tridz/visaguy_workspace/tasks/completed/fix-fileflo-mandatory-file-validation-and-submit-hang.md)

## Acceptance criteria

- [x] Clicking Submit on an empty form with mandatory files displays inline errors and modal dialog.
- [x] `add_form_data` is not called when mandatory files are missing (0 network calls).
- [x] Attaching mandatory files uploads files (HTTP 200) and clears inline error messages.
- [x] Clicking Submit with mandatory files attached completes with HTTP 200 and shows Success modal.
- [x] Save button saves partial data (`form_submitted: 0`) without triggering mandatory checks.
- [x] Conditional mandatory documents that are hidden do not block submission.

## Dependencies

- `fileflo` (form frontend in `form/` Vue 3 + FormKit SPA)
- `visaguy_crm` (provides `data_collecting_form.add_form_data` backend override)

## Completion notes

### Implementation Details

1. **`fileflo/form/src/components/DocForm.vue`**:
   - Registered `+mandatoryDoc` rule with `+` flag (`skipEmpty: false`) so FormKit evaluates empty file arrays.
   - Added `handleFileChange()` store cleanup: removes `rule_mandatoryDoc` from FormKit's node store and dispatches `node.input(node.value, false)` across the document group.
   - Added `removeFile()` cleanup: checks `isGroupMandatorySatisfied(groupName)` and safely uses `CSS.escape()`.
   - Added `@click="onBeforeSubmit"` on the submit button, clearing stray validating nodes and triggering `getMissingMandatoryDocs()`.
   - Integrated condition checks `evaluateConditions(doc.conditions, userInfos)` into `getMissingMandatoryDocs()` and `isDocumentMandatory()`.
   - Refactored `submitTab()` to directly await `this.$resources.submitDetails.submit(payload)` and removed broken `onError` callback from `$resources.submitDetails`.
   - Updated `serverMessage()` to support `error?.message` alongside `error?.messages`.

2. **`fileflo/form/src/main.js`**:
   - Implemented `clearStrayValidatingPlugin` FormKit plugin to clear orphaned `validating` messages when validation prop strings change.

3. **Runtime Verification**:
   - End-to-end automated tests with Chrome DevTools Protocol verified against `https://visaguy-fsl.code.tridz.in/form/350c85dfae4d2708e21d2e944651e20d45615e119ec4802a7617adfd`:
     - Test 1 (Empty submit): Modal displayed `Emirates Id is required.\nResidence Visa Copy is required.`, inline errors displayed, 0 `add_form_data` calls, button enabled.
     - Test 2 (Save draft): Partial save completed (`form_submitted: 0`), HTTP 200.
     - Test 3 (Attach & submit): Uploads succeeded (HTTP 200), inline errors cleared, `add_form_data` succeeded (`form_submitted: 1`), Success modal appeared, button restored.
