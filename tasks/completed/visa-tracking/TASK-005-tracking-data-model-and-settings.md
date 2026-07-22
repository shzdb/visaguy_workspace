---
id: TASK-005
feature: FEAT-001
title: Tracking data model and settings
status: completed
repository: the_visaguy
worktree: /home/shahzad/visa-tracker-worktrees/the_visaguy
owners: []
depends_on:
  - TASK-001
  - TASK-002
  - ADR-003
  - ADR-005
expected_files:
  - the_visaguy/the_visaguy/doctype/visa_tracker_settings/__init__.py
  - the_visaguy/the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.json
  - the_visaguy/the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.py
  - the_visaguy/the_visaguy/doctype/visa_tracker_settings/test_visa_tracker_settings.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status/__init__.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status/visa_tracking_status.json
  - the_visaguy/the_visaguy/doctype/visa_tracking_status/visa_tracking_status.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status/test_visa_tracking_status.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_application/__init__.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_application/visa_tracking_application.json
  - the_visaguy/the_visaguy/doctype/visa_tracking_application/visa_tracking_application.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_application/test_visa_tracking_application.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status_log/__init__.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status_log/visa_tracking_status_log.json
  - the_visaguy/the_visaguy/doctype/visa_tracking_status_log/visa_tracking_status_log.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_status_log/test_visa_tracking_status_log.py
  - the_visaguy/the_visaguy/fixtures/custom_fields.json
  - the_visaguy/the_visaguy/fixtures/property_setters.json
  - the_visaguy/the_visaguy/fixtures/client_scripts.json
  - the_visaguy/the_visaguy/fixtures/roles.json
  - the_visaguy/the_visaguy/fixtures/custom_docperm.json
  - the_visaguy/the_visaguy/visa_tracking/utils/constants.py
  - the_visaguy/the_visaguy/visa_tracking/utils/settings.py
  - the_visaguy/the_visaguy/visa_tracking/services/__init__.py
  - the_visaguy/the_visaguy/visa_tracking/services/status_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py
  - the_visaguy/hooks.py
  - the_visaguy/pyproject.toml
  - ongoing/visa-tracking-implementation/05d-task-005-implementation.md
created: 2026-07-21
updated: 2026-07-21
---

# TASK-005: Tracking data model and settings

## Objective

Implement the complete `the_visaguy` data model for FEAT-001 visa tracking: `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`, the initial status fixture records, role and permission fixtures, and the custom fields/customizations on `Lead`, `Customer`, and `PF Process File`. This task owns the schema and configuration surface only; it does not implement OCR, FileFlo orchestration, public APIs, frontend screens, or the lifecycle synchronization service.

## Context

FEAT-001 splits ownership across repositories per ADR-003 and ADR-004:

- `passport_extractor` owns `Passport Extraction` and extraction history.
- `the_visaguy` owns the tracking domain, settings, status model, public API surface, and the Lead/Customer/PF Process File lifecycle hooks.
- `processflo` owns `PF Process File`; this task supplies only `the_visaguy`-owned fixtures that add custom fields to that DocType.
- `fileflo` owns persistence and emits a generic event; no FileFlo schema change belongs here.
- `visa_tracker` owns the public SPA and is not touched in this task.

TASK-001 created a clean feature worktree at `/home/shahzad/visa-tracker-worktrees/the_visaguy` on branch `feat/visa-tracker`. TASK-002 delivered the `Passport Extraction` DocType in `passport_extractor`. This task may assume the `Passport Extraction` schema and its `Verified` status exist, but must not depend on a migrated `passport_extractor` test site because TASK-002 runtime verification is deferred to TASK-010.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `features/ongoing/visa-tracking/02-backend-workflows-and-api-contracts.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `ongoing/visa-tracking-implementation/04b-task-001-finish-setup.md`
- Feature worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`
- Installed Frappe apps on site `visaguy`, including `the_visaguy`
- Frappe 15 / Python 3.10 runtime

