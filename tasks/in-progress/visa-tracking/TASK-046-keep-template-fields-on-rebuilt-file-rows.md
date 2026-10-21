---
id: TASK-046
feature: FEAT-001
title: Keep template fields on file rows that uploads and rejections rebuild, and repair existing rows
status: in-progress
repository: visaguy_crm
app_path: /home/shahzad/bench/apps/visaguy_crm
owners: []
depends_on:
  - TASK-036
related:
  - TASK-013
expected_files:
  - visaguy_crm/data_collecting_form.py
  - visaguy_crm/rejection_document_email_sending.py
  - visaguy_crm/patches/backfill_file_row_template_fields.py
  - visaguy_crm/patches.txt
  - visaguy_crm/test_file_collection_rows.py
  - visaguy_crm/file_collection_rows.py
created: 2026-10-21
updated: 2026-10-21
---

# TASK-046: Keep template fields on file rows that uploads and rejections rebuild, and repair existing rows

## Objective

When the customer uploads files or staff reject a file, every
`FF File Collection File` row must keep these values from its template
row:

- `field_id`
- `field_id_link`
- `format`
- `description`
- `conditions`

A patch must also repair the existing rows that lost these values.

## Context

Investigated 2026-10-21. Code: **source-wired** (bench checkouts, `main`,
up to date with upstream). Data: **runtime-verified** on the `visaguy`
dev site. That site was restored from a live backup, and its newest
collection is from 2026-10-05. Live data after go-live was **not** checked.

### The copy at creation is correct

All creation paths (`file_collection_from_lead.create_ff_file_collection`,
`allocated_to_process_file`) call `fileflo.document_fetch.document_fetch`.
That function copies every field with the same name from the template rows,
so all five values arrive. Nothing has changed it since 2026-02.

### Rows that are rebuilt later lose values

1. **Multi-upload in the customer form.** `fileflo.data_collection.add_form_data`
   is overridden by `visaguy_crm.data_collecting_form.add_form_data`
   (`override_whitelisted_methods`). For a field with `multiple = 1`, the
   override:
   - adds one row for each uploaded file,
   - removes the input row that came from the template,
   - adds the input row again when upload capacity remains.

   These new rows copy `field_id` (since `b573e2c`) but never
   `field_id_link`. They take `format`, `description` and `conditions`
   from the browser request (`data.get(...)`), not from the stored row, so
   these values are empty when the request does not send them. The
   single-upload path changes the row in place, so it keeps everything.
2. **Additional Documents.** The `is_additional_documents` branch of the same
   function adds rows without either ID. The template has an
   `Additional Documents` row with field ID `additional_documents`.
3. **Rejection.** `rejection_document_email_sending.send_rejection_email`
   is a `before_save` hook on `FF File Collection`. When a file in a
   `multiple = 1` group is rejected, the hook deletes every row of the group
   and adds one new row (`new_file_data`). That row has only `file_name`,
   `group_name`, `mandatory`, `remarks`, `multiple`, `max_allowed` and
   `status`. It has no field IDs, no `format` (so the re-upload accepts any
   file type), no `description` and no `conditions`. On the next upload, the
   override copies the empty values from that row, so they are lost for good.

### Size on the dev site (all collections, exact `file_name` match to the template row)

Rows where the template row has a value but the collection row does not:

| Value | Rows |
|---|---|
| `field_id_link` (2026-09-01 to 2026-10-05 only) | 618 |
| `format` | 109 |
| `description` | 889 |
| `conditions` | 2,902 |
| `Rejected` rows without `format` | 13 |

These counts only include rows whose `file_name` matches a template row
exactly. Uploaded rows (` - N` suffix) are not in them, so the real numbers
are higher. The patch's `dry_run` gives the full numbers.

### Timeline

- Before 2026-10-06, the override on live copied neither field ID. Every
  dev row that lost its IDs was created or rebuilt by a multi-upload. Every
  row that the customer did not touch kept them.
- On 2026-10-06, PR #232 (`feat/visa-tracker`) merged `b573e2c` into
  `visaguy_crm` `main`. After that the override copies `field_id`, but still
  not `field_id_link`.
- Visa tracking went live on 2026-10-06. It is the first feature that reads
  the IDs, which is why the loss became visible then.

