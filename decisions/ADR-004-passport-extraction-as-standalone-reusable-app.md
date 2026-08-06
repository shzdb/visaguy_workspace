# ADR-004: Passport Extraction as a Standalone Reusable App

## Status

Accepted

## Context

FEAT-001 requires extracting passport number and date of birth from uploaded passports. The extraction concern — OCR, MRZ parsing, check-digit validation, confidence handling, review, and history — is independent of VisaGuy's domain, and is plausibly useful to other Frappe projects.

The bench already carries 18 internally maintained apps, several of which overlap (`crm`/`visaguy_crm`/`visaguy_frappe_crm`). Adding a nineteenth app needs justification against simply extending `the_visaguy`.

Passport data is also the most sensitive PII in the system, so where it lives and how long it is retained matters.

## Decision

- Passport extraction lives in a new standalone app, `passport_extractor` (`tridz-dev/passport_extractor`).
- The app owns a `Passport Extraction` DocType holding source, processing state, MRZ data, extracted values, verification state, duplicate detection, and supersession.
- The app declares no `required_apps` and imports nothing from `fileflo`, `processflo`, `Lead`, `Customer`, or `Visa Tracking Application`. It has no knowledge that VisaGuy exists.
- `the_visaguy` owns all domain coupling: it decides which uploads are passports, and links verified extractions to `Lead` and `Customer`.
- Extraction history is append-only. A new or corrected upload creates a new record; prior records are superseded, never overwritten or deleted.
- `Lead.custom_passport_extraction` and `Customer.custom_passport_extraction` point at the current *preferred verified* extraction, not the full history.
- OCR runs locally via PaddleOCR. No passport file or passport data is sent to any external OCR service or LLM.
- The original file and the raw extraction result remain private and internal.

## Consequences

### Positive

- The extraction concern is independently testable, installable, and reusable.
- The PII blast radius is contained in one app with one role (`Passport Extractor User`).
- Append-only history makes corrections, replacements, duplicates, and verification auditable.
- Local-only OCR removes a whole class of third-party data-processing exposure.
- Future FileFlo autofill can consume the same verified record without new extraction work.

### Negative

- A nineteenth maintained app increases upgrade and dependency surface.
- The boundary must be actively defended; a single convenience import from `the_visaguy` would destroy the reusability claim.
- PaddleOCR and its models are heavy, affecting worker memory and deployment size.
- Append-only history grows without bound and needs a retention decision later.
- Cross-app debugging is harder than a single-app implementation.

## Alternatives considered

- **Extraction inside `the_visaguy`.** Rejected: mixes the most sensitive PII in the system into a broad domain app and forecloses reuse.
- **A hosted OCR or LLM extraction API.** Rejected: sending passport images to a third party is an unacceptable privacy and compliance exposure for this data class.
- **Storing only the final extracted values, no history.** Rejected: makes corrections, duplicates, and verification unauditable.

## Revisit when

A second product needs extraction and the boundary is tested in practice, PaddleOCR's footprint becomes untenable for production workers, or a retention policy forces pruning of extraction history.
