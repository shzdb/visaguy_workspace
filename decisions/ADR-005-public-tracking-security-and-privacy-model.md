# ADR-005: Public Tracking Security and Privacy Model

## Status

Accepted, with two later narrowings:

- **ADR-011 (2026-09-03)** replaces the "HMAC lookup" subsection below: the
  public lookup hash is unkeyed.
- **The "Applicant names are returned in full" amendment (2026-09-03)** at
  the end of this ADR replaces the applicant-name half of the "Masking and
  minimal response boundary" subsection, and renames the wire field.

Everything else in this ADR — opaque sessions, generic failures, abuse
controls, CORS, passport-number masking, and the API access boundary —
remains in force.

## Context

FEAT-001 exposes a public visa-status lookup using passport number and date of birth as weak knowledge factors. Because these values have limited entropy and could be guessed or abused, the public API must minimize data exposure, prevent enumeration, and keep session state server-side. The security and privacy model is already described in `features/ongoing/visa-tracking/README.md` and `features/ongoing/visa-tracking/01-architecture-and-data-model.md`; this ADR records it as accepted architecture.

## Decision

### HMAC lookup

- The server computes `verification_lookup_hash` as HMAC-SHA256 over a canonical representation of passport number + date of birth.
- The HMAC key is server-side configuration (for example, `visa_tracker_lookup_hmac_key`) and is never committed to any repository.
- Plain SHA or unsalted hashes of passport+DOB are prohibited because the input entropy is too low for offline attack resistance.

### Opaque short-lived Redis session

- A successful verification returns an opaque, short-lived session token stored in Redis.
- Session expiry is configurable (suggested 15 minutes) and bounded.
- The session token is the only value the public SPA needs to poll or display status.
- The SPA must not store passport number, DOB, or session token in `localStorage`, analytics, or URLs.

### Generic failures

- Invalid passport/DOB combinations, missing tracking records, expired sessions, and abuse triggers all receive the same generic failure response.
- Error messages must not reveal whether a passport number exists, whether a tracking record is present, or what specifically failed.

### Abuse controls

- Rate limiting applies to verification attempts.
- Temporary lockout applies after a configured number of failed attempts (suggested 5) for a configurable duration (suggested 15 minutes).
- Abuse events are logged server-side for operations review; logs must not contain raw passport numbers or DOB.

### CORS restriction

- ~~Public API endpoints restrict allowed origins to the approved frontend base URL configured in `Visa Tracker Settings`.~~
  **Superseded 2026-09-03 by ADR-013**: the `Origin` header is forgeable and is no
  longer an authorization input. Header emission was already delegated to Frappe by
  ADR-008.
- Wildcard or overly permissive CORS is prohibited. This is now governed by
  `allow_cors` in `site_config.json` rather than by an application-level check;
  see ADR-013's consequences.

### Masking and minimal response boundary

The public response may include only:

- applicant name (**amended 2026-09-03: returned in full, not masked** — see
  the amendment at the end of this ADR),
- masked passport number,
- destination and visa type when approved,
- current public status,
- configured public message,
- last-updated timestamp,
- public status timeline,
- generic support link.

The public response must not include:

- DOB,
- full passport number,
- passport files or extracted MRZ,
- internal document names,
- Lead/Customer/PF identifiers,
- internal notes, employee names, authority documents, payment data, or processing errors.

### API access boundary

- The public SPA may call only purpose-built whitelisted methods in `the_visaguy`.
- Direct `/api/resource/*` access to `Visa Tracking Application`, `Passport Extraction`, or related DocTypes is prohibited for Guest.

## Consequences

### Positive

- Weak knowledge factors are not sufficient to enumerate cases or extract PII.
- Server-side sessions keep sensitive state out of the browser.
- Generic failures prevent attacker probing.
- Rate limiting and lockout reduce brute-force risk.
- Minimal response boundary limits blast radius if a session is compromised.

### Negative

- More implementation complexity than a direct DocType query.
- Redis becomes a runtime dependency for public tracking sessions.
- Generic failures give clients less detail when they mistype data.

## Alternatives considered

