---
id: FEAT-001
title: Visa application tracking and passport extraction
status: ongoing
priority: high
repositories:
  - the_visaguy
  - fileflo
  - passport_extractor
  - visa_tracker
owners: []
depends_on:
  - ADR-003
  - ADR-004
  - ADR-005
created: 2026-07-20
updated: 2026-07-21
---

# Visa application tracking and passport extraction

## Summary

Build a public visa-tracking experience where a client verifies with passport number and date of birth, then sees the latest client-facing visa application status and status history.

The feature also introduces a reusable passport extraction app. Passport uploads already collected through FileFlo are detected asynchronously, processed by PaddleOCR and MRZ validation, stored as extraction-history records, reviewed, and linked to VisaGuy business records.

This feature is deliberately split across small, clearly owned components:

- `fileflo` persists submitted form data and emits a generic post-persistence event.
- `the_visaguy` owns VisaGuy-specific orchestration, settings, tracking records, lifecycle rules, custom fields, and public APIs.
- `passport_extractor` owns reusable extraction history and passport extraction logic.
- `visa_tracker` is a standalone React SPA for public status lookup.
- `processflo` remains the owner of `PF Process File`; it is an integration target, not a planned code-change repository.
- `visaguy-website-client` is a read-only design reference. Its visual system and compatible presentational components must be reused so the new tracker looks like the existing consumer website.

No application code, generated schema, secrets, passport samples, or production data belongs in this workspace repository.

## User value

- Clients can check progress without repeated phone calls or WhatsApp follow-ups.
- Operations users update client-facing status from the `PF Process File`, where they already work.
- Tracking starts while the case is still a Lead and continues when a Process File is created.
- Passport number and DOB are captured once from a verified extraction and reused.
- Future FileFlo form autofill can consume the same verified passport record.
- Extraction failures, corrections, replacements, duplicates, and verification remain auditable.

## Product flow

```text
Customer submits passport through FileFlo
        |
        v
FileFlo persists form field and file
        |
        v
After-commit event queues inspection only
        |
        v
the_visaguy worker checks Visa Tracker Settings
        |
        +-- field ID is not configured as passport --> stop
        |
        v
Create Passport Extraction and queue OCR
        |
        v
PaddleOCR + MRZ parse + check-digit validation
        |
        +-- low confidence / invalid checks --> Needs Review
        |
        v
Verified Passport Extraction
        |
        v
Link extraction to Lead and create Visa Tracking Application
        |
        v
Status = configured Lead default status
        |
        v
PF Process File created later
        |
        v
Link same Visa Tracking Application to PF Process File
        |
        v
Status = configured Process File created status
        |
        v
Operations changes Client Status on PF Process File
        |
        v
Visa Tracking Application and status log update
        |
        v
Client verifies passport + DOB in visa_tracker SPA
        |
        v
Public API returns approved, minimal status information
```

## Scope

### Included

1. A new `passport_extractor` Frappe app.
2. A `Passport Extraction` history DocType with source, processing, MRZ, extracted-value, verification, duplicate, and supersession data.
3. Local OCR using the already available PaddlePaddle 3.2.0 and PaddleOCR runtime, plus PyMuPDF and OpenCV headless where required.
4. A `Visa Tracker Settings` Single DocType in `the_visaguy`.
5. Asynchronous FileFlo upload inspection. Even field-ID matching happens in a queue after the FileFlo transaction commits.
6. Exact passport field IDs configured one per line in settings for the first release.
7. A `Visa Tracking Application`, `Visa Tracking Status`, and `Visa Tracking Status Log` in `the_visaguy`.
8. Read-only tracking links on Lead, Customer, and `PF Process File`.
9. A client-status Link field on `PF Process File`.
10. Automatic initial status while only a Lead exists.
11. Automatic configured status when a Process File is linked or created.
12. Daily operations status updates from `PF Process File`.
13. Exceptional direct corrections from `Visa Tracking Application` with audit history.
14. Guest APIs in `the_visaguy` for verification and status retrieval.
15. HMAC-based lookup, short-lived opaque Redis sessions, rate limiting, lockouts, generic failures, masking, CORS restriction, and audit logging.
16. A standalone `visa_tracker` React SPA created locally with Vite, TypeScript, React Router, Tailwind CSS, shadcn/ui, Axios, React Hook Form, and Zod.
17. Design parity with `visaguy-website-client`.
18. A reconciliation path for missed FileFlo events and mismatched tracking statuses.
19. Automated tests and documented manual acceptance tests.

