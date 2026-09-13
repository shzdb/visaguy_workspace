---
id: TASK-023
feature: FEAT-001
title: Stop Lead conversion re-runs from duplicating dependant rows
status: in-progress
repository: visaguy_crm
app_path: /home/shahzad/bench/apps/visaguy_crm
owners: []
depends_on: []
created: 2026-09-13
updated: 2026-09-13
---

# TASK-023: Stop Lead conversion re-runs from duplicating dependant rows

Recorded after the fact. The owner committed this on the bench on
2026-09-07.

## Objective

Make sure the public tracking payload lists each dependant once, when a Lead
is converted to Process Files more than once.

## Context

`visaguy_crm.allocated_to_process_file.create_process_file` calls
`create_connection_to_primary_file` outside the per-applicant guard in
`create_pf_process_file`. A second conversion of the same Lead appended a
second identical `Dependent Process File Details` row and
`Dependent File Collection Details` row. The tracker then listed the
dependant twice.

## Changes

`visaguy_crm` `de7c959` (2026-09-07, "fix: skip duplicate dependant rows on conversion re-run"):

- New `_dependent_row_exists(child_doctype, parent, parenttype, applicant_name, applicant_type)`,
  keyed on `(parent, applicant_name, type)` under `custom_dependent_details`.
- `create_connection_to_primary_file` checks it before each of its two
  inserts.

## Validation

- No automated test was added for this change.
- 2026-09-13, data on site `visaguy` (read-only query): the stored links in
  both child tables are valid (0 rows point to a missing Process File or
  file collection). Duplicates that existed before the fix are still there:
  **3** duplicate groups in `Dependent Process File Details` and **4** in
  `Dependent File Collection Details`.

## Gaps found on review (2026-09-13)

1. **A partial earlier run cannot be repaired.** When the Process File
   detail row already exists, the function returns before it checks the
   file-collection detail row. If an earlier run wrote the first row and
   failed before the second, a re-run never writes the second. The different
   duplicate counts above (3 against 4) show the two tables already disagree.
   Fix: check the two rows independently instead of returning early.
2. **Existing duplicates are not cleaned.** The guard only prevents new
   ones. The tracker still lists those dependants twice.
3. **No test.** A test should cover a re-run, and a re-run after a partial
   first run.

## What remains

1. Fix gap 1 and add the test (gap 3).
2. Owner decision on removing the existing duplicate rows (gap 2). Report
   the rows before deleting anything.
3. Deploy. See risk 36.
