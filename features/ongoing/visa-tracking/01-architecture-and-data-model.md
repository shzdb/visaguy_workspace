# Visa tracking architecture and data model

## Purpose

This document defines repository ownership, data ownership, record relationships, lifecycle rules, queues, and idempotency for FEAT-001. It is authoritative for implementation intent. Application repositories remain authoritative for code and generated DocType schemas.

## System boundary

```text
                         Public internet
                               |
                               v
                    visa_tracker React SPA
                               |
             purpose-built guest API methods only
                               |
                               v
+------------------------------------------------------------------+
|                         the_visaguy                               |
| Visa Tracker Settings | Tracking Application | Status | Status Log|
| FileFlo inspection jobs | lifecycle services | public API/security|
+------------------------------------------------------------------+
           |                      |                       |
           | generic event        | extraction API        | custom fields
           v                      v                       v
       fileflo             passport_extractor       Lead / Customer /
  persists field data      Passport Extraction      PF Process File
                                |
                                v
                    PaddleOCR + MRZ validation
```

## Dependency direction

Allowed:

```text
fileflo -> emits generic event

the_visaguy -> imports passport_extractor public service

the_visaguy -> observes FileFlo and PF Process File events

visa_tracker -> calls the_visaguy public APIs
```

Forbidden:

```text
passport_extractor -> the_visaguy
passport_extractor -> fileflo
passport_extractor -> processflo
fileflo -> passport_extractor
fileflo -> Visa Tracker Settings
visa_tracker -> /api/resource/* tracking or extraction DocTypes
visa_tracker -> FileFlo, ProcessFlo, Lead, Customer APIs
```

## Repository responsibility matrix

### `fileflo`

Owns:

- persistence of submitted form values,
- persistence/linking of uploaded `File` records,
- a generic, reusable after-field-persisted extension event.

Does not own:

- knowledge that a field is a passport,
- Visa Tracker Settings,
- extraction creation,
- OCR,
- tracking records,
- Lead/Customer linking.

The FileFlo change must be deliberately small and generic. The event payload contains stable identifiers, not raw file bytes or passport data.

### `passport_extractor`

Owns:

- `Passport Extraction`,
- file loading and format validation,
- file hashing,
- PDF rendering,
- image preprocessing,
- OCR invocation,
- TD3 MRZ parsing,
- check-digit validation,
- raw result retention,
- extraction lifecycle, retries, review, duplicate/supersession metadata,
- a small reusable Python service API.

Does not own:

- when VisaGuy considers a FileFlo field to be a passport,
- Lead, Customer, FileFlo, ProcessFlo, or tracking references beyond generic source fields,
- public tracking authentication,
- status lifecycle.

### `the_visaguy`

Owns:

- `Visa Tracker Settings`,
- configured passport field IDs,
- FileFlo queued inspection,
- extraction orchestration,
- source-context resolution,
- preferred extraction Links on business records,
- `Visa Tracking Application`, `Visa Tracking Status`, and `Visa Tracking Status Log`,
- Lead/Customer/PF Process File lifecycle,
- custom fields and client scripts shipped as fixtures,
- public verification and status APIs,
- abuse controls and audit events,
- reconciliation jobs and reports.

### `processflo`

Owns the base `PF Process File` DocType and process workflow. The planned custom fields, queries, and event handlers are supplied by `the_visaguy`. No source change is planned in `processflo`.

### `visa_tracker`

Owns the public SPA only. It has no business database and no long-lived authentication credentials.

## Data model

## 1. Passport Extraction

Location: `passport_extractor`.

Naming recommendation: `PEX-.YYYY.-.#####` or the app's standard naming convention.

### Source and provenance

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

Do not add Link fields to Lead, Customer, FF File Collection, or Visa Tracking Application in this generic app.

### Processing

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

### Passport values

Reviewed record fields:

- `passport_number`
- `passport_number_normalized`
- `date_of_birth`
- `expiry_date`
- `surname`
- `given_names`
- `nationality`
- `issuing_country`
- `sex`
- `document_type`
- `personal_number`

MRZ evidence fields:

- `mrz_line_1`
- `mrz_line_2`
- `passport_number_check_valid`
- `date_of_birth_check_valid`
- `expiry_date_check_valid`
- `personal_number_check_valid`
- `composite_check_valid`
- `mrz_valid`

