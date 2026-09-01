# ADR-007: Automatic Verification of Passport Extractions

## Status

Accepted

Supersedes the initial-release stance recorded in
`features/ongoing/visa-tracking/01-architecture-and-data-model.md` line 239
(`require_manual_verification` — "True for initial production release") and
narrows the exclusion "Automatic use of unverified extraction data" in
`features/ongoing/visa-tracking/README.md`.

## Context

FEAT-001 creates a `Visa Tracking Application` only when a `Passport Extraction`
reaches status `Verified`. The gate is enforced in depth:

- `visa_tracking/handlers/passport_extraction_handlers.on_update`
- `visa_tracking/handlers/lead_handlers.py:51`
- `the_visa_guy/doctype/visa_tracking_application.py:34` — throws
  "Passport Extraction must be Verified before tracking can be enabled."

The original rationale is sound: the verified extraction becomes the **public
authentication credential**. `verification_lookup_hash` is derived from passport
number plus date of birth, and that pair is exactly what an anonymous visitor
submits to retrieve a case. An OCR misread does not merely produce a bad record;
it keys an application to the wrong identity.

However, **nothing ever implemented the transition.** `require_manual_verification`
was specified but has zero references in any application. No whitelisted verify
endpoint, no scheduled job, no automatic promotion exists. In practice
extractions stopped permanently at `Extracted` and no tracking application was
ever produced without a human editing the document in desk. The setting was
inert configuration describing an unbuilt behaviour.

The owner reviewed this and chose automatic verification, explicitly declining a
dedicated `verified_by` treatment.

A material mitigating fact: in `passport_extractor`, `Extracted` is **already the
high-confidence terminal state**. `extraction_service` routes anything weaker to
`Needs Review` — failed check digits, missing required fields, a failed optional
field check, or confidence below threshold. `Extracted` therefore means every
ICAO check digit validated and confidence cleared the threshold.

## Decision

- When `Visa Tracker Settings.require_manual_verification` is unset **and**
  `enabled` is set **and** the record has `mrz_valid`, a `Passport Extraction`
  transitioning into `Extracted` is automatically promoted to `Verified`.
- The setting becomes live configuration. Setting it re-enables human review.
- Promotion is **queued, not inline**: `on_update` enqueues
  `the_visaguy.visa_tracking.jobs.auto_verify_extraction` with
  `enqueue_after_commit=True`. Saving the document inside its own `on_update`
  would re-enter the hook.
- The job **re-checks every condition against a freshly loaded document**, so a
  manual verification, a rejection, or a settings change occurring between
  enqueue and execution takes precedence over the queued intent.
- The promotion is applied through a normal ORM save, not `db_set`. The
  `Passport Extraction` controller stamps `verified_by` / `verified_on` during
  validation and freezes them afterwards via `_preserve_verification_audit`;
  writing status directly would leave them empty and break the next save of that
  document. Under the queue the stamp records the job user.

## Consequences

### Positive

- The end-to-end flow completes without human intervention, which is what the
  bench needs to be testable.
- `require_manual_verification` becomes meaningful instead of inert.
- Human review remains one setting away, per environment.

### Negative

- **An OCR result becomes a public authentication credential with no human
  review.** ICAO check digits detect most misreads but not all — a consistent
  substitution can still self-validate — and they attest nothing about whether
  the document itself is genuine.
- `verified_by` records an automated actor, so the audit trail no longer
  distinguishes human sign-off from machine promotion.
- The stricter posture assumed by ADR-005's threat model is relaxed. ADR-005 is
  not superseded; this narrows one of its operating assumptions.

### Recommendation for a production environment

Leave `require_manual_verification` **set** wherever the public tracker faces
real applicants, and rely on automatic verification only on development benches,
until the residual misread risk has been quantified against real documents.

## Alternatives considered

- **Create the tracking application at `Extracted` with `tracking_enabled = 0`**
  ("create early, expose late"). Fits existing invariants exactly — the doctype
  guard blocks *enabling* tracking, not creation — so staff would see the case
  immediately while public exposure waited for verification. Recommended at the
  time; the owner chose full automation instead.
- Auto-verify on a confidence threshold above the existing one. Rejected as
  redundant: `Extracted` already encodes a confidence gate.
- Implementing the promotion inside `passport_extractor`. Rejected: it would
  invert the dependency direction fixed by ADR-003, since the setting lives in
  `the_visaguy`.

## Revisit when

The public tracker serves real applicants, a misread is observed in practice, or
regulatory requirements demand attributable human verification of identity
documents.