## Required behaviour

### 1. Repository and worktree discipline

1.1. Work only in `/home/shahzad/visa-tracker-worktrees/the_visaguy` on branch `feat/visa-tracker`. Do not modify the original `the_visaguy` checkout.

1.2. Do not create a branch or commit in `processflo`. `PF Process File` custom fields are supplied by `the_visaguy` fixtures per ADR-003.

1.3. Do not push to any Git remote.

### 2. `Visa Tracker Settings` Single DocType

Create `the_visaguy/the_visaguy/doctype/visa_tracker_settings/` with the standard Frappe v15 layout. Implement every field from `01-architecture-and-data-model.md` Section 2.

#### 2.1 Feature and extraction settings

| Field | Type | Default/constraint |
|---|---|---|
| `enabled` | Check | Master switch |
| `enable_passport_extraction` | Check | Separate extraction switch |
| `passport_field_ids` | Small Text | One exact ID per line; blank lines ignored |
| `supported_extensions` | Small Text | `pdf`, `jpg`, `jpeg`, `png`; one per line |
| `maximum_file_size_mb` | Int | Must be positive |
| `require_manual_verification` | Check | True for initial production release |
| `inspection_queue` | Select | Short/default according to deployment naming |
| `extraction_queue` | Select | Long |
| `inspection_retry_limit` | Int | Suggested 3 |
| `extraction_retry_limit` | Int | Suggested 2 |

#### 2.2 Lifecycle settings

| Field | Type | Notes |
|---|---|---|
| `default_lead_status` | Link / Visa Tracking Status | Required when tracking enabled |
| `process_file_created_status` | Link / Visa Tracking Status | Required when auto transition enabled |
| `enable_process_file_created_transition` | Check | Controls automatic status change |
| `auto_create_tracking_application` | Check | Initial plan: enabled after verified extraction |
| `auto_link_verified_passport` | Check | Initial plan: enabled after verification |

#### 2.3 Public tracking settings

| Field | Type | Notes |
|---|---|---|
| `enable_public_tracking` | Check | Independent public API switch |
| `frontend_base_url` | Data | Non-secret approved URL |
| `session_expiry_minutes` | Int | Suggested 15; positive and bounded |
| `maximum_failed_attempts` | Int | Suggested 5 |
| `lockout_minutes` | Int | Suggested 15 |
| `status_history_limit` | Int | Suggested 20 |
| `stale_status_days` | Int | Reporting only |

#### 2.4 Validation and caching

- `enabled` must default to unchecked.
- `enable_public_tracking` may only be checked when `enabled` is checked.
- `default_lead_status` is required when `enabled` is checked.
- `process_file_created_status` is required when `enable_process_file_created_transition` is checked.
- `session_expiry_minutes`, `maximum_failed_attempts`, `lockout_minutes`, `status_history_limit`, and `stale_status_days` must be positive and bounded by module constants.
- Provide a cached loader `visa_tracking.utils.settings.get_visa_tracker_settings()` that returns the active settings document or `None` and that respects Frappe's `frappe.cache` pattern.
- Provide `is_tracking_enabled()`, `is_public_tracking_enabled()`, and `is_passport_extraction_enabled()` helpers that read the cached loader.

### 3. `Visa Tracking Status` DocType

Create `the_visaguy/the_visaguy/doctype/visa_tracking_status/` and implement every field from `01-architecture-and-data-model.md` Section 3.

| Field | Type | Constraint |
|---|---|---|
| `status_name` | Data | Unique label |
| `status_code` | Data | Stable, unique, uppercase/slug code |
| `sequence` | Int | Timeline order |
| `default_public_message` | Small Text | No internal detail |
| `active` | Check | Only active values selectable |
| `allow_on_process_file` | Check | Filters operations Link field |
| `is_final` | Check | Terminal state |
| `is_successful` | Check | Reporting only |
| `display_icon` | Data | Frontend-approved identifier, optional |
| `display_colour` | Data | Prefer semantic token over arbitrary hex |