### Excluded from the first release

- WhatsApp conversational status retrieval. WhatsApp only links to the public tracker website.
- Sending passport files or passport data to an LLM or external OCR API.
- Automatic use of unverified extraction data.
- Full FileFlo autofill. The data model and APIs must enable it later, but autofill is a follow-up feature.
- Client-visible document downloads, authority documents, internal comments, payments, employee names, or operational notes.
- Fuzzy public passport matching.
- Wildcard passport field IDs. Exact matching is required initially.
- A public case selector for multiple simultaneous active applications. The MVP permits one active tracking application per verified passport identity; conflicts require internal review.
- A Git remote for the new frontend repository during this task.

## Repository and branch rules

| Repository | Role | Planned source changes | Required branch/workflow |
|---|---|---:|---|
| `visaguy_workspace` | Canonical plan and task status | Documentation only | `feat/visa-tracker` |
| `the_visaguy` | Domain, orchestration, settings, custom fields, APIs | Yes | Create `feat/visa-tracker` before changes |
| `fileflo` | Generic post-persistence extension event | Yes, minimal | Create `feat/visa-tracker` before changes |
| `passport_extractor` | New extraction app | New app/repository | Scaffold, make an initial scaffold commit, then create `feat/visa-tracker` |
| `processflo` | Owns PF Process File | No planned source change | Do not branch or edit unless reconnaissance proves a direct change is unavoidable; then create `feat/visa-tracker` first and record the deviation |
| `visa_tracker` | New public SPA | New local repository | Initialize locally with Vite, initialize Git, commit scaffold and feature work; no remote required and no `feat/visa-tracker` branch required |
| `visaguy-website-client` | Design/component reference | No | Read-only; never commit tracker changes here |

## Development paths

- Frappe app changes are made on the remote bench at `/home/shahzad/bench` over `erpcode.tridz.in:2257`.
- Frontend development uses the local workspace root `/home/shzd/Projects/tridz/`.
- The new public tracker repository should be created at `/home/shzd/Projects/tridz/visa_tracker`.
- `visaguy-website-client` remains the design reference repo in the same local workspace tree.

The developer must not modify any application repository from its current default/non-feature branch.

## Required status model

Initial status records:

1. Application Received
2. Documents Under Review
3. Verification in Progress
4. Working on Your Application
5. Application Submitted
6. Update Shared with Client

Statuses are records, not hardcoded Select options. Each status has a stable code, order, default message, active flag, final flag, success flag, and `allow_on_process_file` flag.

`Visa Tracker Settings` controls at least:

- Default Lead Status
- Process File Created Status
- whether automatic Process File transition is enabled

No business code may hardcode the labels `Application Received` or `Working on Your Application` as lifecycle decisions.

## Status ownership rules

- `Visa Tracking Application.current_status` is the canonical current public state.
- `Visa Tracking Status Log` is the canonical immutable client-visible timeline.
- Before a Process File exists, status is the configured system default and no Lead status field is required.
- After a Process File is linked, `PF Process File.custom_client_status` is the normal operations input.
- Direct changes from `Visa Tracking Application` are exceptional and must synchronize the linked Process File without recursion.
- Every effective status change creates one log entry. Saving the same status again must not create a duplicate log.

## Passport ownership rules

- `Passport Extraction` owns extraction history and reviewed passport values.
- The extractor has no imports from FileFlo, ProcessFlo, Lead, Customer, or Visa Tracking Application.
- `the_visaguy` links verified extraction records to Lead, Customer, and Visa Tracking Application.
- `Lead.custom_passport_extraction` and `Customer.custom_passport_extraction` identify the current preferred verified extraction, not the full history.
- The original file and raw extraction result remain private and internal.
- A new or corrected upload creates a new extraction record; prior history is never overwritten or deleted.

