---
id: TASK-002
feature: FEAT-001
title: Passport extractor scaffold and DocType
status: in-progress
repository: passport_extractor
owners: []
depends_on:
  - TASK-001
  - ADR-004
expected_files:
  - passport_extractor/passport_extractor/doctype/passport_extraction/__init__.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.json
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py
  - passport_extractor/passport_extractor/role/passport_extractor_user/passport_extractor_user.json
  - passport_extractor/passport_extractor/utils.py
  - passport_extractor/passport_extractor/__init__.py
  - passport_extractor/hooks.py
  - passport_extractor/pyproject.toml
  - passport_extractor/README.md
  - passport_extractor/license.txt
created: 2026-07-21
updated: 2026-07-21
---

# TASK-002: Passport extractor scaffold and DocType

## Objective

Complete the `passport_extractor` app's domain structure and implement only the `Passport Extraction` DocType, controller-level state transition validation, permissions, safe file-reference validation seams, and automated tests for the data model. This task deliberately excludes OCR/MRZ processing, FileFlo orchestration, public APIs, and tracking DocTypes.

## Context

FEAT-001 introduces a reusable `passport_extractor` Frappe app that owns extraction history and reviewed passport values. ADR-004 and `features/ongoing/visa-tracking/01-architecture-and-data-model.md` define the app's boundaries:

- `passport_extractor` owns `Passport Extraction` schema, lifecycle, and raw audit retention.
- `passport_extractor` must not import from or depend on `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, or Visa Tracking Application.
- Only generic source fields (`source_doctype`, `source_document`, `source_field_id`, `source_row`) may record provenance; no Link fields to VisaGuy business DocTypes are permitted.
- Raw OCR text and raw extraction results are private; error messages must not leak passport details or PII.

TASK-001 already scaffolded the app, installed it on site `visaguy`, and created a clean feature worktree at `/home/shahzad/visa-tracker-worktrees/passport_extractor` on branch `feat/visa-tracker` at base SHA `07b8cab40cd4054b39a78f23a271d7201e71baa0`. All implementation for this task must happen in that worktree.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `ongoing/visa-tracking-implementation/04b-task-001-finish-setup.md`
- Feature worktree: `/home/shahzad/visa-tracker-worktrees/passport_extractor`
- Installed-app verification site: `visaguy` on bench `/home/shahzad/bench`
- Dedicated test site: `passport-extractor-test.localhost` (create only when the bench already has a configured database root-password key; never print its value)
- Frappe 15 / Python 3.10 runtime

## Required behaviour

### 1. App domain structure

1.1. The `passport_extractor` module must remain dependency-free relative to `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, and Visa Tracking Application. No import, schema Link, or hardcoded business rule may depend on those apps or DocTypes. The accepted generic `source_doctype`/`source_document` provenance fields may hold those values at runtime without creating a package dependency.

1.2. Create a `passport_extractor` module subpackage and place domain code under `passport_extractor/passport_extractor/`.

1.3. Create the DocType directory `passport_extractor/passport_extractor/doctype/passport_extraction/` with the standard Frappe v15 layout.

1.4. Add a small `passport_extractor/passport_extractor/utils.py` for reusable helper functions used by the controller and tests (for example, transition validation helpers and file-reference checks). Do not place OCR, MRZ, or queue logic here.

### 2. `Passport Extraction` DocType schema

Implement every field group and field from `01-architecture-and-data-model.md` Section 1 (`Passport Extraction`). Do not invent fields beyond those listed.

#### 2.1 Source and provenance

| Field | Type | Required | Notes |
|---|---|---:|---|
| `passport_file` | Attach | Yes | Must refer to a private Frappe file |
| `file_hash` | Data | After load | SHA-256 of bytes; indexed if supported |
| `source_doctype` | Link / DocType | No | Generic source, no required dependency |
| `source_document` | Dynamic Link | No | Uses `source_doctype` |
| `source_field_id` | Data | No | Persisted FileFlo field ID |
| `source_row` | Data | No | Stable FileFlo value-row identifier when available |
| `triggered_by` | Select | Yes | FileFlo Submission, Manual, Retry, API |
| `requested_by` | Link / User | No | Guest/system-safe value where applicable |
| `requested_on` | Datetime | Yes | Set by server |

