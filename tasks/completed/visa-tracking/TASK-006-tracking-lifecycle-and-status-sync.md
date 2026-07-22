---
id: TASK-006
feature: FEAT-001
title: Tracking lifecycle and status synchronization
status: completed
repository: the_visaguy
worktree: /home/shahzad/visa-tracker-worktrees/the_visaguy
owners: []
depends_on:
  - TASK-002
  - TASK-004
  - TASK-005
  - ADR-003
expected_files:
  - the_visaguy/the_visaguy/visa_tracking/services/lifecycle_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/status_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/reconciliation_service.py
  - the_visaguy/the_visaguy/visa_tracking/handlers/lead_handlers.py
  - the_visaguy/the_visaguy/visa_tracking/handlers/process_file_handlers.py
  - the_visaguy/the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py
  - the_visaguy/the_visaguy/hooks.py
  - the_visaguy/the_visaguy/fixtures/client_scripts.json
  - ongoing/visa-tracking-implementation/05e-task-006-implementation.md
created: 2026-07-21
updated: 2026-07-21
---

# TASK-006: Tracking lifecycle and status synchronization

## Objective

Implement the Lead/Customer/PF Process File lifecycle orchestration in `the_visaguy`: create and link `Visa Tracking Application` records from verified `Passport Extraction`, keep business-record Links consistent, provide a shared idempotent status service and append-only log, enable bidirectional synchronization between `PF Process File.custom_client_status` and `Visa Tracking Application.current_status` without recursion, support auditable direct corrections with reasons, and deliver report-only reconciliation jobs. This task does not implement OCR, FileFlo event handling, public APIs, or frontend work.

## Context

FEAT-001 splits repository ownership per ADR-003:

- `passport_extractor` owns `Passport Extraction` and extraction history (TASK-002).
- `fileflo` owns generic persistence and the post-save event (TASK-004).
- `the_visaguy` owns tracking domain orchestration, settings, custom fields, lifecycle services, and public API seams.
- `processflo` owns the base `PF Process File` DocType and is an integration target only; no source change is planned there.
- `visa_tracker` is the public SPA and is not touched in this task.

TASK-001 established the exact integration points with source evidence:

- FileFlo persists submissions in `FF File Collection`, `FF File Collection File`, and `FF File Collection Data`; the stable field-ID property is `field_id`.
- `FF File Collection.reference_type` / `reference_name` link to `Lead` or `CRM Lead`.
- `visaguy_crm.visaguy_crm.file_collection_from_lead.generate_file_collection_lead(lead_name, doctype="Lead")` creates File Collections from both ERPNext `Lead` and Frappe CRM `CRM Lead`.
- `visaguy_crm.visaguy_crm.allocated_to_process_file.create_process_file(lead_name, doctype="Lead")` creates `PF Process File` from either Lead DocType and writes back `applicant_details.process_file`.
- `PF Process File` already has `custom_reference_type`, `custom_reference_name`, and `file_collection`; the planned `custom_visa_tracking_application` and `custom_client_status` fields are supplied by `the_visaguy` fixtures (TASK-005).
- Both ERPNext `Lead` and `CRM Lead` are source-wired in the deployed flow.

