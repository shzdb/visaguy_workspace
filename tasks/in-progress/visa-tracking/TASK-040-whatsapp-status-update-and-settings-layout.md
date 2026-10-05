---
id: TASK-040
feature: FEAT-001
title: WhatsApp message on tracking status change, tracker URL in Whatsapp Default, tabbed settings and extraction forms
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-031
  - TASK-032
  - TASK-038
expected_files:
  - the_visaguy/visa_tracking/services/status_service.py
  - the_visaguy/handlers/whatsapp_message.py
  - the_visaguy/visa_tracking/jobs.py
  - the_visaguy/visa_tracking/services/ensure_service.py
  - the_visaguy/visa_tracking/services/reconciliation_service.py
  - the_visaguy/communications/doctype/whatsapp_default/whatsapp_default.json
  - the_visaguy/communications/doctype/whatsapp_default/whatsapp_default.py
  - the_visaguy/communications/doctype/whatsapp_default_templates/whatsapp_default_templates.json
  - the_visaguy/the_visa_guy/doctype/visa_tracker_settings/visa_tracker_settings.json
  - the_visaguy/the_visa_guy/doctype/visa_tracker_settings/visa_tracker_settings.py
  - the_visaguy/the_visa_guy/doctype/visa_tracking_status/visa_tracking_status.json
  - the_visaguy/patches/
  - passport_extractor/passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.json
created: 2026-10-05
updated: 2026-10-05
---

# TASK-040: WhatsApp message on tracking status change, tracker URL in Whatsapp Default, tabbed settings and extraction forms

Owner requests of 2026-10-05. Three parts. Parts A and B are in `the_visaguy`.
Part C touches two repositories (`the_visaguy` and `passport_extractor`).

**Branch.** Work directly on `feat/visa-tracker` in each repository (`the_visaguy`
and `passport_extractor`), the same branch as the rest of FEAT-001. Do not
create a task branch. Both bench checkouts are on `feat/visa-tracker` now.

Verification labels below follow `.agents/rules/project-rules.md`. Source was
read on the bench on 2026-10-05; nothing was run (source-wired, not
runtime-verified).

## Objective

1. Send one WhatsApp template message to the client when the status of their
   `Visa Tracking Application` changes.
2. Let operations turn this on and off per zone in `Whatsapp Default`, and keep
   the tracker URL there.
3. Make the `Visa Tracker Settings` and `Passport Extraction` forms easy to read
   with tabs and sections.

## Context

- One seam changes status: `status_service.update_tracking_status`. It already
  calls `alert_service.notify_status_change` when the status really changed
  (`changed` is true). The WhatsApp send goes next to that call.
- `Whatsapp Default` is one record per Zone. It has `enabled` (master switch),
  `whatsapp_account`, an `event_template` table (event type to template) and
  `handlers/whatsapp_message.py` has the send pattern: `is_enabled(zone,
  customer)`, `_get_whatsapp_default`, `_get_event_template`,
  `clean_mobile_no`, then `send_whatsapp_template(...)` on the `short` queue
  with `enqueue_after_commit=True`.
- The application links to a Lead or CRM Lead (`lead`, `crm_lead`). That record
  has `custom_zone`, `custom_customer_id`, `whatsapp_no`, `mobile_no` and
  `first_name`. Dependants share the primary's Lead (ADR-015).
- `Visa Tracker Settings.frontend_base_url` is read in one place only:
  `VisaTrackerSettings._validate_public_tracking_security`. ADR-013 removed it
  from the security layer and CORS is Frappe's (`allow_cors`, ADR-008). It has
  no runtime use, so it moves to `Whatsapp Default` (Part B).
- On go-live no Process File has an application (ADR-016). The first save of an
  old file creates the application and then recomputes its status. That
  recompute calls `update_tracking_status` with a previous status, so without a
  guard the client of a long-running file would be told "updated to In
  Progress" on the first save. Part A step 4 prevents this.

## Part A — WhatsApp message on status change

### Template (owner task, not code)

