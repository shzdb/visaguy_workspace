---
id: TASK-031
feature: FEAT-001
title: Create tracking on Process File update, and a manual Generate action
status: ready
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-012
  - ADR-014
  - ADR-015
  - ADR-016
expected_files:
  - the_visaguy/visa_tracking/services/ensure_service.py
  - the_visaguy/visa_tracking/handlers/process_file_handlers.py
  - the_visaguy/visa_tracking/jobs.py
  - the_visaguy/visa_tracking/api/desk.py
  - the_visaguy/fixtures/client_scripts.json
  - the_visaguy/visa_tracking/tests/test_ensure_service.py
created: 2026-09-28
updated: 2026-09-28
---

# TASK-031: Create tracking on Process File update, and a manual Generate action

## Owner decisions (2026-09-28)

- D1: tracking is created in every workflow state except `Rejected`.
  Completed and Documents Delivered files are tracked.
- D2: verification is always automatic (ADR-007 amendment).
- D4: `Operations Associate` and `Operations Team Lead` can create tracking
  (the manual actions). `System Manager` keeps access.
- D9 is a deploy setting, not code. See step 6.

## Objective

Implement ADR-016. A Process File that is saved without a tracking
application gets one, for the primary and for each dependant file. The same
logic runs from a manual action on the form.

## Context

- Legacy passport rows are already `Completed`, so the ADR-012 trigger
  never fires for them again.
- No legacy primary passport row has a `field_id`. On `visaguy` the
  Completed passport rows of open files are named `Passport` (7,359),
  `Passport Copy - N` (2,688), `Passport - N` (1,956), `Passport Copy` (75),
  `Passport1`/`Passport2` (45) and `Passport جواز سفر` (5).
- Every such row is in `custom_lead_file_collection`, not `file_collection`.
- Downstream code needs no `field_id`: `handle_verified_extraction` resolves
  the Lead and the applicant row from the extraction's source collection.
- `run_fileflo_inspection` skips rows without a configured `field_id`, so
  this task must not call it for legacy rows.
- A file collection belongs to one person (owner, 2026-09-28). Several
  passport rows are pages of one passport.

## Required behaviour

### 1. One service: `ensure_tracking(process_file)`

Returns an outcome code and does these steps:

0. If `Visa Tracker Settings.enabled` is off, return `disabled`. The save
   hook checks this too, before it enqueues, so turning the setting off is a
   rollback (soft-launch plan, "Rollback").
1. If `custom_visa_tracking_application` is set, return `already_linked`.
2. If the workflow state is `Rejected` (D1), return `excluded_state`.
3. Try `link_process_file_to_tracking` first. An application can exist
   already (for example the Lead-stage extraction was verified before the
   Process File existed). If it links, recompute the status (step 7) and
   return `linked_existing`.
4. Find the passport rows in `custom_lead_file_collection`, then in
   `file_collection`:
   - rows whose `field_id` is in `passport_field_ids`; else
   - rows whose normalized `file_name` matches the legacy list. Normalize:
     trim, lower-case, merge whitespace, remove a trailing ` - N`, then
     compare with `passport`, `passport copy`, `passport1`, `passport2`,
     `passport جواز سفر`. Keep the list in one constant.
   - Only rows with `status = Completed` and a `document`.
   - Never rows named like "previous passport", "other nationality" or
     "accompanying member".
5. If no row is found, return `no_passport_row`, `passport_not_completed` or
   `passport_no_file`.
6. Look for an existing extraction for the collection. Reuse any status
   except `Failed`, `Duplicate` and `Superseded`, and return
   `extraction_pending` or `needs_review`. Otherwise create one with
   `get_or_create_passport_extraction` for the first row (`Passport` or the
   ` - 1` row first), then `enqueue_passport_extraction`. For legacy rows use
   `source_field_id = "legacy_passport"`. Return `extraction_queued`. If
   that extraction fails, try the next row in a later run.
7. After an application links, call `recompute_client_status` so the status
   comes from the workflow state and not from the Lead default status.

### 2. Save trigger

- On `PF Process File` `on_update`, when the link is empty and the state is
  included, enqueue `ensure_tracking` on the short queue. Use a job ID per
  Process File so repeated saves do not stack jobs. Enqueue after commit.
- Do no other work in the request. No file access, no OCR.
- For a primary file, also enqueue the job for each dependant Process File
  (`get_process_file_family`) that has no link.

### 3. When verification finishes

The extraction is asynchronous. When `handle_verified_extraction` creates or
reuses the application, the existing `_maybe_link_process_file_for_application`
links the Process File. Make sure step 7 also runs on this path.

### 4. Error Log deduplication

Outcomes that need a person (`applicant row not resolved`, `lead has no
destination`) must write one Error Log entry per Process File and reason,
not one per save.

### 5. Manual action: "Generate Visa Tracking"

- A button in the form's **Actions** menu when the link is empty, for
  `Operations Associate`, `Operations Team Lead` and `System Manager` (D4).
- It calls a whitelisted method that runs `ensure_tracking` for this file
  and its dependants. It enqueues; it does not run OCR in the request.
- It shows the outcome per file in a message, in plain words. Example:
  "Passport row is not marked Completed." or "Extraction queued. Refresh in
  a few minutes."
- The method checks the role on the server.
- A second button, **Retry passport extraction**, appears when the latest
  extraction for the collection is `Failed`. It creates a new extraction
  with `triggered_by = "Retry"`.

### 6. Process File created status (decision D9)

`link_process_file_to_tracking` applies `process_file_created_status` when
`enable_process_file_created_transition` is set. For a legacy file this adds
a timeline entry that step 7 replaces at once. Do not change this code. The
owner sets the setting at deploy (D9).

## Constraints

- No bulk run. Do not add a scheduled job that processes all open files.
- The save hook must not raise. Catch and log inside the job.
- Do not change `run_fileflo_inspection` or the ADR-012 trigger.
- Do not write to FileFlo rows. Do not set `field_id` on legacy rows.
- Do not log passport numbers, names or dates of birth.

## Expected changes

A new service, a save-hook addition, one job, one whitelisted desk method,
and a client script button. Tests for each outcome code.

## Validation

- Pure tests for the file-name normalization, with each name in Context and
  each excluded name.
- On-site tests on `visa-tracker-test.localhost`:
  - a primary with a Completed legacy `Passport` row gets an application
    after the job and the extraction run;
  - a dependant file gets its own application;
  - a saved file that already has a link enqueues nothing;
  - ten saves in a row enqueue one job;
  - a file with no passport row writes no Error Log entry;
  - an unresolved applicant row writes one Error Log entry across several
    saves;
  - the status after linking matches `resolve_client_status` for the
    workflow state;
  - the manual action refuses a user without one of the three roles;
  - a `Rejected` file enqueues nothing; a `Completed` file is tracked.
- Desk check by an Operations user: the button, the message, and the link
  appearing after refresh.

## Definition of done

All validation passes, the commit SHA is recorded here, and the soft-launch
plan's "Coverage" check can read the outcome codes.
