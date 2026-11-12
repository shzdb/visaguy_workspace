---
id: TASK-fix-empty-mandatory-information-row-crash
feature: FEAT-empty-mandatory-information-row-process-file
title: Fix empty mandatory information row crash
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - visaguy_crm/allocated_to_process_file.py
  - visaguy_crm/test_allocated_to_process_file.py
created: 2026-10-29
updated: 2026-10-29
---

# Fix empty mandatory information row crash

## Objective

Stop `create_process_file` from crashing when an FF File Collection information row has only Mandatory checked and no field name.

## Context

`check_lead_verification` queries `FF File Collection Data` with `mandatory=1` and `value=""`, then concatenates `field_name` into a throw message. Frappe child grids persist a row as soon as Mandatory is checked, so `field_name` can be `None` and the concatenation raises `TypeError`.

## Inputs

- Remote app: `visaguy_crm` on `fasil@code.tridz.in:2203` at `/home/fasil/fasil-bench2/apps/visaguy_crm`
- Function: `check_lead_verification` in `visaguy_crm/allocated_to_process_file.py`
- Tests: `visaguy_crm/test_allocated_to_process_file.py`

## Required behaviour

- Skip information rows whose `field_name` is blank, `None`, or whitespace.
- Keep blocking when a named mandatory information field has an empty value.
- Throw with `_("... {0} ... {1} ...").format(field_name, file_collection)`.
- For the file check, use `group_name or file_name` in the message.
- Keep the existing `value=""` filter for information rows.

## Constraints

- Implement over SSH on the remote bench. Do not edit local `/home/fasil/Tridz/bench_v15`.
- Leave git changes unstaged. Do not commit or push unless asked.
- Do not make `field_name` required on FileFlo child DocTypes.
- Do not change FileFlo guest-form InfoForm validation.

## Expected changes

- `visaguy_crm/allocated_to_process_file.py`: filter nameless information rows; safe throw formatting for information and file checks.
- `visaguy_crm/test_allocated_to_process_file.py`: mocked tests for empty-row skip, named-field block, and file-label fallback.

## Validation

- Unit tests on the remote bench (`visaguy_crm.test_allocated_to_process_file`): 10 passed, including empty-row skip, whitespace skip, named-field block, and file-label fallback. Site `allow_tests` is off, so they were run as standalone unittest with frappe patched.
- Live Create Process File click on the remote site was not re-run after the change.

## Definition of done

- Remote `visaguy_crm` code and tests are updated and left unstaged.
- Unit tests pass on the remote bench.
- Workspace feature and this task document exist and stay aligned.