The owner creates a `WhatsApp Templates` record (waflo), submits it to Meta as a
utility template and waits for approval. Shape:

- Body: "Your visa application status for {{1}} is updated to {{2}}."
  {{1}} is the applicant name, {{2}} the **status name**: the `status_name`
  field of the `Visa Tracking Status` record (not the public title, and not the
  record name, which is the status code such as `QUESTIONNAIRE_SUBMITTED`).
- One URL button, "Track Application". Its URL in the template is the zone's
  tracker domain with a variable suffix (`https://<tracker-domain>/{{1}}`),
  because Meta allows a variable only at the end of the URL.

### Required behaviour

1. `Whatsapp Default.event_template.event_type` gets a new option
   `Visa Tracking Update`. Do **not** add it to `REQUIRED_EVENT_TYPES`: that
   would stop existing zones from saving while enabled.
2. New `_send_visa_tracking_update(application_name, log_name)` in
   `handlers/whatsapp_message.py`, same pattern as the other senders.
   - Load the application; resolve the Lead / CRM Lead from `lead` or
     `crm_lead`.
   - Return without sending unless **all** hold: the zone's
     `notify_visa_tracking_updates` is on; `is_enabled(zone, customer)`; a
     `Visa Tracking Update` template row exists; the number passes
     `clean_mobile_no`; the application is `tracking_enabled` and not
     `application_closed`; the status log row is `visible_to_client`; the
     status has a non-empty `status_name`.
   - Body params: `applicant_display_name` (fall back to `first_name`), then the
     `status_name` of the application's `current_status` (read with
     `frappe.get_cached_value("Visa Tracking Status", status, "status_name")`).
   - Button: `button_url_map={"0": <suffix>}`. The suffix is the part of the
     zone's `tracking_url` after the domain. When that part is empty, send
     `?ref=whatsapp`. Never send the passport number, date of birth or any
     lookup hash.
   - `ref_doctype="Visa Tracking Application"`, `ref_name=application_name`.
   - Any failure is logged to the `whatsapp` logger and never raised.
3. `update_tracking_status` enqueues the sender when `changed` is true **and**
   `previous_status` is set, with `queue="short"`, `enqueue_after_commit=True`,
   `job_id=f"visa-notify-{log.name}"`, `deduplicate=True`. The enqueue is
   wrapped so a failure never breaks the status write (same rule as the
   realtime alert).
4. **Silent catch-up (existing files).** Add a context flag
   (`frappe.flags.visa_tracking_silent`, set and always cleared in a
   `try/finally` helper) and set it in:
   - `jobs.ensure_tracking_job` and the manual Generate action path
     (`ensure_service.ensure_tracking` entry points);
   - `reconciliation_service.repair_client_status_drift`.
   When the flag is set, step 3 sends nothing. Everything an ensure run writes
   (first status, process-file-created transition, recompute) is a baseline,
   not news. Real changes after the application exists notify.
5. No backfill and no bulk send. Turning the switch on messages nobody about
   the past. Do not add a "notify since" timestamp.
6. Operator corrections from the Process File are written with
   `visible_to_client=False`; they send nothing (step 2 covers it).
7. Per-status opt-out: add a Check `notify_client` (default 1) to
   `Visa Tracking Status`, in the existing layout. Step 2 skips a status whose
   box is off. Ship all six configured statuses with it on; operations decide
   on `ON_HOLD` during the D6 wording review.

## Part B — tracker URL and switch in Whatsapp Default; remove from Visa Tracker Settings

1. `Whatsapp Default` gets a new tab **Visa Tracking** with:
   - `notify_visa_tracking_updates` (Check, default 0). Description: "Send a
     WhatsApp message to the client when their visa application status changes.
     Applies only to changes made after this is on."
   - `tracking_url` (Data, label "Tracker URL"). `depends_on` and
     `mandatory_depends_on` the switch.
2. `WhatsappDefault.validate`: when `notify_visa_tracking_updates` is on, require
   `tracking_url` (an explicit `https://` URL; `http://` allowed only for
   `localhost`; no wildcard), a `Visa Tracking Update` template row, and
   the `whatsapp_account` / `enabled` rules that already apply. Existing
   rules for other events do not change.
