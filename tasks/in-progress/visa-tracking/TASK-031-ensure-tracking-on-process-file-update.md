---
id: TASK-031
feature: FEAT-001
title: Create tracking on Process File update, and a manual Generate action
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-012
  - ADR-014
  - ADR-015
  - ADR-016
  - TASK-036
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
- TASK-036 sets `field_id = "passport"` on every primary passport row, on
  templates and existing collections. **This task needs TASK-036 deployed
  first.** It never matches file names.
- On open files the passport row is in `custom_lead_file_collection`, not
  `file_collection`.
- `run_fileflo_inspection(collection)` already does what is needed per
  collection: it takes rows whose `field_id` is in `passport_field_ids`,
  skips rows that are not `Completed`, and creates or reuses one extraction
  per row (idempotent). This task reuses it.
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
4. Call `run_fileflo_inspection` for `custom_lead_file_collection`, then
   for `file_collection` (skip empty or equal values). Do not change it.
5. Map its per-row results to one outcome code, in this order:
   - a row `created` → `extraction_queued`;
   - a row `reused` → `extraction_pending`, or `needs_review` when that
     extraction is in `Needs Review`;
   - only `FAILED_RECORD_EXISTS` → `extraction_failed` (the Retry action
     applies);
   - only `ROW_NOT_COMPLETED` → `passport_not_completed`;
   - no passport row in either collection → `no_passport_row`;
   - `no_field_ids` → `not_configured` (the setting is empty).
6. Several passport rows (front and back pages) give one extraction each.
   That is accepted: the page without an MRZ ends `Failed`, and the other
   creates the application.
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

### 3a. Same identity twice in one Lead (risk 48)

In `create_tracking_application`, before a new application is created:
if another applicant row **on the same Lead** already links an application
with the same `verification_lookup_hash`, create nothing and flag for
review ("same passport on several applicants of one Lead"). One person is
never two applicants in one case. The usual cause is one scan of several
passports uploaded for every family member. The same identity on a
different Lead stays allowed (ADR-015). Outcome code:
`duplicate_identity_in_lead`. Add it to TASK-035's reasons.

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
- Do not write to FileFlo rows. TASK-036 sets the field IDs once.
- Do not log passport numbers, names or dates of birth.

## Expected changes

A new service, a save-hook addition, one job, one whitelisted desk method,
and a client script button. Tests for each outcome code.

## Validation

- Pure tests for the mapping from inspection results to outcome codes.
- On-site tests on `visa-tracker-test.localhost`:
  - a primary with a Completed passport row with `field_id = passport` gets an application
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
  - a `Rejected` file enqueues nothing; a `Completed` file is tracked;
  - two applicant rows of one Lead with the same passport: the first gets
    an application, the second is flagged and gets none.
- Desk check by an Operations user: the button, the message, and the link
  appearing after refresh.

## Definition of done

All validation passes, the commit SHA is recorded here, and the soft-launch
plan's "Coverage" check can read the outcome codes.

## Implementation (2026-09-28)

Branch `feat/visa-tracker` in `the_visaguy` on the bench (installed checkout), commits `e238e1f`, merged `ceb30cd`. Pushed 2026-10-05 (`the_visaguy` `feat/visa-tracker` `80a5c3a`, `passport_extractor` `316154e`); not deployed.
Built by Cursor executors, reviewed and merged by the orchestrator; records in
`ongoing/visa-tracking-soft-launch/`.

Evidence: 78 pure tests; smoke test S1–S13 on the test site (save enqueues, extraction queued, Needs Review, verify, link, status recompute, same-Lead guard, Rejected skip, role refusal). Full suites on `visa-tracker-test.localhost` after all merges: `the_visaguy` 638 OK, `passport_extractor` 98 OK (`--skip-test-records`).

## What remains

1. Owner migrates and tests `visaguy` (never run by Claude; see memory rule).
2. Browser check of the desk UI.
3. Deploy (owner). Pushed 2026-10-05.