#### 2.2 Processing

| Field | Type | Notes |
|---|---|---|
| `status` | Select | Queued, Processing, Extracted, Needs Review, Verified, Rejected, Failed, Duplicate, Superseded |
| `processing_started_on` | Datetime | Set when worker claims job |
| `processing_completed_on` | Datetime | Set for terminal OCR result |
| `extraction_engine` | Data | Example: PaddleOCR |
| `engine_version` | Data | Store runtime versions |
| `confidence` | Percent | Defined algorithmically, not guessed |
| `requires_review` | Check | True for low confidence/check failure/conflict |
| `retry_count` | Int | Bounded |
| `last_job_id` | Data | Optional queue trace, no secrets |
| `error_code` | Data | Stable internal code |
| `error_message` | Small Text | Redacted; no OCR text or PII |

#### 2.3 Passport values

| Field | Type | Notes |
|---|---|---|
| `passport_number` | Data | Reviewed value |
| `passport_number_normalized` | Data | Uppercase/stripped canonical form |
| `date_of_birth` | Date | Reviewed value |
| `expiry_date` | Date | Reviewed value |
| `surname` | Data | Reviewed value |
| `given_names` | Data | Reviewed value |
| `nationality` | Data | Reviewed value |
| `issuing_country` | Data | Reviewed value |
| `sex` | Data | Reviewed value |
| `document_type` | Data | Reviewed value |
| `personal_number` | Data | Reviewed value |

#### 2.4 MRZ evidence

| Field | Type | Notes |
|---|---|---|
| `mrz_line_1` | Data | MRZ line 1 |
| `mrz_line_2` | Data | MRZ line 2 |
| `passport_number_check_valid` | Check | |
| `date_of_birth_check_valid` | Check | |
| `expiry_date_check_valid` | Check | |
| `personal_number_check_valid` | Check | |
| `composite_check_valid` | Check | |
| `mrz_valid` | Check | |

#### 2.5 Raw/audit fields

| Field | Type | Notes |
|---|---|---|
| `raw_ocr_text` | Long Text | Private; raw OCR output |
| `raw_extraction_result` | Code / JSON | Private; raw structured result |
| `verified_by` | Link / User | |
| `verified_on` | Datetime | |
| `verification_notes` | Small Text | |
| `duplicate_of` | Link / Passport Extraction | |
| `supersedes` | Link / Passport Extraction | |
| `superseded_by` | Link / Passport Extraction | |

### 3. Lifecycle and state transitions

3.1. The `status` Select options must be exactly: `Queued`, `Processing`, `Extracted`, `Needs Review`, `Verified`, `Rejected`, `Failed`, `Duplicate`, `Superseded`.

3.2. The controller must enforce the following valid transitions server-side. Any transition not listed must raise `frappe.ValidationError`.

```text
Queued -> Processing
Processing -> Extracted
Processing -> Needs Review
Processing -> Failed
Extracted -> Verified
Extracted -> Needs Review
Needs Review -> Verified
Needs Review -> Rejected
Failed -> Queued (manual/bounded retry)
Verified -> Superseded
Extracted -> Duplicate
Needs Review -> Duplicate
```

3.3. `retry_count` may only increase when transitioning from `Failed` to `Queued`. The controller must reject the transition if `retry_count` would exceed a configurable maximum (default 3) recorded on the document or a module constant.

3.4. `processing_started_on` must be set when entering `Processing` if not already set.

3.5. `processing_completed_on` must be set when entering any terminal OCR state (`Extracted`, `Needs Review`, or `Failed`).

3.6. `verified_by` and `verified_on` must be set when entering `Verified` and retained permanently as audit provenance when the record later becomes `Superseded`.

3.7. `superseded_by` must be set when transitioning to `Superseded`; the target record referenced by `superseded_by` must itself be in `Verified` or `Superseded` status.