Example on the dev site: collection
`Abdul Nazar Edavazhipurath Kabeer-TVGUC-51281233266`, template
`FFTP-Schengen-Primary-Operations-07007`. The two rows the customer did not
touch have both IDs. The four rows rebuilt by the multi-upload path
(accompanying-member passport, Previous Schengen Visa) have `NULL` in both.

### Related

- TASK-013 (blocked) is about merging the forked upload logic with fileflo.
  This task does not decide that question. It only fixes the fork that live
  calls.
- `fileflo.data_collection.add_form_data` has the same gaps. Live does not
  call it, so it is not part of this task.

## Inputs

- Bench: `ssh erpcode`, `/home/shahzad/bench`. Test site:
  `visa-tracker-test.localhost`.
- Name of a field ID: `FF Field ID` is named by its `field_id`
  (`autoname: field:field_id`). The two values on a row are therefore the
  same string.
- Field types on both row DocTypes: `format` Data, `description` Long Text,
  `conditions` Small Text.

## Required behaviour

In this section, "the five values" means `field_id`, `field_id_link`,
`format`, `description` and `conditions`.

### 0. Confirm on live first (owner, read-only)

The owner runs a read-only query on live for collections created after
2026-10-06. It shows which of the five values rebuilt rows are missing.
Record the result here. The code change is the same in every case.

### 1. Upload override (`data_collecting_form.add_form_data`)

- Copy the five values from the stored source row (`file_collection_file`)
  to every row added in the multi-upload branch: each uploaded-file row and
  the re-added input row. Use the stored row, not `data`, which comes from
  the browser.
- If the source row has only one of the two field IDs, fill the other with
  the same value. Set `field_id_link` only when an `FF Field ID` with that
  name exists.
- Additional Documents branch: take the five values from an existing row in
  the same collection with the same `group_name`. If there is no such row,
  keep the current behaviour.

### 2. Rejection hook (`send_rejection_email`)

- Add the five values from the first row of the rejected group to
  `new_file_data`.

### 3. Backfill patch for existing rows

A `[post_model_sync]` patch in `visaguy_crm/patches.txt`, plus a `dry_run`
function that the owner can call with `bench execute`. The patch repairs
all existing collections, not only the ones created after 2026-10-06.

- **Candidates:** `FF File Collection File` rows
  (`parenttype = FF File Collection`) where at least one of the five values
  is empty.
- **Matching:** match each row to one row of the collection's current
  `file_template`.
  1. Normalize `file_name` on both sides and compare: replace non-breaking
     spaces, trim, merge whitespace, lower-case, and remove a trailing
     ` - N`.
  2. If that gives no match, use `group_name`, but only when exactly one
     template row has that `group_name`.
  3. If there is no match, or more than one, skip the row and count it.
- **Filling:**
  - Fill only empty values. Never overwrite a non-empty value. Count rows
    where an existing value is different from the template's.
  - `field_id` comes from the template row's `field_id`, or else its
    `field_id_link`. `field_id_link` comes from the same two values in the
    opposite order, and is set only when that `FF Field ID` exists.
  - `format`, `description` and `conditions` are copied from the template
    row when the template row has a value.
- **Writing:** use chunked bulk `UPDATE` statements, as TASK-036 does.
  Never save a document. A save runs the `FF File Collection` hooks: it
  would send rejection emails and recalculate other values. Do not change
  `modified`.
- **Report:** print counts for each value and for each row status, and
  counts of skipped rows (no template, no match, ambiguous match, existing
  value different). A second run updates nothing.

## Constraints

- No change to `fileflo` or `the_visaguy`.
- No behaviour change other than the five values. Keep row names,
  numbering, capacity, mandatory and rejection email logic exactly as they
  are.
- Filling `conditions` changes which rows the customer form shows, because
  it restores the template's display rules. That is the intended result.
  The validation checks it on one real collection per template type.
- Do not log file URLs or names of people.
- Never run on `visaguy` or live. The owner migrates and deploys.

## Expected changes

- `visaguy_crm/data_collecting_form.py`: copy the five values in the
  multi-upload branch (uploaded rows and the re-added input row) and in the
  Additional Documents branch.
- `visaguy_crm/rejection_document_email_sending.py`: add the five values to
  `new_file_data`.
- New patch file with `execute` and `dry_run`, and its `patches.txt` entry.
- Tests.

## Validation

On `visa-tracker-test.localhost`
(`bench --site visa-tracker-test.localhost run-tests --app visaguy_crm --skip-test-records`):

