---
id: FEAT-empty-mandatory-information-row-process-file
title: Skip empty mandatory information rows when creating a process file
status: completed
priority: high
repositories: [visaguy_crm]
owners: ["fasil"]
depends_on: []
created: 2026-10-29
updated: 2026-10-29
---

# Skip empty mandatory information rows when creating a process file

## Summary

`create_process_file` crashed with `TypeError: can only concatenate str (not "NoneType") to str` when an FF File Collection information row had Mandatory checked but no field name. Incomplete grid rows are now ignored; named mandatory fields that are still empty continue to block process-file creation.

## User value

Consultants can create a process file when a File Collection information table contains an accidental blank row (Mandatory checked, no field name). They still receive a clear validation error when a real named mandatory information field has not been filled.

## Scope

### Included

- Skip `FF File Collection Data` rows with no `field_name` during `check_lead_verification`.
- Keep blocking process-file creation for named mandatory information fields with an empty value.
- Use formatted `frappe.throw` messages so a missing label cannot crash the request.
- Harden the mandatory-file throw with `group_name or file_name`.

### Excluded

- Making `field_name` required on `FF File Collection Data` / `FF File Template Data`.
- Changing FileFlo guest-form InfoForm validation.
- Treating SQL `NULL` values as empty for named fields.

## Requirements

1. An information row with `mandatory=1`, empty `field_name`, and empty `value` must not raise a TypeError and must not block process-file creation.
2. An information row with `mandatory=1`, a non-empty `field_name`, and empty `value` must still throw a validation error that includes the field name and file collection name.
3. The mandatory-file incomplete-upload throw must remain, using `group_name` or falling back to `file_name`.

## Proposed design

In `visaguy_crm.allocated_to_process_file.check_lead_verification`, after fetching mandatory empty-value information rows, keep only rows whose `field_name` is a non-empty string. Throw with `_("... {0} ... {1} ...").format(...)`.

## Tasks

- [x] [TASK-fix-empty-mandatory-information-row-crash](../../tasks/completed/fix-empty-mandatory-information-row-crash.md)

## Acceptance criteria

- [x] Blank mandatory-only information rows do not crash or block `create_process_file`.
- [x] Named mandatory information fields with empty value still block with a field-name message.
- [x] File throw uses a fallback label when `group_name` is missing.
- [x] Unit tests cover skip, named-field block, and file-label fallback.

## Dependencies

- `visaguy_crm` (`allocated_to_process_file.create_process_file`)
- `fileflo` DocType `FF File Collection Data`

## Risks

- Existing File Collections with accidental blank mandatory rows will no longer block conversion. That is intended: those rows are not applicant fields.

## Open questions

None.

## Completion notes

Implemented on the remote bench `visaguy_crm` app (`/home/fasil/fasil-bench2/apps/visaguy_crm`). Changes left unstaged; not committed.

1. **`visaguy_crm/allocated_to_process_file.py`** (`check_lead_verification`):
   - After the existing `mandatory=1` and `value=""` query, keep only information rows whose `field_name` is a non-empty string.
   - Throw with `_("... {0} ... {1} ...").format(...)` for both information and file messages.
   - File message uses `group_name or file_name`.

2. **`visaguy_crm/test_allocated_to_process_file.py`**:
   - Added `TestCheckLeadVerification` with empty-row skip, whitespace skip, named-field block, and file-label fallback.

3. **Validation**: 10/10 tests in `visaguy_crm.test_allocated_to_process_file` passed as standalone unittest (site `allow_tests` is off). Manual Create Process File click on the live site was not re-run after the change; workers may need a bench restart to load the new module.