## Queue requirements

### Synchronous FileFlo path

The synchronous post-save handler may only:

1. receive stable identifiers for persisted FileFlo data,
2. enqueue an inspection job with `enqueue_after_commit=True`, and
3. return.

It must not load Visa Tracker Settings, compare field IDs, calculate a file hash, open the file, import PaddleOCR, parse MRZ, resolve Lead/Customer, or create a tracking application.

### Short queue inspection

The inspection worker must:

1. reload the persisted FileFlo record,
2. load cached Visa Tracker Settings,
3. stop when the feature is disabled,
4. compare the persisted field ID to configured exact field IDs,
5. validate that the value is a supported private file,
6. compute or obtain an idempotency key,
7. avoid duplicate extraction requests,
8. create the `Passport Extraction`, and
9. enqueue long-running OCR after commit.

### Long queue extraction

The extraction worker must:

1. mark Processing,
2. resolve the private file safely,
3. render PDF pages as images where needed,
4. perform orientation/cropping/preprocessing,
5. run PaddleOCR,
6. detect TD3 MRZ candidates,
7. parse values and check digits,
8. store raw result and reviewed-value candidates,
9. classify Extracted, Needs Review, or Failed,
10. avoid logging raw passport details, and
11. make retry behavior bounded and auditable.

## Frontend requirements

The frontend stack is fixed:

- React
- Vite
- TypeScript
- React Router
- Tailwind CSS
- shadcn/ui
- Axios
- React Hook Form
- Zod

The SPA must use the same VisaGuy consumer visual language as `visaguy-website-client`:

- same logo and approved brand assets,
- same header and footer composition,
- same typography scale,
- same colors and CSS variables,
- same button, input, card, alert, loading, spacing, radius, and shadow treatment,
- same responsive behavior where relevant.

Presentational components may be copied and adapted. Next.js-specific routing, image, server, environment, authentication, and data-fetching code must not be copied into the Vite app.

## Public information boundary

The public response may include only:

- masked applicant name,
- masked passport number,
- destination and visa type when approved,
- current public status,
- configured public message,
- last-updated timestamp,
- public status timeline,
- generic support link.

It must not include DOB, full passport number, passport files, extracted MRZ, internal document names, Lead/Customer/PF identifiers, internal notes, employee names, authority documents, payment data, or processing errors.

## Task order

Implementation must follow this order. A junior developer must not skip ahead when a dependency is incomplete.

1. [TASK-001](../../../tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md) — completed preflight, local repository setup, and exact integration evidence.
2. [TASK-002](../../../tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md) — in-progress extraction-history model in the new app.
3. [TASK-003](../../../tasks/completed/visa-tracking/TASK-003-passport-ocr-and-mrz-pipeline.md) — completed PaddleOCR/MRZ pipeline; runtime OCR verification is deferred to TASK-010.
4. [TASK-004](../../../tasks/in-progress/visa-tracking/TASK-004-fileflo-queued-passport-detection.md) — in-progress FileFlo event and queued matching.
5. [TASK-005](../../../tasks/completed/visa-tracking/TASK-005-tracking-data-model-and-settings.md) — completed settings, tracking DocTypes, custom fields, and fixtures; runtime migration is deferred to TASK-010.
6. [TASK-006](../../../tasks/ready/visa-tracking/TASK-006-tracking-lifecycle-and-status-sync.md) — Lead, Customer, and Process File lifecycle.
7. [TASK-007](../../../tasks/ready/visa-tracking/TASK-007-public-api-and-security-controls.md) — secure public APIs.
8. [TASK-008](../../../tasks/completed/visa-tracking/TASK-008-frontend-scaffold-and-design-parity.md) — completed local Vite design system and shared visual shell.
9. [TASK-009](../../../tasks/ready/visa-tracking/TASK-009-frontend-tracking-flow.md) — form, verification, status, timeline, errors.
10. [TASK-010](../../../tasks/ready/visa-tracking/TASK-010-end-to-end-verification-and-rollout.md) — migration, test matrix, security gate, and rollout evidence.

