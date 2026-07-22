# ADR-003: FEAT-001 Repository/Component Ownership and Dependency Direction

## Status

Accepted

## Context

FEAT-001 (Visa application tracking and passport extraction) touches four implementation repositories plus two reference/boundary repositories. Without explicit ownership and dependency direction, implementation agents could introduce circular imports, leak business logic into reusable components, or place customizations in repositories that FEAT-001 does not own. The architecture and data model in `features/ongoing/visa-tracking/01-architecture-and-data-model.md` already defines these boundaries; this ADR materializes them as an accepted decision.

## Decision

### Repository/component ownership

| Repository / Component | Role in FEAT-001 | Owns | Does not own |
|---|---|---|---|
| `fileflo` | Generic persistence and extension point | Persisting submitted form values and uploaded `File` records; emitting a generic, reusable after-field-persisted event | Knowledge that a field is a passport; Visa Tracker Settings; extraction or tracking records |
| `passport_extractor` | Reusable extraction service | `Passport Extraction` DocType; file loading, hashing, PDF rendering, preprocessing, OCR invocation, TD3 MRZ parsing, check-digit validation; raw result and reviewed-value retention; extraction lifecycle, retries, duplicate/supersession metadata; a small reusable Python service API | When VisaGuy considers a FileFlo field to be a passport; Lead, Customer, FileFlo, ProcessFlo, or tracking references beyond generic source fields; public tracking authentication; status lifecycle |
| `the_visaguy` | Domain orchestrator and public API | `Visa Tracker Settings`; configured passport field IDs; FileFlo queued inspection; extraction orchestration; source-context resolution; preferred extraction Links on business records; `Visa Tracking Application`, `Visa Tracking Status`, and `Visa Tracking Status Log`; Lead/Customer/PF Process File lifecycle; custom fields and client scripts shipped as fixtures; public verification and status APIs; abuse controls and audit events; reconciliation jobs and reports | File persistence logic; reusable extraction internals |
| `processflo` | Integration target (no planned source change) | Base `PF Process File` DocType and process workflow | Planned custom fields, queries, and event handlers for tracking (supplied by `the_visaguy`) |
| `visa_tracker` | Public SPA | The standalone React application only | Business database; long-lived authentication credentials; direct access to Frappe resource APIs |
| `visaguy-website-client` | Read-only design reference | Its own visual system and components | Tracker code or commits |

### Dependency direction

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

### Branch/workflow ownership

- `visaguy_workspace`: documentation only on `feat/visa-tracker`.
- `the_visaguy` and `fileflo`: create `feat/visa-tracker` before any source change.
- `passport_extractor`: scaffold the new app/repository, make an initial scaffold commit, then create `feat/visa-tracker`.
- `visa_tracker`: initialize locally, commit scaffold and feature work on the default branch; no remote or `feat/visa-tracker` branch required.
- `processflo`: do not branch or edit unless reconnaissance proves a direct change is unavoidable; then create `feat/visa-tracker` first and record the deviation.
- `visaguy-website-client`: read-only; never commit tracker changes here.

## Consequences

### Positive

- Each repository has a single, clear reason to change.
- `passport_extractor` can be reused by future features without dragging in VisaGuy business logic.
- Dependency arrows prevent circular imports and keep FileFlo agnostic of passport/tracking semantics.
- Public SPA is isolated from internal Frappe DocType APIs.

### Negative

- `the_visaguy` becomes the central orchestrator and must coordinate changes across multiple repositories.
- Event-based boundaries require queue reliability and idempotency discipline.

## Alternatives considered

- Build the entire feature inside `the_visaguy`. Rejected because it would couple extraction logic to VisaGuy and prevent reuse.
- Let FileFlo directly create `Passport Extraction` records. Rejected because it would couple FileFlo to `passport_extractor` and prevent FileFlo from remaining a generic form product.
- Expose tracking DocTypes directly to the public SPA via `/api/resource`. Rejected because it would bypass security controls and leak internal identifiers.

## Revisit when

A new repository joins FEAT-001, `passport_extractor` is consumed by another feature, or the boundary between generic FileFlo events and VisaGuy-specific inspection needs to move.