3.8. `duplicate_of` must be set when transitioning to `Duplicate`; the target record referenced by `duplicate_of` must exist.

3.9. `requires_review` must default to unchecked and may be set automatically by future OCR logic; for this task it must be settable manually only for test coverage and must not be hardcoded to any value.

### 4. Permissions

4.1. No Guest role may have read or write access to `Passport Extraction`.

4.2. Create the app-owned internal role `Passport Extractor User` with permission to create, read, write, and delete `Passport Extraction` records for extraction operations and testing.

4.3. System Manager retains full access.

4.4. Set `raw_ocr_text`, `raw_extraction_result`, `mrz_line_1`, `mrz_line_2`, and `error_message` to permission level 1. Give `Passport Extractor User` both level-0 record permissions and level-1 read/write permissions. System Manager retains full access. No Guest or unrelated role receives either permission level.

### 5. Safe file-reference validation seams

5.1. The controller must provide a `validate_passport_file()` seam that checks whether `passport_file` refers to a private Frappe `File` record. The seam must:

- accept the file URL or `File` name,
- confirm the file exists,
- confirm `is_private == 1`,
- return a clear result object or raise `frappe.ValidationError` for public/missing files,
- not open, read, or hash the file bytes in this task.

5.2. Provide a `compute_file_hash()` seam that accepts a file URL and returns the SHA-256 hex digest. The seam must verify the file is private before hashing. Mark this seam as available for TASK-003; it may raise `NotImplementedError` or return a placeholder if hashing dependencies are missing, but the signature and privacy check must exist.

5.3. On insert, if `passport_file` is provided, call `validate_passport_file()` and store the result. If the file is public or missing, reject the insert.

### 6. Automated tests

6.1. Tests must run only against dedicated site `passport-extractor-test.localhost`, never against active site `visaguy`. Create the test site only if it does not exist and the bench already has a configured database root-password key; do not print or copy the password value. Install `passport_extractor` on that test site before migration/tests.

6.2. Tests must create their own synthetic records and private `File` fixtures dynamically, using obviously fake values. Tests must clean up only the records they create and must not depend on production data or committed passport samples.

6.3. Test every valid and invalid state transition listed in Section 3.2.

6.4. Test that raw OCR/MRZ/error fields are not readable by Guest or by an unprivileged internal test user.

6.5. Test that error messages raised by invalid transitions or public-file validation do not contain passport numbers, MRZ text, or raw OCR content.

6.6. Test that `passport_file` must be private; a public file reference is rejected on insert.

6.7. Test that an unverified record (`Queued`, `Processing`, `Extracted`, `Needs Review`, `Failed`, `Rejected`, `Duplicate`) cannot be treated as verified through an invalid transition.

6.8. Test that `verified_by`/`verified_on` are required and populated on transition to `Verified`.

6.9. Test that retry bounds are enforced for `Failed -> Queued`.

## Constraints

- Work only in `/home/shahzad/visa-tracker-worktrees/passport_extractor`. Do not modify original repository checkouts.
- Do not import from or reference `the_visaguy`, `fileflo`, `processflo`, `erpnext.crm.doctype.lead`, `frappe.core.doctype.user` for business logic, Lead, Customer, or Visa Tracking Application.
- Do not add Link fields to Lead, Customer, FF File Collection, PF Process File, or Visa Tracking Application.
- Do not implement OCR, MRZ parsing, PDF rendering, image preprocessing, queue jobs, FileFlo event handlers, public APIs, or tracking DocTypes.
- Do not trigger or require `bench build --app passport_extractor` or any asset build. The bench Node runtime is below Frappe 15 requirements.
- Do not push to any Git remote.
- Do not commit secrets, production data, passport samples, or sensitive raw data.

## Expected changes

- `passport_extractor/passport_extractor/doctype/passport_extraction/__init__.py`
- `passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.json`
- `passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.py`
- `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py`
- `passport_extractor/passport_extractor/role/passport_extractor_user/passport_extractor_user.json`
- `passport_extractor/passport_extractor/utils.py`
- `passport_extractor/hooks.py` (module/doctype registration only)
- `passport_extractor/passport_extractor/__init__.py` (module export if needed)