3. `Visa Tracker Settings`: remove `frontend_base_url` from the JSON and delete
   `_validate_public_tracking_security`'s Frontend Base URL checks. Keep the
   `generic_failure_message` check (move it to its own method with its own
   guard so it still runs when public tracking is on).
4. Patch: delete the orphan `Singles` row for `frontend_base_url` of
   `Visa Tracker Settings` (`frappe.db.delete("Singles", {...})`). Do **not**
   copy the old value into `Whatsapp Default`: it is `localhost` on one site
   and a test host on another. Operations enter the URL per zone.
5. Tests: remove the two `frontend_base_url` tests in
   `test_visa_tracker_settings.py`; in `visa_tracking/tests/test_public_api.py`
   replace `settings.frontend_base_url` with a module constant for the test
   origin (the origin is still sent as the `Origin` header to prove it gates
   nothing).

## Part C — tabs and sections

Layout only. Keep every `fieldname`, `fieldtype`, option, default,
`permlevel`, `read_only`, `hidden` and `depends_on` as it is. Change only
`field_order`, and add Tab Break, Section Break and Column Break fields with
labels. Bump `modified`. A field that sits before the first Tab Break shows
above the tabs.

Before editing, check `fixtures/property_setter.json` (and the other
fixtures) for a `field_order` Property Setter on `Passport Extraction` or
`Visa Tracker Settings`. If one exists it overrides the JSON (the TASK-032
Process File case). Remove or update it in the same commit.

### Visa Tracker Settings

| Tab | Section | Fields |
|---|---|---|
| (above tabs) | | `title`, `enabled` |
| General | Feature | (switches only; see below) |
| Passport Extraction | Extraction | `enable_passport_extraction`, `require_manual_verification`, `passport_field_ids`, `supported_extensions`, `maximum_file_size_mb` |
| Passport Extraction | Queues and retries | `inspection_queue`, `extraction_queue`, `inspection_retry_limit`, `extraction_retry_limit` |
| Lifecycle | Status | `default_lead_status` |
| Lifecycle | Process File created | `enable_process_file_created_transition`, `process_file_created_status` |
| Lifecycle | Automatic linking | `auto_create_tracking_application`, `auto_link_verified_passport` |
| Public Tracking | Access | `enable_public_tracking` |
| Public Tracking | Sessions | `session_expiry_minutes`, `max_session_lifetime_minutes` |
| Public Tracking | Abuse protection | `maximum_failed_attempts`, `lockout_minutes`, `scope_maximum_failed_attempts`, `scope_lockout_minutes` |
| Public Tracking | What the client sees | `status_history_limit`, `stale_status_days`, `generic_failure_message`, `support_link` |

Drop the "General" tab if it would be empty; `title` and `enabled` stay in the
header. Two columns inside a section where it helps (switches left, values
right); a section of one or two fields stays one column.

### Passport Extraction (`passport_extractor`)

| Tab | Section | Fields |
|---|---|---|
| (above tabs) | | `status`, `confidence`, `requires_review` (one row, three columns) |
| Passport | Passport values | `passport_number`, `passport_number_normalized`, `date_of_birth`, `expiry_date`, `document_type` / `surname`, `given_names`, `nationality`, `issuing_country`, `sex`, `personal_number` (two columns) |
| Source | Source and provenance | `passport_file`, `file_hash`, `source_doctype`, `source_document`, `source_field_id`, `source_row`, `triggered_by`, `requested_by`, `requested_on` |
| Processing | Processing | `processing_started_on`, `processing_completed_on`, `extraction_engine`, `engine_version`, `retry_count`, `last_job_id` |
| Processing | Errors | `error_code`, `error_message` |
| Verification | Review | `verified_by`, `verified_on`, `verification_notes` |
| Verification | Related records | `duplicate_of`, `supersedes`, `superseded_by` |
| Verification | MRZ evidence | `mrz_line_1`, `mrz_line_2`, `mrz_valid`, then the five `*_check_valid` fields in one column |
| Raw data | Raw OCR and result | `raw_ocr_text`, `raw_extraction_result` |

