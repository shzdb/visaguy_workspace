# ADR-015: One Tracking Application per Lead Applicant, Several per Passport

## Status

Accepted (2026-09-14).

Supersedes the feature README exclusion "one active tracking application per
verified passport identity; conflicts require internal review" and the
"public case selector" exclusion. Amends ADR-005: the session carries
several applications through opaque references, and `visa_type` leaves the
public payload. Replaces the Lead- and Customer-level
`custom_visa_tracking_application` Links written by TASK-006. ADR-014
(Process File ownership) is unchanged.

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
   an `Applicant Information` row on `Lead.custom_applicant_information` or
   `CRM Lead.custom_applicant_information`. The file collection is **not**
   the case key.
2. **Every application traces back to its Lead.** Creation starts from the
   Lead the Passport Extraction came from (`_resolve_source_lead`). The
   application's existing `lead` / `crm_lead` Link is **mandatory**:
   exactly one of the two is set.
3. **The applicant link lives on the applicant row.** A new custom field
   `Applicant Information.visa_tracking_application` (Link, read-only). The
   Lead-level `custom_visa_tracking_application` is no longer needed. The
   Customer-level copy (written by `lead_handlers`) is removed with it, since
   a Customer can have several cases.
4. **Finding the row inside that Lead:** the applicant row whose
   `file_collection` equals the extraction's source collection. If none
   matches and the Lead has exactly one applicant row, that row. Otherwise
   flag for review and create nothing. The collection is used only to pick
   a row within the known Lead; the stored key is the row.
5. **Reuse only within the same applicant row.** Same identity hash and same
   applicant row → reuse (idempotent redelivery). Same hash, different row →
   a new application. The "identity conflict" flag stays only for true
   duplicates on one row.
6. **`destination` comes from the Lead and is mandatory.**
   `Lead/CRM Lead.custom_destination` is a required Link to `Destination` on
   both doctypes. `Visa Tracking Application.destination` becomes a
   mandatory Link to `Destination`.
7. **`visa_type` is removed** from `Visa Tracking Application`, from the
   public status payload, and from the SPA. No source exists on the Lead.
8. **Closed and completed cases are treated like any other case.** They are
   listed with the rest. `tracking_enabled` still gates what a client can
   see.
9. **Role per case needs no new logic.** Each application links its own
   Process File (ADR-014); `get_process_file_family` gives primary or
   dependant for that case. Before a Process File exists, the applicant
   row's `type` is the role.
10. **Public API** (technical choice, recorded here):
    - `verify_identity` loads every tracking-enabled application for the
      hash (capped at 20) and stores them in the session as
      **session-scoped random references** → application names. Response
      unchanged: a token only.
    - New `list_applications(session_token)` →
      `[{application_ref, destination, role, title, last_updated}]`.
    - `get_tracking_status(session_token, application_ref=None)`. With no
      reference and exactly one application, the response is today's
      without `visa_type`, so the current SPA keeps working (it renders visa
      type only when present).
    - An unknown or foreign reference returns the constant generic failure.
      Rate limiting, audit and masking rules are unchanged.
11. **SPA:** one application → status page as today; several → a case list,
    then the status page with a switch control. References stay in React
    state only (ADR-005).

Operations roles for the related manual-status work (ADR-010 amendment
2026-09-14) are `Operations Team Lead` and `Operations Associate`.

## Consequences

### Positive

- Every case a person is in is trackable, with the right role per case.
- Fixes the existing defect where a second Lead points at another case's
  application.
- Backward compatible for one-case clients.

### Negative

- The session and the public contract grow (references, a new endpoint), and
  one key (`visa_type`) is removed.
- `Applicant Information` is a `visaguy_crm` child doctype; the new field is
  a `the_visaguy` Custom Field fixture on it.
- Removing the Lead- and Customer-level fields must not go through a
  fixture sweep (risk 25). Stop writing them first; delete them later with
  an explicit patch. 9 Leads have the Lead-level field set on `visaguy`.
- An applicant row deleted and re-added on the Lead creates a new case.
- A Lead with several applicant rows and no matching collection needs a
  person to resolve it.

## Alternatives considered

- **File collection as the case key.** Rejected by the owner.
- **One application per passport, with a case list inside it.** Rejected:
  status, timeline and dependants are per case.
- **Lead-level Link kept for the primary only.** Rejected by the owner: no
  separate field is needed once each row has its own link.
- **Keep `visa_type` and fill it later.** Rejected by the owner for now.

## Revisit when

An applicant can appear twice in one Lead, cases move between Leads, a visa
type source is added to the Lead, or the cap of 20 applications per identity
is reached.
