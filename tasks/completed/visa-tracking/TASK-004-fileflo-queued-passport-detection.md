---
id: TASK-004
feature: FEAT-001
title: FileFlo queued passport detection
status: completed
repository: fileflo, the_visaguy
worktree: /home/shahzad/visa-tracker-worktrees/fileflo, /home/shahzad/visa-tracker-worktrees/the_visaguy
owners: []
depends_on:
  - TASK-001
  - TASK-002
  - TASK-003
  - TASK-005
  - ADR-003
  - ADR-004
expected_files:
  - fileflo/fileflo/data_collection.py
  - fileflo/fileflo/events.py
  - fileflo/fileflo/hooks.py
  - the_visaguy/the_visaguy/hooks.py
  - the_visaguy/the_visaguy/visa_tracking/jobs.py
  - the_visaguy/the_visaguy/visa_tracking/services/fileflo_inspection_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/extraction_orchestrator.py
  - the_visaguy/the_visaguy/visa_tracking/utils/idempotency.py
  - the_visaguy/the_visaguy/visa_tracking/utils/provenance.py
  - the_visaguy/the_visaguy/visa_tracking/tests/test_fileflo_inspection.py
  - ongoing/visa-tracking-implementation/05c-task-004-implementation.md
created: 2026-07-21
updated: 2026-07-21
---

# TASK-004: FileFlo queued passport detection

## Objective

Wire FileFlo to emit a minimal, generic after-commit post-persistence extension event, and implement the `the_visaguy` queued inspection that detects configured passport fields, resolves the persisted private file and source provenance, idempotently creates `Passport Extraction` requests, and delegates OCR to `passport_extractor`. All heavy or VisaGuy-specific work must run out of the FileFlo submission transaction.

## Context

FEAT-001 splits ownership across repositories per ADR-003 and ADR-004:

- `fileflo` owns generic persistence and must remain unaware of passports, Visa Tracker Settings, or `passport_extractor`.
- `the_visaguy` owns the decision to treat a FileFlo field as a passport and the orchestration that creates and enqueues extraction work.
- `passport_extractor` owns the `Passport Extraction` DocType and the long-running OCR/MRZ pipeline (TASK-003).
- `processflo` is an integration target only and must not be modified.

TASK-001 evidenced the exact integration points:

- FileFlo submission parent DocType: `FF File Collection`.
- File row child table: `FF File Collection File`; stable field-ID property: `field_id`.
- Value row child table: `FF File Collection Data`; stable field-ID property: `field_id`.
- File attachment DocType: `FF Document`; the uploaded file is stored in its `attach` field.
- Persistence path: `fileflo/fileflo/data_collection.py::add_form_data`.
- File Collection-to-Lead join: `FF File Collection.reference_type` / `reference_name` (`Lead` or `CRM Lead`).
- Lead-to-PF Process File path is owned by `visaguy_crm` and is not needed for detection.
- Both ERPNext `Lead` and Frappe CRM `CRM Lead` are source-wired in the deployed flow.

