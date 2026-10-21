---
id: TASK-047
feature: FEAT-001
title: Customer form Save works without required-field checks
status: ready
repository: fileflo, visaguy_crm
owners: []
depends_on: []
related:
  - TASK-046
expected_files:
  - fileflo: form/src/components/DocForm.vue
  - fileflo: form/src/components/InfoForm.vue
  - fileflo: form/src/utils/validationUtil.js
  - visaguy_crm: visaguy_crm/data_collecting_form.py
created: 2026-10-21
updated: 2026-10-21
---

# TASK-047: Customer form Save works without required-field checks

## Objective

On the FileFlo customer form, Save stores what the customer has entered,
without required-field checks. Submit keeps every check. The owner reports
that Save often fails.

## Context

Investigated 2026-10-21. Code: **source-wired**.

### Same API (verified)

- Source (`fileflo/form/src/components/DocForm.vue`): Save and Submit both
  call the `submitDetails` resource,
  `fileflo.data_collection.add_form_data`. The only difference is
  `form_submitted` (0 or 1).
- Served bundle (`fileflo/public/form/assets/Home-Bol9bkov.js`, built
  2026-09-02): one `add_form_data` call, used for Save, Submit and the
  pre-save of the other applicant tabs.
- `visaguy_crm` overrides it (`hooks.py`,
  `override_whitelisted_methods`). No other app overrides it. Both apps are
  installed on `visaguy`.
- The bundle is not in git. `bench build` builds it
  (`run_build_command_for_apps`), so a deploy rebuilds it.

### Differences between Save and Submit

Frontend:

1. `handleSave` runs `validateGuestFormData`, which also checks mandatory
   Multi Select fields and the minimum table row count. These are
   required-field checks.
2. The Save button is disabled until the customer edits something in this
   session (`fillingStarted`), and again after each save. Adding or
   removing a table row does not count as an edit.
3. Ctrl+S calls the form's submit, so it runs Submit, not Save.
4. Errors show a fixed "please reload" text. The server message is lost.

Backend (`visaguy_crm.data_collecting_form.add_form_data`):

- On the first Save, the linked Lead, CRM Lead or PF Process File is loaded
  and saved with `custom_form_saved = 1`. Any validation on that document
  (for example the Process File rule that needs an operations appointment
  date for some destinations, the single-primary-applicant rule, the Lead
  email check) fails the whole request. Frappe does not write these
  validation errors to the Error Log. This is the main suspect for the
  failing saves, but it is **not confirmed**: live logs were not checked.
- `custom_form_saved` is only read by a Lead client script that hides the
  "Update Applicant Details" button. No server hook depends on it.

## Required behaviour

### fileflo frontend

- Save checks only date rules (`validation_rule`). It does not check
  mandatory Multi Select fields or the minimum table row count. Submit keeps
  every check on every applicant tab.
- File format, file size and file count checks are not changed.
- Ctrl+S runs Save when the Save button is enabled in settings. Otherwise
  it does nothing.
- The Save button is enabled whenever no save, submit or upload is running.
- Adding or removing a table row marks the tab as edited (for the
  leave-page warning).
- On an error, Save and Submit show the server's message. They fall back to
  the current text when there is no message.

### visaguy_crm backend

- On the first Save, set `custom_form_saved = 1` on the linked document
  with `frappe.db.set_value`, without a document save. A validation on the
  Lead or Process File must not fail the customer's save.
- Submit is not changed.

## Constraints

- One branch per repository, cut from `main`. PRs: `fileflo` to `main`,
  `visaguy_crm` to `main` and `stage`.
- Do not commit the built bundle.
- No change to which fields Submit requires.

## Validation

- `fileflo`: `yarn build` succeeds (Node 18 or newer). Unit-level check of
  `validateGuestFormData` for both modes.
- `visaguy_crm`: pure test that a first Save sets the flag with
  `frappe.db.set_value` and does not save the linked document, and that
  Submit still saves it.
- Owner: on `visaguy`, Save a form with an empty mandatory Multi Select
  and with a linked Process File that fails validation. Both must save.
  Submit must still block on required fields.

## Definition of done

Validation passes. Commit SHAs and PR links are recorded here. Deploy is
owner-only.