- `status_code` must be uppercase, unique, and auto-normalized to a slug form on save (letters, digits, underscores only).
- `sequence` must be unique or validated to prevent accidental duplicates.
- Provide `get_active_statuses()`, `get_allowed_process_file_statuses()`, and `get_status_by_code(code)` helpers.

### 4. Initial `Visa Tracking Status` records

Seed the six initial statuses from `features/ongoing/visa-tracking/README.md` Section "Required status model" via a fixture file or idempotent installation hook. The exact labels and codes are:

| Sequence | Status name | Suggested code |
|---|---|---|
| 10 | Application Received | APPLICATION_RECEIVED |
| 20 | Documents Under Review | DOCUMENTS_UNDER_REVIEW |
| 30 | Verification in Progress | VERIFICATION_IN_PROGRESS |
| 40 | Working on Your Application | WORKING_ON_APPLICATION |
| 50 | Application Submitted | APPLICATION_SUBMITTED |
| 60 | Update Shared with Client | UPDATE_SHARED_WITH_CLIENT |

All six must be `active = 1`. `Application Received`, `Working on Your Application`, `Application Submitted`, and `Update Shared with Client` should have `allow_on_process_file = 1` initially; the remaining two may be system-managed transitions. Do not hardcode these labels in business logic; code must reference `status_code` or Link values loaded from settings.

### 5. `Visa Tracking Application` DocType

Create `the_visaguy/the_visaguy/doctype/visa_tracking_application/` and implement every field from `01-architecture-and-data-model.md` Section 4.

#### 5.1 References

| Field | Type | Notes |
|---|---|---|
| `passport_extraction` | Link / Passport Extraction | Must be Verified before public enablement |
| `lead` | Link / Lead | Initial lifecycle reference |
| `crm_lead` | Link / CRM Lead | Add only if TASK-001 confirmed deployed need |
| `customer` | Link / Customer | Populated later |
| `process_file` | Link / PF Process File | Initially blank |
| `file_collection` | Link / FF File Collection | Owned here |
| `visa_order_doctype` | Link / DocType | Optional generic reference |
| `visa_order` | Dynamic Link | Optional |

#### 5.2 Public state

| Field | Type | Notes |
|---|---|---|
| `current_status` | Link / Visa Tracking Status | Canonical current public status |
| `current_public_message` | Small Text | Snapshot/override |
| `status_updated_on` | Datetime | Effective status timestamp |
| `tracking_enabled` | Check | Required for public lookup |
| `application_closed` | Check | Excludes from active lookup |
| `applicant_display_name` | Data | Internal full value; API masks it |
| `destination` | Link/Data | Return only if approved |
| `visa_type` | Link/Data | Return only if approved |

#### 5.3 Secure lookup

| Field | Type | Notes |
|---|---|---|
| `verification_lookup_hash` | Data | Indexed HMAC-SHA256 over canonical passport number + DOB |
| `lookup_hash_version` | Data | Supports key/algorithm rotation |

#### 5.4 Validation and naming

- Naming recommendation: `VTA-.YYYY.-.#####`.
- `tracking_enabled` cannot be checked unless `passport_extraction` points to a `Verified` `Passport Extraction`, `current_status` is set and active, and `verification_lookup_hash` is populated.
- `passport_extraction`, `lead`, `customer`, `process_file`, `file_collection`, `visa_order_doctype`, and `visa_order` must be `no_copy`.
- Provide a service seam `visa_tracking.services.lookup_service.compute_lookup_hash(passport_number, date_of_birth)` that returns `(hash, version)`. The function must:
  - canonicalize the passport number and date of birth,
  - read the HMAC key from a server-side configuration key named `visa_tracker_lookup_hmac_key` using `frappe.conf`,
  - use HMAC-SHA256,
  - raise if the key is missing and `raise_on_missing` is True.