The following scaffold files are already present and must remain unchanged unless module registration requires a minimal edit:

- `passport_extractor/pyproject.toml`
- `passport_extractor/README.md`
- `passport_extractor/license.txt`
- `passport_extractor/__init__.py`

## Validation

- [ ] `passport_extraction.json` parses as valid JSON and conforms to Frappe DocType schema (use `json.load` and visual/schema review).
- [ ] `passport_extraction.py` compiles (`python -m py_compile passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.py`).
- [ ] `utils.py` compiles and imports without errors in the bench Python environment.
- [ ] Before migration/tests, `PYTHONPATH=/home/shahzad/visa-tracker-worktrees/passport_extractor` resolves `passport_extractor.__file__` inside the feature worktree; stop if it does not.
- [ ] `passport-extractor-test.localhost` exists as a dedicated test site and has `passport_extractor` installed.
- [ ] With the feature worktree first on `PYTHONPATH`, `bench --site passport-extractor-test.localhost migrate` succeeds.
- [ ] With the same `PYTHONPATH`, `bench --site passport-extractor-test.localhost run-tests --app passport_extractor` passes all tests in `test_passport_extraction.py`.
- [ ] `bench --site visaguy list-apps` still shows the empty installed `passport_extractor` scaffold; do not migrate feature schema on `visaguy` in this task.

## Implementation evidence

- Static implementation commit: `6746d049db93c86d3cce8f35f763aac6b9366192`.
- Corrective invariant-review commit: `2f25c0d52d2bb898c217b61f448705e5eda550c7`.
- Source/static gates passed: 47 non-layout fields, exact statuses, protected-field permission levels, Python compilation, worktree-first imports, forbidden-dependency scan, and clean worktree.
- Runtime migration and integration tests remain blocked because `passport-extractor-test.localhost` cannot be safely created while the bench lacks a configured database `root_password` key. No migration or test was run on `visaguy`.
- Full evidence: `ongoing/visa-tracking-implementation/05b-task-002-implementation.md`.
- [ ] No import from `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, or Visa Tracking Application appears in `passport_extractor` source.
- [ ] `git status --short` in the feature worktree is clean after all changes are committed locally.
- [ ] No asset build command is required or run.

## Definition of done

- `Passport Extraction` DocType exists on dedicated test site `passport-extractor-test.localhost` with all field groups from Section 2; production-like `visaguy` migration remains a rollout responsibility.
- Controller enforces every valid transition from Section 3.2 and rejects invalid transitions.
- Permissions prevent Guest access and restrict raw OCR/MRZ/error fields to privileged roles.
- File-reference validation seams exist and reject public or missing files.
- All automated tests pass.
- Changes are committed locally in the feature worktree; no push is performed.
- TASK-002 is ready for TASK-003 to add OCR/MRZ processing and queue integration.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Generated Frappe layout contradiction**: the actual Frappe v15 generated file layout under the feature worktree differs materially from the expected paths in this task, making the planned DocType location or import paths invalid.
2. **DocType creation failure**: `Passport Extraction` cannot be created through supported Frappe tooling and migration flow on site `visaguy`.
3. **Test-site safety issue**: migration or tests fail in a way that threatens site `visaguy` data or stability.
4. **Missing architecture decision**: an implementation question arises that is not answered by FEAT-001, ADR-004, or `01-architecture-and-data-model.md`.
5. **Dependency leak**: implementing the required behavior forces an import or Link field to a forbidden DocType or app.
6. **Permission denial**: any required repository, bench, or site operation is denied by host policy or user approval.

7. **Test-site isolation unavailable**: the dedicated test site cannot be safely created or used without exposing credentials or modifying active-site data.

## Completion notes

- Ready to start implementation from base SHA `07b8cab40cd4054b39a78f23a271d7201e71baa0` in `/home/shahzad/visa-tracker-worktrees/passport_extractor`.
- TASK-002 depends on TASK-001 and ADR-004.