- Multi-upload with remaining capacity: every uploaded row and the
  re-added input row have the five values, even when the request leaves out
  `format`, `description` and `conditions`.
- Multi-upload that fills the capacity: every uploaded row has the five
  values.
- Single upload: the row keeps the five values (regression).
- Reject one file in a `multiple = 1` group: the new row has the five
  values, and a later upload into it gives rows with the five values. Mock
  the email send.
- Additional Documents, with and without a matching row in the same
  collection.
- Patch fixtures cover:
  - a normalized-name match and a `group_name` match,
  - an ambiguous match and a row with no template,
  - a row with a different existing value,
  - a row with only one of the two field IDs,
  - a template row with an empty `description`.

  After the run, only the correct values change, `modified` is unchanged,
  no email or job is queued, and a second run changes nothing.
- Open the customer form for one repaired collection of each template type
  and check that the rows shown are the template's rows.
- `dry_run` counts are recorded here, first on the test site and then by
  the owner on live before the deploy.

## Definition of done

- All validation passes.
- The commit SHA and branch are recorded here.
- The owner's live check from step 0 and the live `dry_run` counts are
  recorded here.
- Deploy is owner-only.

## Not in scope

- Merging the forked upload logic with fileflo is TASK-013.

## Implementation (2026-10-21)

Branch `fix/file-row-template-fields` in `visaguy_crm`, cut from
`upstream/main` (`daa863e`), commit `7dc785c`. One branch for both targets
(owner decision: no separate stage history; owner resolves any conflicts).

- PR to `main`: https://github.com/tridz-dev/visaguy_crm/pull/247
- PR to `stage`: https://github.com/tridz-dev/visaguy_crm/pull/248

Both PRs merge without conflicts.

Follow-up commits on the same branch (2026-10-21):

- `246e398`: `FileRowFactory` (`file_collection_rows.py`) is now the only
  builder of rebuilt rows (`uploaded_row`, `slot_row`, `additional_row`,
  `rejected_row`). Inherited values come from the stored row, then the
  template row, then the request. The rejection replacement row takes
  `file_name`, `mandatory`, `multiple` and `max_allowed` from the template
  row (gap 1). The patch uses the same `TemplateIndex`. A guard test fails
  if code appends a `file_collection_file` row from a dict literal outside
  the factory. This replaces `file_row_template_fields.py`.
- `867d767`: comments trimmed; no workspace references in code (owner rule,
  now in `.agents/rules/project-rules.md`).

Open owner decisions (not in this change):

- After a multi-upload, no row in the group is mandatory, by design. A
  rejection of the only upload does not force a re-upload. Dev data: 0
  groups today.
- 66,134 groups changed before 2026-06 have less capacity than the template
  allows, because the old upload code dropped the slot row.

Files:

- `visaguy_crm/file_collection_rows.py` (new): `FileRowFactory`, `TemplateIndex`.
- `visaguy_crm/data_collecting_form.py`: multi-upload rows and Additional
  Documents rows take the values from the stored row. The request only fills
  what the stored row lacks.
- `visaguy_crm/rejection_document_email_sending.py`: the replacement row
  keeps the five values.
- `visaguy_crm/patches/backfill_file_row_template_fields.py` (new) with
  `execute` and `dry_run`. Registered in `patches.txt` under
  `[post_model_sync]`.
- `visaguy_crm/test_file_collection_rows.py` (new).

`step` (multi-step forms) exists only on `stage`'s FileFlo, so it is not in
this change.

Evidence:

- 28 pure tests pass. 7 of them fail with the `main` versions of the two
  changed files.
- The other pure tests in the app pass. `server_scripts.lead.test_lead_hooks`
  fails to load on unchanged `main` as well.
- The candidate SQL was run read-only on `visaguy`: 268,077 candidate rows of
  269,338, 21 without a template.
- GitHub CI "Server" fails at job setup because the workflow uses the
  deprecated `actions/cache@v2`. All branches fail the same way since at
  least 2026-10-09, so no tests ran in CI.

Not run:

- On-site tests: these need the installed checkout switched, which needs
  owner go-ahead.
- The patch or `dry_run` against a database.

## What remains

1. Owner: the read-only live check (step 0).
2. Owner: run `dry_run` on live and record the counts here.
3. Owner: merge, migrate and deploy.
4. After the migrate, check one repaired collection per template type in the
   customer form.
5. Remove the bench worktree `/home/shahzad/sl-worktrees/visaguy_crm-task046`
   after the merge.
