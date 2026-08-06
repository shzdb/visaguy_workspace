---
id: TASK-007
feature: FEAT-001
title: Secure public tracking APIs and abuse controls
status: completed
repository: the_visaguy
owners: []
depends_on:
  - TASK-006
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Secure public tracking APIs and abuse controls

## Objective

Expose guest APIs that let a client verify with passport number and date of birth and then read a minimal, approved status payload, without leaking PII.

## Required behaviour

- HMAC-based lookup of the passport/DOB pair.
- A short-lived opaque session token held in Redis; no sensitive value in the token.
- Rate limiting and temporary lockout on repeated failures.
- A single generic failure response for every invalid combination.
- Masking of applicant name and passport number.
- CORS restricted to the tracker origin.
- Audit logging of verification attempts.

## Public information boundary

The response may include only: masked applicant name, masked passport number, destination and visa type when approved, current public status, configured public message, last-updated timestamp, public status timeline, and a generic support link.

It must not include DOB, full passport number, passport files, extracted MRZ, internal document names, Lead/Customer/PF identifiers, internal notes, employee names, authority documents, payment data, or processing errors.

## Constraints

No sensitive value may appear in a URL, query string, log line, browser storage, analytics payload, or error message.

## Validation

An invalid passport/DOB pair returns the generic response; rate limiting and lockout trigger under test; the response payload contains no field outside the approved list.

## Definition of done

The public surface is minimal, rate-limited, audited, and free of PII leakage.

## Implementation evidence

`tvgglobal/the_visaguy`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `d20cc6d` | 2026-07-21 | feat: add secure public tracking APIs |

Modules: `visa_tracking/api/verification.py`, `api/status.py`, `services/lookup_service.py`, `services/session_service.py`, `services/rate_limit_service.py`, `services/response_service.py`, `utils/security.py` (120 lines), `utils/constants.py`.

Tests: `test_public_api.py`, `test_lookup_service.py`, `test_session_service.py`, `test_rate_limit_service.py`, `test_response_service.py`, `test_security_utils.py`.

Backing DocType: `Visa Tracker Audit Log`.

## Known limitations

The API tests exist as source but no recorded pass evidence is held in this workspace, and CORS restriction has not been verified against a deployed origin — the tracker SPA does not exist yet (TASK-008). Both are gated in TASK-010. Current label: **source-wired**, not **runtime-verified**.