`status` etc. stay visible on every tab so a reviewer sees state while
reading values. Keep the TASK-033 buttons and the `passport_extraction.js` /
list script working; check they do not reference a field by position.

## Constraints

- Application repositories are the source of truth for code; commit locally on
  `feat/visa-tracker` and stop. The owner deploys and pushes. No
  `Co-Authored-By` trailer.
- Test only on `visa-tracker-test.localhost`. Never run migrate, patches or
  scripts on `visaguy`.
- No secrets, no WhatsApp credentials, no real phone numbers in tests or
  fixtures. Mock `send_whatsapp_template`.
- Do not change the public API, the SPA, or `status_service` semantics (log
  rows, idempotency, `alert_service`).
- Do not add the new event type to `REQUIRED_EVENT_TYPES`.
- Default for `notify_visa_tracking_updates` is off, on every zone, including
  zones that already exist.

## Validation

Pure tests:

- Sender: each skip rule (switch off, zone disabled, customer opted out, no
  template row, bad mobile, application closed or not tracking enabled, log
  not visible, status `notify_client` off) sends nothing; the happy path sends
  one call with the expected params and button suffix; a failure inside the
  sender does not raise.
- `update_tracking_status`: first status (no previous) sends nothing; a real
  change enqueues once with the log-based job ID; an idempotent no-op call
  enqueues nothing; the silent flag suppresses the enqueue and is cleared after
  an exception.
- `ensure_tracking_job` and `repair_client_status_drift` set the flag.
- `WhatsappDefault.validate`: switch on without URL, or without template row,
  fails; switch off passes with neither; an existing enabled zone without the
  new row still saves.
- Layout: for both doctypes, every original fieldname is still present once
  and every Tab/Section break has a label; `field_order` matches the JSON.

On the test site (migrate first):

- Visa Tracker Settings and Passport Extraction open with the tabs above; no
  field is lost or duplicated; saving Visa Tracker Settings works with public
  tracking on and no URL.
- `Whatsapp Default` for a test zone: switch on, URL and template row set, then
  an operator moves a test file's status and one message is queued with the
  right params. Switch off: nothing is queued.
- Existing-file case: take an open file without an application, save it. The
  application is created and its status set, and **no** message is queued.
  Then change its workflow state: one message is queued.
- The message carries the `status_name` value, not the public title or the code.
- The new patch runs once and is a no-op on a second run.
- On-site suite passes (`--app the_visaguy`, and `--app passport_extractor` for
  its own tests).

## Definition of done

Validation passes and the commit SHAs are recorded here, one per repository.
The owner confirms the approved Meta template name and the zone's tracker URL
before the switch is turned on for any zone; that step is outside this task.

## After the task (workspace)

- `docs/operations/visa-tracking-runbook.md`: the `frontend_base_url` rows
  (settings table, CORS check, the test-site value) now describe the CORS
  origin in `site_config` and the per-zone `tracking_url`.
- ADR-013: add a one-line note that `Visa Tracker Settings.frontend_base_url`
  was removed by TASK-040. Do not rewrite the accepted text.

## Implementation record (2026-10-05)

- the_visaguy: `6272ad7`, `c5f25d3`, `84601a7`, `80a5c3a` on `feat/visa-tracker` (local; not pushed).
- passport_extractor: `316154e` on `feat/visa-tracker` (local; not pushed).
- Merged on the bench by fast-forward; test site migrated. On-site: the_visaguy 778 OK, passport_extractor 103 OK.
- Test-site checks done: schema and layout, patch ran, a real change queues one message, silent and same-status calls queue none, sender sends nothing with the switch off.
- Still open before this task is `completed`: a real send on a test zone with an approved Meta template and the button suffix; the first-save-of-an-old-file case end to end; the layout viewed in the browser; the owner's deploy. See `ongoing/visa-tracking-soft-launch/10-task-040.md`.
