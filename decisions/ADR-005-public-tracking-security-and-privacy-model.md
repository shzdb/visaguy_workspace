# ADR-005: Public Tracking Security and Privacy Model

## Status

Accepted

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

- Public API endpoints restrict allowed origins to the approved frontend base URL configured in `Visa Tracker Settings`.
- Wildcard or overly permissive CORS is prohibited.

### Masking and minimal response boundary

The public response may include only:

- masked applicant name,
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