TASK-005 delivers the tracking DocTypes (`Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`), fixtures, and service seams. TASK-006 fills in the lifecycle caller logic that uses those seams.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `tasks/ready/visa-tracking/TASK-004-fileflo-queued-passport-detection.md`
- `tasks/ready/visa-tracking/TASK-005-tracking-data-model-and-settings.md`
- `ongoing/visa-tracking-implementation/04a-task-001-recon-and-setup.md`
- `ongoing/visa-tracking-implementation/04b-task-001-finish-setup.md`
- Feature worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`
- Installed Frappe apps on site `visaguy`, including `the_visaguy`, `fileflo`, `processflo`, `erpnext`, `crm`, `visaguy_crm`
- Frappe 15 / Python 3.10 runtime

## Required behaviour

### 1. Repository and worktree discipline

1.1. Work only in `/home/shahzad/visa-tracker-worktrees/the_visaguy` on branch `feat/visa-tracker`. Do not modify the original `the_visaguy` checkout.

1.2. Do not create a branch, commit, or edit in `processflo`. All `PF Process File` customizations are supplied by `the_visaguy` fixtures per ADR-003.

1.3. Do not push to any Git remote.

### 2. Verified-extraction-to-business-record linking

2.1. Implement `visa_tracking.services.lifecycle_service.link_verified_extraction_to_lead(passport_extraction, lead_name, doctype="Lead")` that:

- validates `passport_extraction.status == "Verified"`,
- loads the target Lead or CRM Lead by `lead_name`,
- sets `custom_passport_extraction` on the Lead/CRM Lead to the `Passport Extraction` name,
- sets `custom_visa_tracking_application` on the Lead/CRM Lead if a tracking application already exists,
- does not create a tracking application itself (that is handled in Section 3),
- does not run OCR or public API logic,
- logs no passport number, DOB, or raw extraction content.

2.2. Implement `link_verified_extraction_to_customer(passport_extraction, customer_name)` that performs the same Link update on `Customer`.

2.3. Use the TASK-001-evidenced resolution paths:

- For a FileFlo source, resolve the Lead/CRM Lead through `FF File Collection.reference_type` and `FF File Collection.reference_name`.
- For a PF Process File source, resolve through `PF Process File.custom_reference_type` and `PF Process File.custom_reference_name`.
- Both DocTypes are confirmed source-wired; support `doctype="Lead"` and `doctype="CRM Lead"`.

### 3. Tracking application creation

3.1. Implement `visa_tracking.services.lifecycle_service.create_tracking_application(passport_extraction, lead_name, doctype="Lead", file_collection=None)` that:

- validates that `passport_extraction.status == "Verified"`,
- loads `Visa Tracker Settings` via `visa_tracking.utils.settings.get_visa_tracker_settings()`,
- stops if `enabled` is unchecked or `auto_create_tracking_application` is unchecked,
- checks for an existing active `Visa Tracking Application` for the same verified passport identity using `verification_lookup_hash` (re-use the existing record instead of creating a duplicate; flag a review note if the Lead differs),
- creates a new `Visa Tracking Application` with:
  - `passport_extraction` set to the verified extraction,
  - `lead` or `crm_lead` set per `doctype`,
  - `file_collection` set when provided,
  - `current_status` set to `Visa Tracker Settings.default_lead_status`,
  - `verification_lookup_hash` computed by `visa_tracking.services.lookup_service.compute_lookup_hash(...)` using the verified passport number and DOB,
  - `lookup_hash_version` populated from the lookup service,
  - `tracking_enabled` set only when all validation rules from TASK-005 pass,
- calls the shared status service to append the first `Visa Tracking Status Log` row,
- updates the Lead/CRM Lead `custom_visa_tracking_application` Link,
- returns the `Visa Tracking Application` name.

3.2. If `auto_link_verified_passport` is enabled, also update `custom_passport_extraction` on the Lead/CRM Lead to point to the verified extraction.

3.3. A verified extraction must not create more than one active tracking application for the same passport identity in the first release. Conflicts must be surfaced for internal review rather than silently merged.

### 4. Shared idempotent status service and log

4.1. Implement `visa_tracking.services.status_service.update_tracking_status(tracking_application, new_status, source_doctype=None, source_document=None, public_message=None, changed_by=None, change_reason=None, effective_on=None, visible_to_client=True, **idempotency_context)` that:

- loads the tracking application and the requested `Visa Tracking Status` (by Link name or `status_code`),
- validates the status is `active`,
- compares the new status to `current_status`; if identical and the public message/effective timestamp are materially unchanged, performs no write and returns the existing log row (idempotency),
- atomically updates `current_status`, `current_public_message`, and `status_updated_on` on `Visa Tracking Application`,
- appends exactly one `Visa Tracking Status Log` row with:
  - `previous_status`,
  - `new_status`,
  - `public_message` (snapshot; falls back to status default),
  - `effective_on`,
  - `visible_to_client`,
  - `source_doctype` and `source_document`,
  - `changed_by`,
  - `change_reason`,
  - `correction_of` when provided,
- returns the log row name and a boolean indicating whether a change occurred.

4.2. Expose `visa_tracking.services.status_service.append_status_log(...)` as the canonical internal seam used by all lifecycle callers.

4.3. Ensure the service is safe to call from Frappe event handlers, queue jobs, and reconciliation reports; it must never recurse into itself.

4.4. Implement `visa_tracking.services.status_service.get_public_timeline(tracking_application, limit=None)` that returns visible log rows newest-first, honoring `Visa Tracker Settings.status_history_limit` when `limit` is not supplied.

### 5. PF Process File lifecycle synchronization

5.1. Implement `visa_tracking.services.lifecycle_service.link_process_file_to_tracking(pf_process_file_name)` that:

- loads the `PF Process File`,
- resolves the source Lead/CRM Lead via `custom_reference_type` / `custom_reference_name`,
- finds the related `Visa Tracking Application` through the Lead/CRM Lead `custom_visa_tracking_application` Link or, if absent, through matching `file_collection`,
- sets `PF Process File.custom_visa_tracking_application` to the tracking application,
- sets `Visa Tracking Application.process_file` to the PF Process File,
- if `Visa Tracker Settings.enable_process_file_created_transition` is checked, calls `update_tracking_status` with `process_file_created_status` and source `PF Process File`,
- sets `PF Process File.custom_client_status` to the resulting canonical `current_status` without triggering a recursive update.

5.2. Register a `PF Process File` `on_update` handler in `the_visaguy/the_visaguy/hooks.py` that observes changes to `custom_client_status` and calls the bidirectional sync logic.

5.3. Implement `visa_tracking.services.lifecycle_service.sync_process_file_client_status(pf_process_file_name, tracking_application=None)` that:

- reads `PF Process File.custom_client_status`,
- calls `update_tracking_status` on the linked tracking application with source `PF Process File`,
- writes the canonical `current_status` back to `PF Process File.custom_client_status` only when the values differ,
- uses a recursion guard (for example a low-level `db_set` with `update_modified=False` and a thread-local skip flag) so that updating `custom_client_status` does not re-trigger `on_update`.

5.4. Implement `visa_tracking.services.lifecycle_service.sync_tracking_status_to_process_file(tracking_application_name)` that:

- reads `Visa Tracking Application.current_status`,
- writes it to `PF Process File.custom_client_status` via the recursion-safe low-level write,
- does not append a log row (the original status change already logged).

5.5. Both directions must converge to the same canonical status and must produce exactly one log entry per effective status change.

### 6. Direct correction from Visa Tracking Application

6.1. Implement `visa_tracking.services.lifecycle_service.correct_tracking_status(tracking_application_name, new_status, change_reason, corrected_by=None, sync_to_process_file=True)` that:

- requires `change_reason` for any correction,
- calls `update_tracking_status` with source `Visa Tracking Application` and `correction_of` set to the previous log row when appropriate,
- if `sync_to_process_file` is True and a Process File is linked, calls `sync_tracking_status_to_process_file` using the recursion-safe write,
- records the correction reason in the status log but never exposes it in public responses.

6.2. Enforce that only users with the `Visa Tracker Manager` or `System Manager` role may perform direct corrections.

### 7. Customer creation handling

7.1. Register a `Customer` `on_update` or `after_insert` handler in `the_visaguy/the_visaguy/hooks.py` that, when a Customer is linked to a Lead that has a tracking application:

- copies `Lead.custom_passport_extraction` to `Customer.custom_passport_extraction`,
- copies `Lead.custom_visa_tracking_application` to `Customer.custom_visa_tracking_application`,
- sets `Visa Tracking Application.customer`,
- does not create a second tracking application,
- does not change the public status solely because a Customer was created.

### 8. Passport extraction verified handler

8.1. Register a handler (or consume the TASK-004 orchestration signal) in `visa_tracking.handlers.passport_extraction_handlers` that runs after a `Passport Extraction` transitions to `Verified`:

- resolves the source Lead/CRM Lead from the extraction's generic `source_doctype`/`source_document` or from the associated FileFlo context,
- calls `link_verified_extraction_to_lead`,
- calls `create_tracking_application` when settings allow,
- never runs OCR or public API logic.

8.2. The handler must be idempotent: repeated delivery of the same verified event must not duplicate tracking applications.

### 9. Report-only reconciliation

9.1. Implement `visa_tracking.services.reconciliation_service.reconcile_missing_extractions()` that:

- scans configured FileFlo passport fields for persisted private files that have no corresponding `Passport Extraction` record,
- reports the list internally; does not automatically enqueue inspection in the first release,
- includes only stable identifiers (FileFlo collection/row/file names), never passport data.

9.2. Implement `visa_tracking.services.reconciliation_service.reconcile_status_mismatches()` that:

- scans linked `PF Process File` / `Visa Tracking Application` pairs where `custom_client_status` differs from `current_status`,
- reports mismatches with both DocType names and status values,
- does not perform automatic repair in the first release.

9.3. Expose both reports as safe-to-call Python functions; scheduler hooks are optional in this task and may be deferred to TASK-010 if the bench scheduler configuration is not yet verified.

### 10. Client script for PF Process File

10.1. Update or extend `the_visaguy/the_visaguy/fixtures/client_scripts.json` so that `PF Process File` hides or disables `custom_client_status` when `custom_visa_tracking_application` is blank.

10.2. The client script must be shipped as a `the_visaguy` fixture; `processflo` source remains unchanged.

### 11. Automated tests

11.1. Tests must use only synthetic records and obviously fake passport data.

11.2. Test that linking a verified extraction sets the correct Links on `Lead`, `CRM Lead`, and `Customer`.

11.3. Test that `create_tracking_application` produces one active record per verified identity and reuses an existing record on duplicate identity.

11.4. Test that `update_tracking_status` is idempotent: calling it twice with the same status produces only one log row.

11.5. Test that changing `PF Process File.custom_client_status` updates `Visa Tracking Application.current_status` and appends exactly one log row.

11.6. Test that a direct correction updates the Process File without recursion and records the correction reason.

11.7. Test that reconciliation reports identify missing extractions and status mismatches without mutating data.

11.8. Do not run tests on site `visaguy`. Use a dedicated test site when available; otherwise mark runtime validation deferred to TASK-010.

## Constraints

- Work only in `/home/shzd/Projects/workspaces/visaguy_workspace` and the `the_visaguy` feature worktree at `/home/shahzad/visa-tracker-worktrees/the_visaguy`.
- Do not modify `processflo` source, branches, or fixtures.
- Do not implement OCR, MRZ parsing, FileFlo queued detection, extraction orchestration, public whitelisted APIs, frontend screens, or scheduler cron registration unless unavoidable.
- Do not add Link fields from `passport_extractor` to Lead, Customer, `PF Process File`, or `Visa Tracking Application`; keep dependency direction per ADR-003.
- Do not import `fileflo` or `processflo` internals for business logic; use Frappe's generic `get_doc`, `db.get_value`, and `frappe.db.sql` with stable DocType names only.
- Do not commit secrets, production data, passport samples, or sensitive raw data.
- Do not run migrations or tests on site `visaguy`.
- Do not push to any Git remote.
- Do not require or run `bench build --app the_visaguy` unless the bench Node runtime issue recorded in TASK-001 is resolved.

## Exclusions

- OCR/MRZ pipeline (TASK-003).
- FileFlo queued detection and matching (TASK-004).
- Public verification and status APIs, HMAC session handling, rate limiting, lockout, and CORS (TASK-007).
- Frontend scaffold, design parity, and public SPA flows (TASK-008 and TASK-009).
- End-to-end verification, migration on `visaguy`, security gate, and rollout (TASK-010).
- Direct changes to `processflo` source or fixtures.
- Automatic repair in reconciliation reports; reports are read-only in this task.
- Runtime verification blocked by the missing `root_password` configuration; defer to TASK-010 or a dedicated test-site unblock.

## Expected changes

- `the_visaguy/the_visaguy/visa_tracking/services/lifecycle_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/status_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py` (if not already completed in TASK-005)
- `the_visaguy/the_visaguy/visa_tracking/services/reconciliation_service.py`
- `the_visaguy/the_visaguy/visa_tracking/handlers/lead_handlers.py`
- `the_visaguy/the_visaguy/visa_tracking/handlers/process_file_handlers.py`
- `the_visaguy/the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py`
- `the_visaguy/the_visaguy/hooks.py` (event handler registration only)
- `the_visaguy/the_visaguy/fixtures/client_scripts.json` (PF Process File hide/disable script)
- `ongoing/visa-tracking-implementation/05e-task-006-implementation.md`

## Validation

### Static validation

- [ ] Each new `.py` service/handler file compiles with `python -m py_compile` in the bench Python environment.
- [ ] `the_visaguy.__file__` resolves inside the feature worktree when the worktree is first on `PYTHONPATH`.
- [ ] No forbidden import from `fileflo`, `processflo`, or `passport_extractor` internals appears in `the_visaguy` source except the allowed public service imports from `passport_extractor`.
- [ ] `processflo` working tree remains dirty only in its pre-existing unrelated file (`processflo/generate_file_collection.py`); no new changes are introduced.
- [ ] `git status --short` in the feature worktree is clean after all changes are committed locally.

### Runtime validation (defer if test site unavailable)

- [ ] A dedicated test site exists and has `the_visaguy` installed.
- [ ] `bench --site <test-site> migrate` succeeds with the new handlers and fixtures.
- [ ] Creating a verified `Passport Extraction` fixture and calling the lifecycle service creates a `Visa Tracking Application` with the configured default Lead status.
- [ ] Updating `PF Process File.custom_client_status` updates `Visa Tracking Application.current_status` and appends exactly one log row.
- [ ] Direct correction from `Visa Tracking Application` updates `PF Process File.custom_client_status` without recursion and records the correction reason.
- [ ] Reconciliation reports identify synthetic mismatches without mutating data.
- [ ] No migration or test runs on site `visaguy`.

### Runtime deferral note

If the bench still lacks a configured `root_password` key or no dedicated test site is available, record runtime validation as deferred to TASK-010. Static validation and local commits are still required for this task.

## Definition of done

- Lifecycle service creates `Visa Tracking Application` records from verified `Passport Extraction` and links them to `Lead`, `CRM Lead`, and `Customer` using TASK-001-evidenced paths.
- Shared status service is idempotent, appends exactly one log per effective change, and supports correction reasons and public timeline queries.
- Bidirectional synchronization between `PF Process File.custom_client_status` and `Visa Tracking Application.current_status` works without recursion and produces exactly one log per effective change.
- Direct correction flow requires a reason, updates the linked Process File safely, and keeps the reason internal.
- Reconciliation reports are read-only and identify missing extractions and status mismatches.
- Client script shipped as a `the_visaguy` fixture hides/disables `custom_client_status` when no tracking application is linked.
- All static validation items pass.
- Changes are committed locally in the feature worktree; no push is performed.
- `processflo` remains read-only and unbranched.
- `visaguy` is not migrated or tested on.
- Implementation evidence is recorded in `ongoing/visa-tracking-implementation/05e-task-006-implementation.md`.
- TASK-006 is ready for TASK-007 to add public verification and status APIs.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Worktree mismatch**: the feature worktree path or branch differs from `/home/shahzad/visa-tracker-worktrees/the_visaguy` / `feat/visa-tracker`.
2. **Generated layout contradiction**: the Frappe v15 generated file layout under the feature worktree differs materially from the expected paths.
3. **Forbidden dependency leak**: implementing the required behavior forces an import or Link field that violates ADR-003 or ADR-004.
4. **Recursion cannot be prevented**: bidirectional synchronization generates recursive `on_update` calls that cannot be safely guarded with Frappe's available APIs.
5. **ProcessFlo modification required**: implementing the lifecycle link cannot be done through `the_visaguy` fixtures and appears to require a `processflo` source change.
6. **Permission denial**: any required repository, bench, or worktree operation is denied by host policy or user approval.
7. **Source evidence mismatch**: the TASK-001-evidenced FileFlo, Lead, or PF Process File paths contradict the actual code and cannot be adapted without a workspace decision.