- Do not store plain SHA or unsalted hashes. Do not commit the HMAC key value.

### 6. `Visa Tracking Status Log` DocType

Create `the_visaguy/the_visaguy/doctype/visa_tracking_status_log/` and implement every field from `01-architecture-and-data-model.md` Section 5.

| Field | Type | Notes |
|---|---|---|
| `tracking_application` | Link | Required; indexed |
| `previous_status` | Link | Blank for first entry |
| `new_status` | Link | Required |
| `public_message` | Small Text | Snapshot shown for this transition |
| `effective_on` | Datetime | Timeline timestamp |
| `visible_to_client` | Check | Default true for public statuses |
| `source_doctype` | Link / DocType | Lead, PF Process File, Visa Tracking Application, System |
| `source_document` | Dynamic Link | Internal only |
| `changed_by` | Link / User | Server-set |
| `change_reason` | Small Text | Internal correction reason; never public |
| `correction_of` | Link / Visa Tracking Status Log | Optional audit relationship |

- The log must be read-only to ordinary users; no standard delete permission.
- Provide a service seam `visa_tracking.services.status_service.append_status_log(...)` for creating entries. This task only defines the seam signature and DocType; the full lifecycle caller logic is TASK-006.
- Provide `get_public_timeline(tracking_application, limit)` that returns visible log rows newest-first.

### 7. Custom fields shipped by `the_visaguy`

Export all custom fields as `the_visaguy` fixtures. Do not modify `processflo` source.

#### 7.1 Lead

- `custom_passport_extraction`: Link / Passport Extraction, read-only, no-copy.
- `custom_visa_tracking_application`: Link / Visa Tracking Application, read-only, no-copy.

No client-status field is added to Lead.

#### 7.2 Customer

- `custom_passport_extraction`: Link / Passport Extraction, read-only, no-copy.
- `custom_visa_tracking_application`: Link / Visa Tracking Application, read-only, no-copy.

#### 7.3 CRM Lead

Add the same two custom fields only if TASK-001 evidence confirmed that both ERPNext Lead and CRM Lead are active in the deployed flow. If TASK-001 evidence showed CRM Lead is not used, document that explicitly and omit CRM Lead fields.

#### 7.4 PF Process File

- `custom_visa_tracking_application`: Link / Visa Tracking Application, read-only, no-copy.
- `custom_client_status`: Link / Visa Tracking Status.

The Client Status Link query must filter:

```text
active = 1
allow_on_process_file = 1
```

Hide or disable `custom_client_status` when `custom_visa_tracking_application` is blank. This may be implemented through a client script fixture or property setter; server-side validation is optional in this task and will be hardened in TASK-006.

### 8. Roles and permissions

Create fixtures for the following roles:

