# ADR-007: FormKit Mandatory File Validation, Reactivity Sync, and Submission Pipeline in FileFlo

## Status

Accepted

## Context

`fileflo` provides the guest-facing document collection frontend (`form/` Vue 3 + FormKit SPA at `/form/<link_id>`) used across visa workflows to collect applicant documents and preliminary details for `FF File Collection` records.

Child rows in `FF File Collection File` can be marked as `mandatory: 1`. Previously, two critical issues affected this form:
1. **Submission Hang on Valid Attachments**: When a customer attached all mandatory documents and clicked **Submit**, the button showed an indefinite loading spinner. No network request (`add_form_data`) was sent, and no error was logged in the browser console.
2. **Missing Validation Feedback on Empty Submit**: When mandatory documents were not attached and **Submit** was clicked, neither the inline red FormKit error nor a validation modal dialog appeared.

### Root Causes
- **FormKit Rule Evaluation on Empty Values**: In FormKit, custom validation rules skip evaluation when the input value is empty (`[]`) by default, unless prefixed with `+` (`skipEmpty: false`). Without `+`, FormKit bypassed custom validation for empty file inputs.
- **Stale Blocking Messages in FormKit Node Store**: FormKit tracks validation state internally within each node's message store (`rule_mandatoryDoc`). Files selected via the native `<input type="file">` were dispatched to the Vuex store (`store.js`). Even though the custom rule function `mandatoryDoc(node)` evaluated to `true` (valid) after file attachment, FormKit's node store retained the stale blocking message because input mutations occurred outside FormKit's internal reactivity scope. FormKit considered the form blocked (`blocking > 0`) and silently aborted form submission without triggering `@submit="handleSubmit"`.
- **Dynamic Rule String Leaks**: Earlier attempts dynamically appended or removed rule strings in `:validation` (e.g. `'required|'`). Dynamic rule mutations caused FormKit nodes to strand a `validating: true` ledger entry that never cleared.
- **Fragile Asynchronous Submit Context**: `submitTab()` previously relied on a `submitContext` object and `onSuccess`/`onError` resource callbacks on `$resources.submitDetails`. In `frappe-ui`, `this` inside resource definitions points to the resource instance rather than the Vue component, causing errors like `TypeError: this.serverMessage is not a function`.
- **Draft Preservation Requirement**: Commit `7336480` introduced partial saving (`canSave`, `checkRequired: false`) via the **Save** button and `Ctrl+S`, allowing applicants to save incomplete drafts without mandatory validation. This behavior had to be strictly preserved.

## Decision

1. **Enforce Rule Evaluation with `+` Prefix**:
   - Register `+mandatoryDoc` in `:validation` when `doc.mandatory` is true and status is neither `Completed` nor `Uploaded`.
   - The `+` flag sets `skipEmpty: false`, forcing FormKit to execute `mandatoryDoc(node)` even on empty file arrays (`[]`) upon submission.
2. **Synchronize FormKit Reactivity Explicitly**:
   - In `handleFileChange()`: Upon file selection and store mutation, query the document's FormKit node via `formNode.at(d.file_name)`, remove the blocking message via `node.store.remove('rule_mandatoryDoc')`, and invoke `node.input(node.value, false)` across all documents in the group.
   - In `removeFile()`: Check group satisfaction via `isGroupMandatorySatisfied(groupName)`. If satisfied, remove the blocking message; if not satisfied, dispatch `node.input(remainingFiles, false)` so FormKit re-adds the blocking rule.
   - Use `CSS.escape(fileName)` in `removeFile()` with safe fallbacks to prevent `DOMException` when document names contain quotes or special characters (e.g., *"Driver's License"*).
3. **Prevent Stray Validating Flags**:
   - Register `clearStrayValidatingPlugin` in `main.js` to automatically clean up orphaned `validating` messages when validation prop strings change.
   - Walk the form node tree in `onBeforeSubmit()` to remove any residual `validating` flags on nodes lacking validation rules.
4. **Unified Pre-Submit Modal & Condition Safeguards**:
   - Hook `@click="onBeforeSubmit"` on the Submit button.
   - Implement `getMissingMandatoryDocs()` to scan all tabs for missing mandatory documents.
   - Evaluate document visibility conditions (`evaluateConditions(doc.conditions, userInfos)`) in both `getMissingMandatoryDocs()` and `isDocumentMandatory(doc)` so conditionally hidden documents are never erroneously flagged as missing.
   - If missing documents exist, display a `Validation Error` modal dialog (`showValidationErrors`) listing the required files.
5. **Direct Async/Await Submission**:
   - Remove `submitContext` and the broken `onError` callback from `$resources.submitDetails`.
   - Use direct `async/await` in `submitTab()`, delegating error display to the component's `try/catch` in `handleSubmit()` and `handleSave()` where `this.serverMessage` is correctly scoped.
6. **Preserve Draft Saving**:
   - The Save button remains `type="button"` and invokes `handleSave()`, executing `validateCurrentTab()` with `checkRequired: false` to allow saving partial information and documents (`form_submitted: 0`).

## Consequences

### Positive
- Submitting empty mandatory fields immediately displays both inline red FormKit messages and a unified `Validation Error` modal.
- Submitting with all mandatory documents attached reliably submits (`form_submitted: 1`), displays the `Success` modal, and avoids infinite spinner hangs.
- Partial draft saving via Save button and `Ctrl+S` remains fully functional.
- Hidden conditional documents (e.g. spouse documents when marital status is single) do not block submission.

### Negative
- Document groups requiring explicit FormKit state clearing must follow the `group_name || file_name` pattern when manipulating child files.

## Alternatives Considered

- **Toggling `:validation` dynamically**: Caused FormKit to leak internal `validating: true` ledger states, permanently locking the submit button.
- **Calling `node.validate()` directly**: File input nodes in FormKit do not expose a standalone `.validate()` method; triggering re-evaluation requires `node.input(value, false)`.