Raw/audit fields:

- `raw_ocr_text` as private Long Text,
- `raw_extraction_result` as Code/JSON,
- `verified_by`,
- `verified_on`,
- `verification_notes`,
- `duplicate_of`,
- `supersedes`,
- `superseded_by`.

The normal passport fields contain the current reviewed values. Raw machine output remains in `raw_extraction_result` so corrections do not destroy provenance.

### Status transitions

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
Extracted/Needs Review -> Duplicate
```

Invalid transitions must be rejected server-side.

## 2. Visa Tracker Settings

Location: `the_visaguy`; Single DocType.

### Feature and extraction settings

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

### Lifecycle settings

| Field | Type | Notes |
|---|---|---|
| `default_lead_status` | Link / Visa Tracking Status | Required when tracking enabled |
| `process_file_created_status` | Link / Visa Tracking Status | Required when auto transition enabled |
| `enable_process_file_created_transition` | Check | Controls automatic status change |
| `auto_create_tracking_application` | Check | Initial plan: enabled after verified extraction |
| `auto_link_verified_passport` | Check | Initial plan: enabled after verification |

### Public tracking settings

| Field | Type | Notes |
|---|---|---|
| `enable_public_tracking` | Check | Independent public API switch |
| `frontend_base_url` | Data | Non-secret approved URL |
| `session_expiry_minutes` | Int | Suggested 15; positive and bounded |
| `maximum_failed_attempts` | Int | Suggested 5 |
| `lockout_minutes` | Int | Suggested 15 |
| `status_history_limit` | Int | Suggested 20 |
| `stale_status_days` | Int | Reporting only |

Secrets such as HMAC keys do not belong in this DocType. Record only the configuration key name in documentation.

## 3. Visa Tracking Status

Location: `the_visaguy`.

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

Statuses should be seeded through fixtures or installation logic and remain configurable.

## 4. Visa Tracking Application

Location: `the_visaguy`.

One record represents one client-trackable visa case.

### References

| Field | Type | Notes |
|---|---|---|
| `passport_extraction` | Link / Passport Extraction | Must be Verified before public enablement |
| `lead` | Link / Lead | Initial lifecycle reference |
| `crm_lead` | Link / CRM Lead | Add only if TASK-001 confirms deployed need |
| `customer` | Link / Customer | Populated later |
| `process_file` | Link / PF Process File | Initially blank |
| `file_collection` | Link / FF File Collection | Owned here because `the_visaguy` already depends on business context |
| `visa_order_doctype` | Link / DocType | Optional generic reference |
| `visa_order` | Dynamic Link | Optional |

### Public state

| Field | Type | Notes |
|---|---|---|
| `current_status` | Link / Visa Tracking Status | Canonical current public status |
| `current_public_message` | Small Text | Snapshot/override; no internal text |
| `status_updated_on` | Datetime | Effective status timestamp |
| `tracking_enabled` | Check | Required for public lookup |
| `application_closed` | Check | Excludes from active lookup as configured |
| `applicant_display_name` | Data | Internal full value; API masks it |
| `destination` | Link/Data | Return only if approved |
| `visa_type` | Link/Data | Return only if approved |

### Secure lookup

| Field | Type | Notes |
|---|---|---|
| `verification_lookup_hash` | Data | Indexed HMAC-SHA256 over canonical passport number + DOB |
| `lookup_hash_version` | Data | Supports key/algorithm rotation |

Do not store a plain SHA hash of passport+DOB. Those values have limited entropy and can be guessed offline. The HMAC key is server-side configuration, for example `visa_tracker_lookup_hmac_key`; never commit its value.

### Validation rules

- Public tracking cannot be enabled without a Verified Passport Extraction.
- Public tracking cannot be enabled without a current active status.
- Initial release permits one active tracking record for a passport identity. A conflict is flagged for review rather than silently choosing one.
- `verification_lookup_hash` is recomputed only through the domain service when the verified identity changes.
- Direct API writes to this DocType are not exposed to Guest.

## 5. Visa Tracking Status Log

Location: `the_visaguy`.

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

The log is append-only through the domain service. Do not edit or delete history to correct it. Add a correction record and adjust visibility when necessary.

## Custom fields shipped by `the_visaguy`

### Lead

- `custom_passport_extraction`: Link to Passport Extraction, read-only, no-copy.
- `custom_visa_tracking_application`: Link to Visa Tracking Application, read-only, no-copy.

No client-status field is added to Lead.

### Customer

- `custom_passport_extraction`: Link, read-only, no-copy.
- `custom_visa_tracking_application`: Link, read-only, no-copy.

### PF Process File

- `custom_visa_tracking_application`: Link, read-only, no-copy.
- `custom_client_status`: Link to Visa Tracking Status.

The Client Status query filters:

```text
active = 1
allow_on_process_file = 1
```

Hide or disable Client Status when no tracking application is linked.

## Lifecycle state machine

## Stage A: FileFlo and Lead only

Preconditions:

- a FileFlo passport field has been submitted,
- context resolves to a Lead,
- extraction is Verified.

Actions:

1. Link preferred extraction to Lead.
2. Create one Visa Tracking Application if none exists.
3. Set Lead Link to the tracking application.
4. Set current status from `default_lead_status`.
5. Create first status log.
6. Calculate secure lookup hash.
7. Enable tracking only when validation passes.

## Stage B: Customer created

Actions:

1. Copy preferred extraction Link to Customer.
2. Copy tracking application Link to Customer.
3. Set `Visa Tracking Application.customer`.
4. Do not create a second tracking application.
5. Do not change public status merely because Customer was created.

## Stage C: PF Process File created or linked

Actions:

1. Resolve the source Lead/tracking application.
2. Link `PF Process File.custom_visa_tracking_application`.
3. Set `Visa Tracking Application.process_file`.
4. If enabled, apply `process_file_created_status` through the shared status service.
5. Set `PF Process File.custom_client_status` to the resulting canonical status.
6. Create one status log only if the effective status changed.

## Stage D: Operations updates Client Status

Actions:

1. Validate active/allowed status.
2. Call shared `update_tracking_status` service.
3. Update canonical current status/message/timestamp.
4. Append one log.
5. Keep PF Process File field aligned.
6. Never run OCR or public notification in this transaction.

## Stage E: Exceptional direct correction

An authorized internal user may update from Visa Tracking Application. The same service:

- requires a correction reason where appropriate,
- updates PF Process File using a recursion-safe low-level write or flag,
- appends an auditable log,
- does not rewrite prior rows.

## Idempotency

### FileFlo event key

Preferred identity:

```text
source_doctype + source_document/source_row + source_field_id + persisted file identity/version
```

Use file hash as a secondary deduplication signal, not as the only source relationship.

Required behavior:

- repeated delivery of the same event returns/reuses the existing extraction,
- a genuinely replaced file creates a new extraction,
- a prior Failed record may be retried explicitly without creating infinite duplicates,
- verified duplicate passport identities are flagged for review.

### Status idempotency

The shared status service must compare:

- tracking application,
- new status,
- public message,
- effective timestamp semantics,
- source event identity where available.

A normal save with unchanged status creates no log.

## Reconciliation

Two scheduled/reporting checks are required:

1. Configured FileFlo passport uploads with no extraction record.
2. Linked PF Process File and Visa Tracking Application records whose current statuses differ.

The first may safely enqueue inspection after deduplication. The second should report mismatches first; automatic repair is not enabled until production behavior is understood.

## Permissions

- Passport Extraction: internal roles only; no Guest read/write.
- Visa Tracker Settings: System Manager or explicit Visa Tracker Manager role.
- Visa Tracking Application: internal operations/support roles; no Guest DocType access.
- Visa Tracking Status: controlled configuration role; operations can read/select.
- Visa Tracking Status Log: internal read; create only through service; no ordinary delete.
- Public SPA: only purpose-built whitelisted methods.

## Migration and fixture ownership

`the_visaguy` fixtures own:

- custom fields on Lead, Customer, and PF Process File,
- client script/query behavior where required,
- roles and custom permissions where required,
- initial Visa Tracking Status records if fixture strategy is chosen.

`passport_extractor` owns its own DocType schema, roles, permissions, and patches.

Run migration and fixture validation in staging. Never export unrelated production customizations into the feature commit.