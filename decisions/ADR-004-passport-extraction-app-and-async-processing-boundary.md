# ADR-004: Reusable Passport Extraction App, Asynchronous Processing Boundary, Private Audit History, and Verified-Data Ownership Model

## Status

Accepted, with one later narrowing: **ADR-012 (2026-09-03)** replaces the
trigger edge in the "Asynchronous processing boundary" subsection — a
configured passport row enters extraction when its
`FF File Collection File.status` becomes `Completed`, not when the
submission is persisted. The rest of this ADR, including the boundary rules
themselves, remains in force. See also the "Amendment (2026-09-03)" at the
end of this ADR for the extraction worker's execution identity.

## Context

FEAT-001 introduces automated passport data extraction from FileFlo uploads. The extraction must be reusable, must not slow down FileFlo submissions, must keep raw passport output private, and must preserve a complete audit history of extractions, corrections, and replacements. These boundaries are already defined in `features/ongoing/visa-tracking/01-architecture-and-data-model.md`; this ADR records them as accepted architecture.

## Decision

### Reusable passport extraction app

- A new Frappe app, `passport_extractor`, owns all extraction concerns:
  - `Passport Extraction` DocType and schema.
  - File loading, format validation, hashing, PDF rendering, image preprocessing.
  - PaddleOCR invocation, TD3 MRZ detection and parsing, check-digit validation.
  - Raw result retention, reviewed-value management, and extraction lifecycle states.
  - A small, documented Python service API for other apps to create and query extraction records.
- `passport_extractor` must not import from or depend on `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, or Visa Tracking Application.

### Asynchronous processing boundary

- The synchronous FileFlo post-save handler may only:
  1. receive stable identifiers for persisted FileFlo data,
  2. enqueue an inspection job with `enqueue_after_commit=True`, and
  3. return.
- It must not load Visa Tracker Settings, compare field IDs, calculate a file hash, open the file, import PaddleOCR, parse MRZ, resolve Lead/Customer, or create a tracking application.
- A short queue inspection worker in `the_visaguy` decides whether the persisted FileFlo field is a configured passport field and, if so, creates a `Passport Extraction` record.
- A long queue extraction worker in `passport_extractor` performs the OCR/MRZ pipeline.

### Private audit history

- `Passport Extraction` is append-only for audit purposes. Corrections and replacements create new records; prior history is never overwritten or deleted.
- Raw OCR text and raw extraction results are stored in private fields and are not exposed to Guest or public APIs.
- Extraction error logs must not contain raw passport details, MRZ text, or PII.

### Verified-data ownership model

- `passport_extractor` owns the reviewed passport values and the verification state (`Verified`, `Rejected`, `Needs Review`, etc.).
- `the_visaguy` decides when a verified extraction becomes the preferred passport for a Lead or Customer and links the record via `custom_passport_extraction`.
- Only a `Verified` extraction may be used to create or enable a `Visa Tracking Application`.
- A new or corrected upload creates a new extraction record; `the_visaguy` may update its preferred Link to point to the newer verified record, but the old extraction record remains in the audit history.

## Consequences

### Positive

- FileFlo submission response time is not materially affected by OCR workload.
- OCR and MRZ logic is isolated in a reusable app with a clear public API.
- Full provenance is preserved for compliance and debugging.
- Verified-data ownership prevents unverified extractions from driving public tracking status.

### Negative

- The queue-based design requires idempotency, retry bounds, and observability.
- Delayed extraction means a short window exists where the uploaded file has no extraction record.
- Extra care is needed to ensure `passport_extractor` remains dependency-free relative to VisaGuy business records.

## Alternatives considered

- Run OCR synchronously inside the FileFlo request. Rejected because it would slow submissions and couple FileFlo to heavy CV libraries.
- Store extraction records inside `the_visaguy`. Rejected because it would make the extractor non-reusable and would mix audit history with business orchestration.
- Allow unverified extractions to drive tracking. Rejected because it would risk exposing incorrect passport data and violate the verified-data ownership rule.

## Revisit when

Extraction needs to run in a separate service/process, another feature needs to consume `passport_extractor`, or the privacy boundary around raw OCR output needs to change.

## Amendment (2026-09-03): the extraction worker runs as Administrator

`passport_extractor.jobs.run_passport_extraction` now sets
`frappe.set_user("Administrator")` for the duration of the job and restores
the previous user in a `finally` block (`passport_extractor` `014a36e`).

**Why.** The chain that starts extraction begins with a **guest** FileFlo
upload, so the enqueued job inherited `Guest` as its session user. `Guest`
cannot write `Passport Extraction`. The job therefore could not move the
record out of `Queued` and could not save a failure state either — the
symptom in production was extractions sitting at `Queued` forever with no
error surfaced anywhere a human would look. This is the same class of silent
failure as the configuration gaps listed in the feature README.

**What this does and does not widen.** The elevation is confined to one
background job that reads a private `File` already linked to the extraction
record and writes only that extraction. It does not run in a request, does
not accept a user-supplied user, and does not extend to the inspection
handler, the lifecycle service, or any public API — those keep their own
permission handling. The privacy boundary of ADR-004 is unchanged: raw OCR
output stays in private, permlevel-restricted fields.

**Alternative not taken.** Granting `Guest` write permission on
`Passport Extraction` would have fixed the symptom by making a public role
able to write extraction records — strictly worse, and a permanent widening
rather than a scoped one.