## Supporting specifications

- [Architecture and data model](01-architecture-and-data-model.md)
- [Backend workflows and API contracts](02-backend-workflows-and-api-contracts.md)
- [Frontend design and layout](03-frontend-design-and-layout.md)
- [Security, privacy, and abuse controls](04-security-privacy-and-abuse-controls.md)
- [Test and verification matrix](05-test-and-verification-matrix.md)
- [Junior developer runbook](06-developer-runbook.md)

## Acceptance criteria

The feature is complete only when all of the following have implementation evidence:

- FileFlo submission response time is not materially increased by passport detection.
- Field-ID matching happens in a worker, not in the request transaction.
- A configured passport field creates exactly one extraction per persisted file/version.
- A non-configured field creates no extraction.
- OCR runs only in a worker and no external OCR/LLM receives the passport.
- Passport number and DOB are parsed from a valid MRZ and check digits are stored.
- Low-confidence or invalid results require review.
- Only a verified extraction is linked as the preferred Lead/Customer passport.
- A tracking application is created and linked while the case is a Lead.
- Its initial status is read from settings.
- When a Process File is linked, its tracking Link and configured created-status are populated.
- Operations can update Client Status on PF Process File.
- The tracking current status and exactly one history row update.
- An exceptional direct status correction remains synchronized and audited.
- Public verification uses an HMAC lookup and returns an opaque short-lived token.
- Invalid passport/DOB combinations receive a generic response.
- Rate limiting and temporary lockout are tested.
- No sensitive values appear in URLs, logs, browser localStorage, analytics, or error messages.
- The React SPA builds successfully and matches the approved consumer website design on desktop and mobile.
- The frontend repository contains local commits even though no remote is configured.
- All backend repositories changed by the implementation use `feat/visa-tracker`.
- Migrations, fixtures, queue jobs, API tests, UI tests, and manual acceptance tests have recorded evidence.
- No real passport or production PII is committed to any repository.

## Dependencies

- Frappe 15/Python 3.10 runtime.
- PaddlePaddle 3.2.0 and PaddleOCR import availability, already confirmed on the target bench by the project owner.
- A successful runtime OCR test and model availability are still required before calling extraction runtime-verified.
- Existing FileFlo persistence and form-field identifiers.
- Existing Lead-to-FileFlo and Lead-to-PF Process File relationships, to be evidenced in TASK-001.
- Redis workers and scheduler.
- Access to `visaguy-website-client` for read-only design reference.

## Risks

- Passport and DOB are weak knowledge factors; public data must remain minimal.
- Field IDs may differ between forms or change over time.
- FileFlo can resubmit or update the same field, causing duplicate jobs without idempotency.
- OCR libraries are heavy and can affect worker memory.
- PaddleOCR model files may be unavailable to production workers unless deployment preloads them.
- Passport images may be rotated, blurred, multi-page, password-protected, or not contain an MRZ.
- The workspace records that `processflo` currently has a dirty working tree. Do not modify it without reconciling unrelated changes.
- Direct two-way status synchronization can recurse or generate duplicate logs if not routed through one service.
- Permissive CORS, raw guest DocType access, or detailed authentication errors could expose PII.
- Blindly copying Next.js components into Vite can introduce broken imports and design drift.

## Open questions

No unresolved product or architecture decision blocks implementation. TASK-001 must replace assumptions with source evidence for:

- the exact FileFlo persisted record and post-save location,
- the exact stable field-ID property,
- the exact File Collection-to-Lead relationship,
- the exact Lead-to-PF Process File creation/link path,
- whether both ERPNext Lead and CRM Lead require tracking Links in the deployed flow.

If evidence contradicts this plan, stop the affected task, document the mismatch, and request a workspace decision rather than improvising a new architecture.

## Completion notes

Implementation started with TASK-001 preflight and repository setup. Move to `completed/` only after TASK-010 records implementation and validation evidence.
