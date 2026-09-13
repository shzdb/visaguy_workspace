# ADR-015: One Tracking Application per Lead Applicant, Several per Passport

## Status

Accepted (2026-09-14), with two open items (see "Open items").

Supersedes the feature README exclusion "one active tracking application per
verified passport identity; conflicts require internal review" and the
"public case selector" exclusion. Amends ADR-005 (session carries several
applications through opaque references). Replaces the Lead- and
Customer-level `custom_visa_tracking_application` Links written by TASK-006.
ADR-014 (Process File ownership) is unchanged.

## Context

One person (one passport + date of birth) can be in several visa cases at
the same time, with a different role in each: primary in one and dependant
in another, primary in all, and so on.

Today (`the_visaguy` `8cf4c64`):

- `create_tracking_application` reuses the active application with the same
  `verification_lookup_hash`, or flags an "identity conflict" and creates
  nothing when there are several.
- On reuse, `_ensure_lead_links` points the second Lead's
  `custom_visa_tracking_application` at the first case's application — the
  second case then shows another case's data.
- `verify_identity` returns one arbitrary match; the session holds one
  application; the SPA shows one status page.

On `visaguy` (2026-09-14): 2 passports appear in more than one source
document and 2 "identity conflict" errors are logged.

## Decision

Owner decisions of 2026-09-14:

1. **A tracking application belongs to one Lead applicant row.** The case is
   the `Applicant Information` row on `Lead.custom_applicant_information` or
   `CRM Lead.custom_applicant_information`. The file collection is **not**
   the case key.
2. **The link lives on the applicant row.** A new custom field
   `Applicant Information.visa_tracking_application` (Link, read-only).
   The Lead-level `custom_visa_tracking_application` is no longer needed.
   The Customer-level copy (written by `lead_handlers`) is removed with it,
   since a Customer can have several cases.
3. **Reuse only within the same applicant row.** Same identity hash and same
   applicant row → reuse (idempotent redelivery). Same hash, different row →
   a new application. The "identity conflict" flag stays only for true
   duplicates on one row.
4. **`destination` is copied from the Lead and is mandatory.**
   `Lead/CRM Lead.custom_destination` is a required Link on both doctypes.
   `Visa Tracking Application.destination` becomes mandatory.
5. **Closed and completed cases are treated like any other case.** They are
   listed with the rest; no separate handling. `tracking_enabled` still
   gates what a client can see.
6. **Role per case needs no new logic.** Each application links its own
   Process File (ADR-014); `get_process_file_family` gives primary or
   dependant for that case. Before a Process File exists, the applicant
   row's `type` is the role.
7. **Public API** (technical choice, recorded here):
   - `verify_identity` loads every tracking-enabled application for the
     hash (capped at 20) and stores them in the session as
     **session-scoped random references** → application names. Response
     unchanged: a token only.
   - New `list_applications(session_token)` →
     `[{application_ref, destination, visa_type, role, title, last_updated}]`.
   - `get_tracking_status(session_token, application_ref=None)`. With no
     reference and exactly one application, the response is identical to
     today's, so the current SPA keeps working until the new one ships.
   - An unknown or foreign reference returns the constant generic failure.
     Rate limiting, audit and masking rules are unchanged.
8. **SPA:** one application → status page as today; several → a case list,
   then the status page with a switch control. References stay in React
   state only (ADR-005).

## Open items

- **O1 — Visa type source.** The owner asked for visa type from the Lead,
  but neither `Lead` nor `CRM Lead` has a visa type field (checked
  2026-09-14 on `visaguy`; nor do `Destination` or `PF Process File`).
  Until a source is named, `visa_type` stays optional and empty.
- **O2 — Finding the applicant row at creation.** Creation starts from a
  Passport Extraction whose provenance is a FileFlo row in a file
  collection. The only field joining that to an applicant row is
  `Applicant Information.file_collection`. Using it to *find* the row does
  not make it the case *key* (the stored key is the row), but the owner
  should confirm this lookup, or name another join.

## Consequences

### Positive

- Every case a person is in is trackable, with the right role per case.
- Fixes the existing defect where a second Lead points at another case's
  application.
- Backward compatible for one-case clients.

### Negative

- The session and the public contract grow (references, a new endpoint).
- `Applicant Information` is a `visaguy_crm` child doctype; the new field is
  a `the_visaguy` Custom Field fixture on it.
- Removing the Lead- and Customer-level fields must not go through a
  fixture sweep (risk 25). Stop writing them first; delete them later with
  an explicit patch. 9 Leads have the Lead-level field set on `visaguy`.
- An applicant row deleted and re-added on the Lead creates a new case.

## Alternatives considered

- **File collection as the case key.** Rejected by the owner.
- **One application per passport, with a case list inside it.** Rejected:
  status, timeline and dependants are per case.
- **Lead-level Link kept for the primary only.** Rejected by the owner: no
  separate field is needed once each row has its own link.

## Revisit when

An applicant can appear twice in one Lead, cases move between Leads, or the
cap of 20 applications per identity is reached.