TASK-002 delivered the `Passport Extraction` DocType and safe file-reference seams. TASK-005 delivers `Visa Tracker Settings` with the configured exact passport field IDs. This task wires the two together through FileFlo.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `ongoing/visa-tracking-implementation/04a-task-001-recon-and-setup.md`
- `ongoing/visa-tracking-implementation/04b-task-001-finish-setup.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `tasks/completed/visa-tracking/TASK-003-passport-ocr-and-mrz-pipeline.md`
- `tasks/completed/visa-tracking/TASK-005-tracking-data-model-and-settings.md`
- Feature worktrees:
  - `/home/shahzad/visa-tracker-worktrees/fileflo` on `feat/visa-tracker` at `6683010e89d9209363e6ba3881f4a90a47420bd2`
  - `/home/shahzad/visa-tracker-worktrees/the_visaguy` on `feat/visa-tracker` at `e690b5b1ac897874fb33439fa429e2aee103cc3e`
- Frappe 15 / Python 3.10 runtime

## Scope

### Included

- A generic, reusable after-commit extension event in `fileflo`.
- `the_visaguy` subscription to that event via Frappe hooks.
- A short-queue inspection worker in `the_visaguy`.
- Exact-match comparison of configured `Visa Tracker Settings.passport_field_ids` against FileFlo `field_id` values.
- Resolution of `FF Document` -> private Frappe `File` and source provenance.
- Idempotent creation of `Passport Extraction` records in `Queued` status.
- Delegation of OCR to `passport_extractor.jobs.run_passport_extraction` on the configured long queue.
- Bounded inspection retries and an active reconciliation job for missed FileFlo uploads.
- Automated static tests with synthetic records.

### Excluded

- OCR, MRZ parsing, PDF rendering, image preprocessing, and check-digit validation (TASK-003).
- `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`, custom fields, and fixtures (TASK-005).
- Lead/Customer/PF Process File lifecycle orchestration, verified-extraction linking, status synchronization, and read-only reconciliation reports (TASK-006).
- Public verification/status APIs, HMAC sessions, rate limiting, and CORS (TASK-007).
- Frontend work (TASK-008 and TASK-009).
- End-to-end runtime verification, migration on `visaguy`, security gate, and rollout (TASK-010).
- Any source change, branch, commit, or fixture in `processflo`.
- Runtime verification if a dedicated isolated test site is unavailable; in that case it is deferred to TASK-010.

## Required behaviour

### 1. FileFlo generic after-commit post-persistence extension event

1.1. Modify `fileflo/fileflo/data_collection.py::add_form_data` (or the equivalent persistence path evidenced in TASK-001) so that, after `FF File Collection`, `FF File Collection File`, `FF File Collection Data`, and `FF Document` records are persisted, it emits a generic extension event using `frappe.enqueue(..., enqueue_after_commit=True)`.

1.2. The event payload must contain only stable identifiers. It must not contain raw file bytes, passport numbers, dates of birth, MRZ text, or any PII.

Required payload shape:

```python
{
    "ff_file_collection": "<FF File Collection name>",
    "reference_type": "<DocType, e.g. Lead or CRM Lead>",
    "reference_name": "<document name>",
    "file_rows": [
        {
            "row_doctype": "FF File Collection File",
            "row_name": "<child row name>",
            "field_id": "<field_id value>",
            "ff_document": "<FF Document name>",
        }
    ],
    "information_rows": [
        {
            "row_doctype": "FF File Collection Data",
            "row_name": "<child row name>",
            "field_id": "<field_id value>",
        }
    ],
}
```

1.3. The event must be dispatched through a configurable hook list defined in `fileflo/fileflo/hooks.py`, for example `fileflo_extension_handlers`. `fileflo` must call `frappe.get_hooks("fileflo_extension_handlers")` and enqueue each handler with the payload. If no handlers are registered, the event is silently dropped.

1.4. `fileflo` must not import from or reference `the_visaguy`, `passport_extractor`, `processflo`, Lead, Customer, `Visa Tracking Application`, or `Visa Tracker Settings`.

1.5. The synchronous FileFlo request path must perform no settings reads, field-ID comparisons, file validation, hash computation, OCR, Lead/Customer resolution, or tracking-record creation. It must only receive stable identifiers and enqueue the extension event.

### 2. `the_visaguy` subscriber

2.1. Register a subscriber function in `the_visaguy/the_visaguy/hooks.py` under the same `fileflo_extension_handlers` hook key, for example `the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection`.

2.2. The subscriber must accept the payload and immediately enqueue a short-queue inspection job:

```python
frappe.enqueue(
    "the_visaguy.visa_tracking.jobs.inspect_fileflo_collection",
    queue=settings.inspection_queue if settings else "short",
    ff_file_collection_name=payload["ff_file_collection"],
    enqueue_after_commit=True,
)
```

2.3. The subscriber must not load `Visa Tracker Settings`, compare field IDs, open files, or perform any other business logic. It must tolerate a missing or disabled settings document gracefully.

### 3. Inspection worker

3.1. Implement `the_visaguy.visa_tracking.jobs.inspect_fileflo_collection(ff_file_collection_name, retry_count=0)` as the short-queue entry point.

3.2. Load `FF File Collection` by name. If it does not exist, treat as a transient failure and retry according to Section 5.

3.3. Load cached `Visa Tracker Settings` via `visa_tracking.utils.settings.get_visa_tracker_settings()`. Stop silently if any of the following are true:

- `enabled` is unchecked.
- `enable_passport_extraction` is unchecked.
- `passport_field_ids` is blank.

3.4. Build a set of configured passport field IDs from `passport_field_ids` (one exact ID per line, stripped, blank lines ignored). Matching must be exact; no wildcards or substring matching.

3.5. Iterate `FF File Collection.file_collection_file` rows. For each row whose `field_id` is in the configured set:

1. Resolve `FF File Collection File.document` -> `FF Document`.
2. Read `FF Document.attach` to obtain the Frappe `File` URL or name.
3. Load the `File` record and confirm it exists and `is_private == 1`.
4. If the File exists and is private, leave supported-extension and size validation to the TASK-003 worker after a valid `Queued` extraction starts.
5. If the File is public or missing, record/log only a stable redacted inspection outcome, create no `Passport Extraction`, and enqueue no OCR work.

3.6. Compute source provenance for the candidate extraction:

- `source_doctype` = `"FF File Collection"`
- `source_document` = `FF File Collection.name`
- `source_field_id` = `FF File Collection File.field_id`
- `source_row` = `FF File Collection File.name`

Do not store `reference_type`/`reference_name` or Lead/Customer identifiers on `Passport Extraction`; those remain in `the_visaguy` orchestration context for TASK-006.

3.7. Compute an idempotency key from `source_doctype`, `source_document`, `source_field_id`, `source_row`, and the stable file identifier (Frappe `File` name or URL). The helper lives in `visa_tracking.utils.idempotency`.

3.8. Query existing `Passport Extraction` records matching the same source fields and file identifier, ordered newest first. Behaviour:

- If an existing record exists with status not in `("Failed", "Duplicate", "Superseded")`, reuse it. Update `last_job_id` only if a new OCR job is enqueued. Do not create a duplicate.
- If the newest existing record is `Failed`, do **not** auto-retry merely because another FileFlo event arrived. Auto-retry is only triggered by the explicit retry/reconciliation path.
- If the file identifier changed (genuine replacement), create a new `Passport Extraction` record. The older record remains in the audit history; supersession is handled by TASK-006 when needed.

3.9. If no reusable record exists, create a `Passport Extraction` document with:

- `status` = `Queued`
- `triggered_by` = `FileFlo Submission`
- `passport_file` = the resolved private Frappe `File` reference
- `source_doctype`, `source_document`, `source_field_id`, `source_row` from Section 3.6
- `requested_by` = current user if available, otherwise a guest/system-safe value
- `requested_on` = current server datetime

Use `passport_extractor` public service seams where available (e.g., `passport_extractor.utils.validate_passport_file`) for consistency, but keep the call lightweight and do not open file bytes.

3.10. Enqueue the long-running extraction worker:

```python
job = frappe.enqueue(
    "passport_extractor.jobs.run_passport_extraction",
    queue=settings.extraction_queue or "long",
    passport_extraction_name=pex.name,
    enqueue_after_commit=True,
)
pex.db_set("last_job_id", job.id)
```

3.11. If no configured passport fields are present, the worker must complete without creating any extraction record and without raising an error.

### 4. Deduplication and idempotency

4.1. Implement `visa_tracking.utils.idempotency.compute_extraction_idempotency_key(source_doctype, source_document, source_field_id, source_row, file_identifier)` that returns a deterministic, opaque string (e.g., SHA-256 hex of sorted, delimited inputs).

4.2. Implement `visa_tracking.utils.idempotency.find_existing_extraction(source_doctype, source_document, source_field_id, source_row, file_identifier)` that returns the newest matching `Passport Extraction` or `None`.

4.3. Repeated delivery of the same FileFlo event for the same source row and same file must return or update the existing extraction, never create a duplicate.

4.4. A genuinely replaced file (different Frappe `File` reference for the same FileFlo row) must create a new extraction record. The old record is left unchanged; supersession logic belongs to TASK-006.

4.5. Verified duplicate passport identities are detected later by TASK-006; this task must not implement duplicate-identity review logic.

### 5. Retries

5.1. Transient inspection failures (missing collection, settings load failure, database lock) must be retried up to `Visa Tracker Settings.inspection_retry_limit` (default 3).

5.2. Pass `retry_count` as a job argument. On transient failure, if `retry_count < limit`, re-enqueue `inspect_fileflo_collection` with `retry_count + 1` and an exponential backoff delay. If the limit is exceeded, log a redacted error message and stop.

5.3. OCR extraction retry is delegated to `passport_extractor.services.extraction_service.retry_extraction` (TASK-003) and is bounded by `Visa Tracker Settings.extraction_retry_limit`. The inspection worker must not directly manipulate `Passport Extraction.retry_count`.

### 6. Reconciliation

6.1. Implement `the_visaguy.visa_tracking.jobs.enqueue_missing_fileflo_extractions()` as an active backfill seam (scheduler registration is optional and may be deferred to TASK-010).

6.2. The reconciliation job must:

- Load `Visa Tracker Settings` and stop if disabled.
- Build the configured passport field ID set.
- Scan `FF File Collection` rows whose child `FF File Collection File` rows have a matching `field_id`.
- For each matching row, check whether a non-failed `Passport Extraction` exists for the same source and file identifier.
- For missing or `Failed` records older than a configurable threshold, enqueue `inspect_fileflo_collection`.
- Deduplicate enqueued jobs using the idempotency key so the same source is not inspected multiple times in parallel.
- Never modify `processflo`, `fileflo`, Lead, Customer, or `PF Process File` records.

6.3. TASK-006 supplies a separate read-only reconciliation report; this task owns the active backfill enqueue path only.

### 7. Source-provenance helpers

7.1. Implement `visa_tracking.utils.provenance.resolve_fileflo_file(ff_file_collection_file_name)` that returns a result object containing:

- `ff_document_name`
- `file_name` (Frappe `File` name)
- `file_url`
- `is_private` boolean
- `exists` boolean
- stable error code if resolution fails

7.2. The helper must use only Frappe generic APIs (`frappe.get_doc`, `frappe.db.get_value`) with DocType names as strings. It must not import from `fileflo`.

### 8. Automated tests

8.1. Tests must run only against a dedicated test site, never `visaguy`. If no test site is available, write the tests and defer execution to TASK-010.

8.2. Tests must create synthetic `FF File Collection`, `FF File Collection File`, `FF Document`, and private `File` fixtures dynamically, using obviously fake data. They must clean up only the records they create.

8.3. Required test coverage:

- `fileflo` emits the generic after-commit event with the expected payload shape and `enqueue_after_commit=True`.
- `fileflo` source contains no forbidden imports (`the_visaguy`, `passport_extractor`, `processflo`, Lead, Customer, etc.).
- The `the_visaguy` subscriber enqueues the inspection job on the configured short queue.
- Inspection stops when `Visa Tracker Settings.enabled` or `enable_passport_extraction` is unchecked.
- Inspection skips rows whose `field_id` is not in `passport_field_ids`.
- Inspection creates exactly one `Queued` `Passport Extraction` for a configured private file row.
- Source provenance fields (`source_doctype`, `source_document`, `source_field_id`, `source_row`) are populated correctly.
- A public or missing file reference creates no extraction, emits only a stable redacted inspection outcome, and enqueues no OCR.
- An unsupported extension or oversized file results in a `Failed` extraction with the appropriate redacted error code.
- Repeated identical FileFlo events create only one `Passport Extraction`.
- A changed file for the same FileFlo row creates a new `Passport Extraction`.
- Transient failure retries are bounded by `inspection_retry_limit`.
- Reconciliation enqueues inspection only for missing/failed records and does not mutate FileFlo or ProcessFlo records.

8.4. All tests must verify that error messages and logs contain no passport numbers, dates of birth, MRZ text, file paths, or raw file bytes.

## Constraints

- Work only in `/home/shahzad/visa-tracker-worktrees/fileflo` and `/home/shahzad/visa-tracker-worktrees/the_visaguy`. Do not modify original repository checkouts.
- Do not create a branch, commit, edit, stash, reset, or clean in `processflo`. `processflo` remains read-only.
- `fileflo` must not import from or depend on `the_visaguy`, `passport_extractor`, `processflo`, Lead, Customer, `Visa Tracking Application`, or `Visa Tracker Settings`.
- `the_visaguy` may import only the public service API of `passport_extractor` (allowed by ADR-003); it must not import `fileflo` or `processflo` internals. Use Frappe generic APIs with DocType names as strings.
- Do not compute file hashes, open file bytes, import PaddleOCR/PyMuPDF/OpenCV, or parse MRZ in the FileFlo request path or the inspection worker.
- Do not create `Visa Tracking Application`, update Lead/Customer Links, or implement status synchronization; those belong to TASK-006.
- Do not expose `Passport Extraction` records, raw OCR data, MRZ lines, or file URLs to Guest or public APIs.
- Do not run migrations, tests, or `bench build` on site `visaguy`.
- Do not push to any Git remote.
- Do not commit secrets, production data, passport samples, raw file bytes, or PII.

## Expected changes

- `fileflo/fileflo/data_collection.py` — trigger the generic after-commit event.
- `fileflo/fileflo/events.py` — generic dispatcher that iterates `fileflo_extension_handlers` and enqueues subscribers.
- `fileflo/fileflo/hooks.py` — declare the `fileflo_extension_handlers` hook list.
- `the_visaguy/the_visaguy/hooks.py` — register the `the_visaguy` subscriber under `fileflo_extension_handlers`.
- `the_visaguy/the_visaguy/visa_tracking/jobs.py` — `enqueue_fileflo_inspection`, `inspect_fileflo_collection`, and `enqueue_missing_fileflo_extractions`.
- `the_visaguy/the_visaguy/visa_tracking/services/fileflo_inspection_service.py` — inspection logic, settings checks, field-ID matching, and source resolution.
- `the_visaguy/the_visaguy/visa_tracking/services/extraction_orchestrator.py` — idempotent `Passport Extraction` creation and OCR enqueueing.
- `the_visaguy/the_visaguy/visa_tracking/utils/idempotency.py` — idempotency key and lookup helpers.
- `the_visaguy/the_visaguy/visa_tracking/utils/provenance.py` — FileFlo file-resolution helpers.
- `the_visaguy/the_visaguy/visa_tracking/tests/test_fileflo_inspection.py` — automated tests.
- `ongoing/visa-tracking-implementation/05c-task-004-implementation.md` — implementation evidence and validation notes.

## Validation

### Static validation

- [ ] Each new `.py` file compiles with `python -m py_compile` in the bench Python environment.
- [ ] Each modified `.py` file still compiles after edits.
- [ ] `fileflo.__file__` resolves inside `/home/shahzad/visa-tracker-worktrees/fileflo` when that worktree is first on `PYTHONPATH`.
- [ ] `the_visaguy.__file__` resolves inside `/home/shahzad/visa-tracker-worktrees/the_visaguy` when that worktree is first on `PYTHONPATH`.
- [ ] No forbidden import from `the_visaguy`, `passport_extractor`, `processflo`, Lead, Customer, `Visa Tracking Application`, or `Visa Tracker Settings` appears in `fileflo` source.
- [ ] No forbidden import from `fileflo` or `processflo` internals appears in `the_visaguy` source, except the allowed public service imports from `passport_extractor`.
- [ ] `processflo` working tree remains dirty only in its pre-existing unrelated file (`processflo/generate_file_collection.py`); no new changes are introduced.
- [ ] `git status --short` in both feature worktrees is clean after all changes are committed locally.
- [ ] `git diff --check` passes in both worktrees.

### Runtime validation

- [ ] A dedicated test site exists and has `the_visaguy`, `fileflo`, and `passport_extractor` installed.
- [ ] `bench --site <test-site> migrate` succeeds with the new hooks and code.
- [ ] Submitting a synthetic FileFlo collection with a configured passport field creates exactly one `Passport Extraction` in `Queued` status and enqueues one `passport_extractor.jobs.run_passport_extraction` job.
- [ ] Submitting a synthetic FileFlo collection with a non-configured field creates no `Passport Extraction`.
- [ ] Repeated delivery of the same FileFlo event does not create duplicate `Passport Extraction` records.
- [ ] A public or missing file reference creates no extraction and does not enqueue OCR.
- [ ] A missing or disabled `Visa Tracker Settings` document causes the inspection worker to stop without error.
- [ ] The reconciliation job enqueues inspection only for missing/failed records and does not mutate FileFlo or ProcessFlo data.
- [ ] No migration, test, or destructive operation runs on site `visaguy`.

### Runtime deferral note

If the bench still lacks a configured `root_password` key or no dedicated test site is available, record runtime validation as deferred to TASK-010. Static validation and local commits are still required for this task.

## Definition of done

- `fileflo` emits a generic after-commit post-persistence extension event with stable identifiers only, and has no VisaGuy dependency.
- `the_visaguy` subscribes to the event and enqueues a short-queue inspection worker.
- The inspection worker loads cached `Visa Tracker Settings`, stops when disabled, and matches FileFlo rows against configured exact `field_id` values.
- For each matching private file, the worker resolves `FF Document` and Frappe `File`, populates generic source provenance, and idempotently creates a `Queued` `Passport Extraction`.
- The worker delegates OCR to `passport_extractor.jobs.run_passport_extraction` on the configured long queue.
- Repeated FileFlo events for the same source and file do not create duplicate extraction records; replaced files create new records.
- Bounded inspection retries and an active FileFlo-extraction reconciliation seam are implemented.
- All static validation items pass and automated tests are written.
- Changes are committed locally in both feature worktrees; no push is performed.
- `processflo` remains read-only and unbranched.
- `visaguy` is not migrated or tested on.
- Implementation evidence is recorded in `ongoing/visa-tracking-implementation/05c-task-004-implementation.md`.
- TASK-004 is ready for TASK-006 to add Lead/Customer/PF Process File lifecycle orchestration.