- `Visa Tracker Manager`: create/read/write/delete on `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, and `Visa Tracking Status Log`.
- `Visa Tracker Operator`: read/write on `Visa Tracking Application`, read on `Visa Tracking Status`, `Visa Tracking Status Log`, and `Visa Tracker Settings`; no delete.
- `System Manager`: full access to all four DocTypes.
- No Guest role may receive read or write access to any of these DocTypes or to `Passport Extraction` through `the_visaguy` permissions.

### 9. App wiring and fixtures

9.1. Register the four new DocTypes and fixtures in `the_visaguy/hooks.py`.

9.2. Ensure `fixtures` exports include:

- `Custom Field`
- `Property Setter`
- `Client Script`
- `Role`
- `Custom DocPerm`
- `Visa Tracking Status` (initial records)

9.3. Provide a module subpackage `the_visaguy/the_visaguy/visa_tracking/` with:

- `utils/constants.py` — module constants (status codes, retry limits, session bounds).
- `utils/settings.py` — cached settings loader and predicate helpers.
- `services/__init__.py`.
- `services/status_service.py` — status log seam and public timeline helper.
- `services/lookup_service.py` — HMAC lookup hash seam.

These service modules may contain minimal scaffolding; full lifecycle logic is TASK-006 and full public API logic is TASK-007.

### 10. Automated tests

10.1. Tests must use only synthetic records and obvious fake passport data.

10.2. Test that `Visa Tracker Settings` validates required fields based on feature toggles.

10.3. Test that `Visa Tracking Status` normalizes codes and enforces uniqueness constraints.

10.4. Test that `Visa Tracking Application` rejects enabling public tracking without a Verified `Passport Extraction` and a populated `verification_lookup_hash`.

10.5. Test that `compute_lookup_hash` returns deterministic, distinct values for distinct inputs and uses HMAC with the configured key.

10.6. Test that `Visa Tracking Status Log` rows are created through the service seam and are not editable by an unprivileged operator test user.

10.7. Test fixture loading idempotency: running the fixture export/import flow twice must not duplicate `Visa Tracking Status` records or custom fields.

10.8. Do not run tests on site `visaguy`. Use a dedicated test site when available; otherwise mark runtime validation deferred to TASK-010.

## Constraints

- Work only in `/home/shzd/Projects/workspaces/visaguy_workspace` and the `the_visaguy` feature worktree at `/home/shahzad/visa-tracker-worktrees/the_visaguy`.
- Do not modify `processflo` source, branches, or fixtures.
- Do not implement OCR, MRZ parsing, FileFlo queued inspection, extraction orchestration, public whitelisted APIs, frontend screens, or the full lifecycle synchronization service.
- Do not add Link fields from `passport_extractor` to Lead, Customer, `PF Process File`, or `Visa Tracking Application`; keep dependency direction per ADR-003.
- Do not import from `fileflo` or `processflo` for business logic.
- Do not commit secrets, production data, passport samples, or sensitive raw data.
- Do not run migrations or tests on site `visaguy`.
- Do not push to any Git remote.
- Do not require or run `bench build --app the_visaguy` unless the bench Node runtime issue recorded in TASK-001 is resolved.

## Exclusions

- OCR/MRZ pipeline (TASK-003).
- FileFlo queued detection and matching (TASK-004).
- Lead/Customer/PF Process File lifecycle orchestration and two-way status sync (TASK-006).
- Public verification and status APIs, HMAC session handling, rate limiting, lockout, and CORS (TASK-007).
- Frontend scaffold, design parity, and public SPA flows (TASK-008 and TASK-009).
- End-to-end verification, migration on `visaguy`, security gate, and rollout (TASK-010).
- Direct changes to `processflo` source or fixtures.
- Runtime verification blocked by the missing `root_password` configuration; defer to TASK-010 or a dedicated test-site unblock.

## Expected changes

- `the_visaguy/the_visaguy/doctype/visa_tracker_settings/`
- `the_visaguy/the_visaguy/doctype/visa_tracking_status/`
- `the_visaguy/the_visaguy/doctype/visa_tracking_application/`
- `the_visaguy/the_visaguy/doctype/visa_tracking_status_log/`
- `the_visaguy/the_visaguy/visa_tracking/utils/constants.py`
- `the_visaguy/the_visaguy/visa_tracking/utils/settings.py`
- `the_visaguy/the_visaguy/visa_tracking/services/status_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py`
- `the_visaguy/the_visaguy/fixtures/custom_fields.json`
- `the_visaguy/the_visaguy/fixtures/property_setters.json`
- `the_visaguy/the_visaguy/fixtures/client_scripts.json`
- `the_visaguy/the_visaguy/fixtures/roles.json`
- `the_visaguy/the_visaguy/fixtures/custom_docperm.json`
- `the_visaguy/the_visaguy/fixtures/visa_tracking_status.json`
- `the_visaguy/hooks.py` (fixture and DocType registration only)
- `ongoing/visa-tracking-implementation/05d-task-005-implementation.md`

## Validation

### Static validation

- [ ] Each `.json` DocType schema parses as valid JSON.
- [ ] Each `.py` controller, service module, and test file compiles with `python -m py_compile` in the bench Python environment.
- [ ] `the_visaguy.__file__` resolves inside the feature worktree when the worktree is first on `PYTHONPATH`.
- [ ] No forbidden import from `fileflo`, `processflo`, or `passport_extractor` internals appears in `the_visaguy` source except the allowed public service imports from `passport_extractor`.
- [ ] No Link field in `passport_extractor` points to Lead, Customer, `PF Process File`, or `Visa Tracking Application`.
- [ ] Fixtures contain only the custom fields, roles, permissions, and initial statuses listed in this task.
- [ ] `git status --short` in the feature worktree is clean after all changes are committed locally.

### Runtime validation (defer if test site unavailable)

- [ ] A dedicated test site exists and has `the_visaguy` installed.
- [ ] `bench --site <test-site> migrate` succeeds with the new DocTypes and fixtures.
- [ ] Initial `Visa Tracking Status` records exist and are active.
- [ ] Custom fields appear on `Lead`, `Customer`, and `PF Process File` after fixture sync.
- [ ] CRM Lead custom fields appear only if TASK-001 confirmed CRM Lead is deployed.
- [ ] All automated tests pass.
- [ ] No migration or test runs on site `visaguy`.

### Runtime deferral note

If the bench still lacks a configured `root_password` key or no dedicated test site is available, record runtime validation as deferred to TASK-010. Static validation and local commits are still required for this task.

## Definition of done

- `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, and `Visa Tracking Status Log` DocTypes exist in the feature worktree with all fields from `01-architecture-and-data-model.md`.
- Initial `Visa Tracking Status` records are fixture-ready and idempotent.
- Roles and permissions fixtures prevent Guest access and grant appropriate internal access.
- Custom fields on `Lead`, `Customer`, and `PF Process File` are exported as `the_visaguy` fixtures; CRM Lead fields are included only if TASK-001 evidence supports it.
- Cached settings loader, HMAC lookup-hash seam, and status-log service seam are implemented and tested statically.
- All static validation items pass.
- Changes are committed locally in the feature worktree; no push is performed.
- `processflo` remains read-only and unbranched.
- `visaguy` is not migrated or tested on.
- Implementation evidence is recorded in `ongoing/visa-tracking-implementation/07b-task-005-implementation.md`.
- TASK-005 is ready for TASK-006 to add lifecycle orchestration and status synchronization.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Worktree mismatch**: the feature worktree path or branch differs from `/home/shahzad/visa-tracker-worktrees/the_visaguy` / `feat/visa-tracker`.
2. **Generated layout contradiction**: the Frappe v15 generated file layout under the feature worktree differs materially from the expected paths.
3. **DocType creation failure**: a tracking DocType cannot be created through supported Frappe tooling.
4. **Forbidden dependency leak**: implementing the required behavior forces an import or Link field that violates ADR-003 or ADR-004.
5. **CRM Lead ambiguity**: TASK-001 evidence is contradictory or missing on whether CRM Lead is active in the deployed flow.
6. **Permission denial**: any required repository, bench, or worktree operation is denied by host policy or user approval.
7. **ProcessFlo modification required**: implementing the `PF Process File` custom fields cannot be done through `the_visaguy` fixtures and appears to require a `processflo` source change.

## Completion notes

- Implemented and committed in `the_visaguy` at `f7ad8c0518a6442cbb33136b84dba524f2909ecd`.
- DocType/fixture JSON, Python compilation, hook registration, permission, secret, dependency, and worktree-cleanliness gates passed.
- Dedicated-site migration and Frappe integration tests are intentionally deferred to TASK-010; `visaguy` was not migrated or tested.
- Evidence: `ongoing/visa-tracking-implementation/07b-task-005-implementation.md`.
