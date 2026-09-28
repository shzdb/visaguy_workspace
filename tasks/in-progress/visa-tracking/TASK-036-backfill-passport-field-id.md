---
id: TASK-036
feature: FEAT-001
title: Patch that sets the passport field ID on templates and existing collections
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-012
  - ADR-016
expected_files:
  - the_visaguy/patches/v1_0/set_passport_field_id.py
  - the_visaguy/patches.txt
  - the_visaguy/visa_tracking/tests/test_set_passport_field_id_patch.py
created: 2026-09-28
updated: 2026-09-28
---

# TASK-036: Patch that sets the passport field ID on templates and existing collections

## Objective

Give every primary passport row the FileFlo field ID `passport`, on the
templates and on existing file collections. After this, one rule finds the
passport everywhere: `field_id = "passport"`. No live code matches file
names (owner, 2026-09-28; ADR-016 amendment).

## Context (site `visaguy`, 2026-09-28, runtime-verified)

- `FF Field ID` `passport` exists (fields `field_id`, `field_label`).
  `FF File Template File` and `FF File Collection File` both have
  `field_id` (Data) and `field_id_link` (Link to `FF Field ID`).
- Templates: 429. Rows named `Passport Copy` or `Passport`: 227. Only 4
  have `field_id = passport`; 223 have none.
- Collections: 55,408. Primary passport rows: 37,490 in 29,176
  collections. None has a `field_id`.
  - 27,539 rows match a passport row on the collection's current template.
  - 9,938 rows have a template that no longer has a row of that name
    (template edited after the collection was made).
  - 13 rows have no template.
  - So the patch matches collection rows by name, not through the
    template.
- Row status: 24,703 Completed with a file, 2,867 Uploaded, 9,579 blank
  without a file (upload not done yet), 9 Rejected, others few.
- In `fileflo` and `visaguy_crm`, `field_id` on a file row is only copied
  along during uploads (`data_collecting_form.py`). Nothing else reads it.
  Setting it does not change how forms behave.

## Required behaviour

### 1. Matching rule (only here, in the patch)

Normalize `file_name`: replace non-breaking spaces, trim, lower-case, merge
whitespace, remove a trailing ` - N`. Match when the result is one of
`passport`, `passport copy`, `passport1`, `passport2`, `passport جواز سفر`.

Never match: "Spouse Passport Copy", "Previous passport", "Old passport",
other-nationality rows, accompanying-member rows, "sponsor's passport". A
collection belongs to one person, so another person's passport row in it
is not this applicant's passport.

### 2. Updates

- Template rows that match and have an empty `field_id`: set `field_id =
  "passport"` and `field_id_link = "passport"`.
- Collection rows that match and have an empty `field_id`: the same.
- Never overwrite a non-empty `field_id`. Count and print any matched row
  that has a different one.

### 3. No side effects (critical)

Write with `frappe.db.sql` bulk `UPDATE` (or `frappe.db.set_value(...,
update_modified=False)`), **never** a document save. A save runs the
`FF File Collection` / `FF File Collection File` hooks (ADR-012), which
would queue OCR for about 24,700 Completed rows at once. That is the bulk
backfill ADR-016 rejected.

Also:

- Do not call `enqueue_missing_fileflo_extractions` or
  `reconcile_missing_extractions` after the patch. After it, both would
  queue every Completed passport row on the site. Add a guard to both: they
  refuse to run unless called with an explicit `limit` or a list of
  collections. Record this in the runbook.
- Do not change `modified`.

### 4. Form and runs

- A Frappe patch in `the_visaguy/patches.txt` under `[post_model_sync]`,
  so it runs once on migrate, before TASK-031's hook is used.
- A `dry_run` function the owner can call with `bench execute` before the
  deploy. It prints the counts in Context (templates, rows, per status,
  skipped names) and writes nothing.
- The patch prints the same counts. It is idempotent: a second run updates
  nothing.

### 5. After the patch

Set `Visa Tracker Settings.passport_field_ids` to `passport` (Phase 2 of
the soft-launch plan). New collections made from a patched template get
the field ID from the template.

## Constraints

- No change to `fileflo` or `visaguy_crm` code.
- No OCR, no enqueue, no Error Log per row.
- Do not log file URLs or names of people.

## Validation

- Pure test for the name normalization: every matched name in Context,
  every excluded name, non-breaking spaces, ` - 12`.
- On `visa-tracker-test.localhost`: fixture template and collections;
  after the patch the right rows have `field_id = passport`; excluded rows
  are unchanged; a row with another `field_id` is unchanged; no job is in
  the queue; `modified` is unchanged; a second run changes nothing.
- A new collection generated from a patched template has the field ID on
  its passport row. If it does not, record where FileFlo builds rows and
  stop.
- On production, the dry run's counts are recorded here before the deploy.

## Definition of done

Validation passes, the dry-run and patch counts from production are
recorded here, and the commit SHA is recorded.

## Implementation (2026-09-28)

Branch `feat/visa-tracker` in `the_visaguy` on the bench (installed checkout), commits `5d0a3b8`, `5f1cf81`, merged `6f1db0d`. Not pushed, not deployed.
Built by Cursor executors, reviewed and merged by the orchestrator; records in
`ongoing/visa-tracking-soft-launch/`.

Evidence: 24 pure tests; patch ran on test-site migrate (created FF Field ID `passport`; 0 rows, no FileFlo data there); second run updates 0. Not run on `visaguy` (owner). Full suites on `visa-tracker-test.localhost` after all merges: `the_visaguy` 638 OK, `passport_extractor` 98 OK (`--skip-test-records`).

## What remains

1. Owner migrates and tests `visaguy` (never run by Claude; see memory rule).
2. Browser check of the desk UI.
3. Push and deploy (owner).