- Direct guest DocType query with filters. Rejected because it would expose internal identifiers and allow enumeration.
- Stateless signed JWT containing passport identity. Rejected because it would place sensitive claims in the client and complicate revocation.
- Detailed error messages for invalid passport/DOB. Rejected because they would leak case existence information.
- Session in browser `localStorage`. Rejected because it increases XSS/PII exposure.

## Revisit when

The threat model changes, additional public channels (for example, WhatsApp) consume the API, or regulatory requirements alter masking or retention rules.

## Amendment (2026-09-03): applicant names are returned in full

**Owner decision.** The public status payload returns the applicant's full
name. It is no longer masked. This replaces the "masked applicant name"
bullet in the "Masking and minimal response boundary" subsection above and
the corresponding masking rules in TASK-007 §"Applicant name".

**The wire field is renamed with it: `applicant_name_masked` →
`applicant_name`**, both at the top level of the status payload and inside
each `dependants` entry. A key named `..._masked` carrying an unmasked value
is a lie in the contract that every future reader has to be told about; the
rename removes the need for the explanation. `passport_number_masked` keeps
its name and its masking.

The rename is a breaking change to the public status contract, taken
deliberately and safely: `visa_tracker` is the only consumer (a bench-wide
search for the old key returns nothing outside `the_visaguy` and
`visa_tracker`), the SPA is deployed from the same release, and both sides
were changed together. `applicant_name` was previously listed in
`visa_tracker`'s `FORBIDDEN_STATUS_RESPONSE_FIELDS` — as the name of the
*unmasked* value the payload must never contain — and has been removed from
that list, which is exactly the assertion this decision reverses.

**Why this is a smaller change than it looks.** The masking never protected
the name against the person receiving it. To reach the status payload a
caller has already presented a matching passport number and date of birth
and holds a valid opaque session — they are, by construction, the applicant
or someone the applicant gave their passport details to. A masked `J****e`
told that caller nothing they did not already know, while making the tracker
read as broken to a client looking at their own case. Every other control in
this ADR — the lookup gate, opaque sessions, generic failures, rate
limiting, CORS, the API access boundary, and passport-number masking — is
unchanged and still stands between an anonymous visitor and this payload.

**What it does change, honestly.** The blast radius of a compromised or
guessed session is now one full name (plus, for a primary, the full names of
their dependants) rather than a masked initial. Name is the only field whose
exposure increased; DOB, full passport number, files, MRZ, internal document
names and Lead/Customer/PF identifiers remain excluded exactly as before.
This is accepted as proportionate given that the credential to reach the
payload is the applicant's own passport number and DOB.

**Where the name comes from.** `Visa Tracking Application.applicant_display_name`,
populated on application create from the verified `Passport Extraction`'s
`given_names` + `surname`. **This field had never been written by any code
path before this change** — nothing set it, so it was always empty and the
public payload always returned the blank-name placeholder `*****` for every
applicant. Reuse of an existing application backfills a missing display name
without touching other fields (`_backfill_applicant_display_name`, an
`update_modified=False` `db.set_value`). Dependant names come from the
dependant's own Process File `applicant_name`.

**Two consequences worth recording rather than discovering later.**

1. The constant-shape guarantee for this field is gone. The old masking
   helper returned `*****` for a blank, whitespace, or `None` name; the new
   code returns `""`. An application whose extraction carried neither given
   names nor surname now yields an empty string on the wire, and the SPA
   renders whatever it renders for an empty name. See risk 32.
2. `mask_applicant_name` in `visa_tracking/services/response_service.py` is
   now unreferenced by production code. It is retained and still unit-tested.
   Deleting it is a separate, deliberate cleanup, not a side effect of this
   decision.

ADR-010's "Privacy shape (owner decision)" paragraph describes dependant
names as "masked name via the existing masking helper" under the key
`applicant_name_masked`. That sentence predates this amendment and is now
wrong on both points; the array shape it specifies is otherwise unchanged
and still correct.

### Revisit this amendment when

A public channel that is not the applicant's own browser consumes the status
payload (for example, a WhatsApp bot forwarding a status into a shared
thread), or a regulator or contract requires minimization of names in
client-facing responses.
