---
id: TASK-007
feature: FEAT-001
title: Public API and security controls
status: completed
repository: the_visaguy
worktree: /home/shahzad/visa-tracker-worktrees/the_visaguy
owners: []
depends_on:
  - TASK-005
  - TASK-006
  - ADR-005
expected_files:
  - the_visaguy/the_visaguy/visa_tracking/services/__init__.py
  - the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/status_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/session_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/rate_limit_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/audit_service.py
  - the_visaguy/the_visaguy/visa_tracking/services/response_service.py
  - the_visaguy/the_visaguy/visa_tracking/api/verification.py
  - the_visaguy/the_visaguy/visa_tracking/api/status.py
  - the_visaguy/the_visaguy/visa_tracking/utils/constants.py
  - the_visaguy/the_visaguy/visa_tracking/utils/security.py
  - the_visaguy/the_visaguy/doctype/visa_tracking_application/test_visa_tracking_application.py
  - the_visaguy/the_visaguy/doctype/visa_tracker_settings/test_visa_tracker_settings.py
  - ongoing/visa-tracking-implementation/05f-task-007-implementation.md
created: 2026-07-21
updated: 2026-07-21
---

# TASK-007: Public API and security controls

## Objective

Implement the guest-accessible public verification and status API surface in `the_visaguy` for FEAT-001. The API must use an HMAC lookup over normalized passport number + date of birth, issue short-lived opaque Redis sessions, enforce rate limiting and temporary lockout, restrict CORS to the approved frontend origin, emit PII-free audit events, and return a strictly allowlisted, masked response. This task is backend-only; the frontend SPA flow is TASK-009.

## Context

FEAT-001 exposes a public visa-status lookup where a client proves weak knowledge of passport number and date of birth. ADR-005 records the accepted security model: HMAC lookup, opaque Redis sessions, generic failures, abuse controls, CORS restriction, response masking, and no PII in logs or URLs.

TASK-005 delivers the `Visa Tracking Application` schema with `verification_lookup_hash`, `lookup_hash_version`, cached settings, and the HMAC lookup seam. TASK-006 delivers the lifecycle service that keeps `current_status`, `status_updated_on`, and the status log consistent. TASK-007 builds the public API and all security controls on top of those services without changing lifecycle ownership.

All implementation happens in the `the_visaguy` feature worktree on branch `feat/visa-tracker`. Runtime validation runs only on a dedicated isolated test site; the active `visaguy` site must not be migrated or tested.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `tasks/ready/visa-tracking/TASK-005-tracking-data-model-and-settings.md`
- `tasks/ready/visa-tracking/TASK-006-tracking-lifecycle-and-status-sync.md`
- Feature worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`
- Installed Frappe apps on site `visaguy`, including `the_visaguy`
- Redis instance used by the bench for queues and sessions
- Frappe 15 / Python 3.10 runtime

## Required behaviour

### 1. Repository and worktree discipline

1.1. Work only in `/home/shahzad/visa-tracker-worktrees/the_visaguy` on branch `feat/visa-tracker`. Do not modify the original `the_visaguy` checkout.

1.2. Do not push to any Git remote.

### 2. HMAC lookup hash (reuse and harden from TASK-005)

2.1. The lookup hash must be HMAC-SHA256 over a canonical representation of `passport_number + date_of_birth`. Use the seam `visa_tracking.services.lookup_service.compute_lookup_hash(passport_number, date_of_birth)` delivered by TASK-005 and ensure it:

- normalizes the passport number by uppercasing and stripping whitespace and separators,
- normalizes the date of birth to ISO `YYYY-MM-DD` regardless of input format,
- uses the configuration key `visa_tracker_lookup_hmac_key` from `frappe.conf`,
- raises `frappe.ValidationError` when the key is missing and `raise_on_missing=True`,
- returns a stable `(hash, version)` tuple where `version` is a module constant (for example `v1`) supporting future algorithm rotation.

2.2. The HMAC key must exist only in site config/environment. Do not store it in `Visa Tracker Settings`, fixtures, code, or repository files. Record only the key name in documentation.

2.3. Plain SHA, unsalted hashes, or reversible encodings of passport+DOB are prohibited.

### 3. Guest verification API

3.1. Provide a whitelisted Guest method at:

```text
the_visaguy.visa_tracking.api.verification.verify_identity
```

Exposed as `frappe.whitelist(allow_guest=True)`.

3.2. HTTP method: `POST` only. Reject `GET` and other methods.

3.3. Request body (JSON):

```json
{
  "passport_number": "string",
  "date_of_birth": "string"
}
```

Both fields are required and must be non-empty strings. Do not accept query parameters, form-encoded bodies, or URL path segments for these values.

3.4. CORS enforcement:

- Read `Visa Tracker Settings.frontend_base_url`.
- Reject requests whose `Origin` header does not exactly match the configured base URL, unless running in a dedicated local development mode that is itself origin-restricted.
- Wildcard (`*`) or `null` origins must be rejected.
- Return the same generic failure used for invalid passport/DOB on CORS rejection; do not reveal that the failure was CORS.

3.5. Rate limiting and lockout:

- Identify the client by a composite key of `origin scope + source IP + lookup target bucket` using Frappe's request context (`frappe.local.request_ip` and the request environment).
- Track failed verification attempts in Redis with a key scoped to `visa_tracker:failed:<bucket>`.
- After `Visa Tracker Settings.maximum_failed_attempts` failures (default 5) within the lockout window, reject further attempts for `lockout_minutes` (default 15) with the same generic failure.
- A successful verification does not reset the failure counter; the counter expires with its TTL. The implementation may choose to reset on success only if it preserves bounded lockout semantics; document the chosen behavior.
- Use deterministic test hooks so tests can advance or inspect counters without waiting real time.

3.6. Verification flow:

1. Validate CORS.
2. Validate request shape and required fields.
3. Check rate-limit/lockout state; if locked out, return generic failure.
4. Compute `compute_lookup_hash(passport_number, date_of_birth)`.
5. Query `Visa Tracking Application` for `tracking_enabled = 1`, `application_closed != 1`, and `verification_lookup_hash = <hash>`.
6. If no record is found, increment the failure counter and return the generic failure.
7. If found, create a short-lived opaque session token, store it in Redis bound to the tracking application and settings-derived TTL, and return only the token.

3.7. Generic failure response (HTTP 200 with constant shape):

```json
{
  "success": false,
  "message": "Unable to verify. Please check your details and try again.",
  "data": null
}
```

The message must be configurable through `Visa Tracker Settings.generic_failure_message` with a safe default. The same JSON shape is returned for:

- missing/invalid request fields,
- CORS rejection,
- rate limit or lockout,
- non-existent passport/DOB combination,
- closed or disabled tracking record,
- unexpected server errors.

3.8. Success response (HTTP 200):

```json
{
  "success": true,
  "message": "Verification successful.",
  "data": {
    "session_token": "<opaque token>"
  }
}
```

3.9. Audit logging:

- Log every verification attempt to a server-side `Visa Tracker Audit Log` (DocType or structured log) with: timestamp, endpoint, origin, IP hash (not raw IP), success boolean, failure reason category, and tracking application reference only on success.
- Never log passport number, DOB, full lookup hash, or session token value.
- On success, log a redacted event such as `verification_succeeded`.
- On generic failure, log a redacted event such as `verification_failed` with a reason category like `not_found`, `cors`, `rate_limited`, `invalid_request`, or `error`.

### 4. Guest status API

4.1. Provide a whitelisted Guest method at:

```text
the_visaguy.visa_tracking.api.status.get_tracking_status
```

Exposed as `frappe.whitelist(allow_guest=True)`.

4.2. HTTP method: `POST` only. Reject `GET`.

4.3. Request body (JSON):

```json
{
  "session_token": "string"
}
```

4.4. CORS enforcement identical to the verification API.

4.5. Session resolution:

- Look up the Redis key for the supplied session token.
- If missing, expired, or tampered, return the generic failure.
- Load the referenced `Visa Tracking Application`.
- If the application is disabled or closed, return the generic failure.
- If session semantics require single-use, delete the Redis key after successful resolution and return generic failure on reuse; otherwise refresh the TTL up to the configured maximum. Default: bounded, refreshable session with explicit maximum lifetime.

4.6. Response allowlist and masking:

Success response (HTTP 200):

```json
{
  "success": true,
  "message": "Status retrieved.",
  "data": {
    "applicant_name_masked": "J****e",
    "passport_number_masked": "A1****23",
    "destination": "United Arab Emirates",
    "visa_type": "Tourist Visa",
    "current_status": "Working on Your Application",
    "public_message": "We are preparing your application for submission.",
    "last_updated": "2026-07-21T09:30:00Z",
    "timeline": [
      {
        "status": "Application Received",
        "message": "Your application has been received.",
        "effective_on": "2026-07-18T10:00:00Z",
        "icon": "inbox"
      }
    ],
    "support_link": "https://example.com/support"
  }
}
```

Masking rules:

- Applicant name: show first character and last character, mask the middle with `*` to a fixed length (for example 4 asterisks). For a single name or very short name, still produce a masked constant shape.
- Passport number: show the first two and last two characters, mask the middle with `*` to a fixed length (for example 4 asterisks).
- If applicant name is blank, return a masked placeholder such as `*****` instead of an empty string.

4.7. Response exclusions:

The status API must never return:

- DOB,
- full passport number,
- passport file URLs or file names,
- MRZ text or OCR output,
- internal document names,
- Lead/Customer/PF identifiers,
- internal notes, employee names, authority documents, payment data, processing errors,
- session token value after the initial verification response,
- any field whose value is `None` where a constant-shape placeholder can be returned instead.

4.8. Constant-shape behavior:

- The success JSON schema must be identical whether the case has 0 timeline entries or the configured maximum.
- Missing optional values must be returned as empty strings or empty arrays, not `null`, so the SPA cannot infer case existence from field presence.
- History is limited to `Visa Tracker Settings.status_history_limit` (default 20) newest-first.

4.9. Audit logging:

- Log `status_fetched` with timestamp, endpoint, origin, IP hash, and tracking application reference.
- Never log the session token value or full response payload.

### 5. Opaque Redis sessions

5.1. Session token generation:

- Use `secrets.token_urlsafe(32)` or equivalent cryptographically secure random source.
- Token length must be at least 32 bytes of entropy.
- Do not encode any case identifier, passport data, or claims in the token.

5.2. Redis storage:

- Key: `visa_tracker:session:<token>`.
- Value: JSON containing at minimum `tracking_application` reference and `created_at` timestamp.
- TTL: `session_expiry_minutes * 60` seconds (default 15 minutes), bounded by a module constant maximum (for example 60 minutes).
- Use the same Redis connection Frappe uses for queues (`frappe.cache()` or `frappe.get_cache()`), or an explicitly configured Redis URL. Do not fall back to an unbounded or separate unauthenticated Redis.

5.3. Session lifecycle:

- A session is created only on successful verification.
- A session may be refreshable: each successful `get_tracking_status` call resets TTL up to a hard maximum total lifetime of `max_session_lifetime_minutes` (default 60), after which a new verification is required.
- A session may optionally be single-use; if so, mark the Redis key with `single_use: true` and delete it after the first successful status fetch. The default must be refreshable, not single-use, unless product decision changes.
- Explicit logout or session invalidation is not required for the first release.

5.4. No session state in the browser:

- The API must not set cookies for the session token.
- The API must not read session token from cookies.
- The frontend is responsible for keeping the token only in memory during the SPA session (TASK-009).

### 6. Rate limiting, lockout, and audit service modules

6.1. `visa_tracking.services.rate_limit_service` must provide:

- `is_allowed(client_key: str) -> bool`
- `record_failure(client_key: str) -> None`
- `get_failure_count(client_key: str) -> int`
- `reset_failures(client_key: str) -> None` (for tests and safe admin use)
- `get_lockout_remaining_seconds(client_key: str) -> int`

All functions must be testable with a configurable Redis backend and deterministic TTLs.

6.2. `visa_tracking.services.audit_service` must provide:

- `log_verification_attempt(success: bool, reason: str, tracking_application=None)`
- `log_status_fetch(tracking_application=None)`
- Helpers to hash the client IP for privacy (for example HMAC-SHA256 with a per-site audit key or stable salt from site config).
- Never write raw passport, DOB, token, or full lookup hash.

6.3. Audit records must be append-only and not editable by `Visa Tracker Operator`. System Manager may read and delete for retention only.

### 7. CORS and request validation

7.1. `visa_tracking.utils.security` must provide:

- `validate_cors(origin: str) -> bool`
- `get_approved_origin() -> str`
- `reject_unsafe_request()` raising a generic exception mapped to the generic failure response.

7.2. Reject requests with:

- content types other than `application/json` for POST bodies,
- bodies larger than a module constant (for example 16 KB),
- suspicious or non-JSON payloads.

### 8. Deterministic security tests

8.1. Tests run only on a dedicated isolated test site, never on `visaguy`.

8.2. Use only synthetic/fake passport numbers and DOB values.

8.3. Test cases must include:

- Valid passport+DOB returns a 200 success with an opaque token and no other data.
- Invalid passport+DOB returns the same generic failure with HTTP 200.
- Missing `passport_number` or `date_of_birth` returns the generic failure.
- CORS rejection returns the generic failure; do not expose CORS-specific error text.
- Disallowed origin cannot call the API.
- After `maximum_failed_attempts` failures, the next request is locked out and returns generic failure.
- Lockout expires correctly when TTL is manipulated in tests.
- Valid session token returns the allowlisted, masked status response.
- Invalid/expired session token returns the generic failure.
- Session refresh/single-use behavior is deterministic (match the chosen default).
- Masking produces constant-shape strings regardless of input length.
- Response does not contain DOB, full passport number, internal identifiers, or `null` shape leaks.
- No passport number, DOB, full hash, or session token appears in Frappe error logs, response logs, or audit records.
- Audit log contains redacted success/failure categories.

8.4. Provide a test helper that creates a `Visa Tracking Application` with a known fake hash so tests can exercise the API without knowing the real HMAC key.

### 9. API access boundary

9.1. The public SPA may call only the two whitelisted methods in `the_visaguy`.

9.2. Direct `/api/resource/Visa Tracking Application`, `/api/resource/Passport Extraction`, `/api/resource/Visa Tracking Status Log`, or any other internal DocType endpoint is prohibited for Guest.

9.3. No internal DocType permissions are granted to Guest for tracking or extraction records.

## Constraints

- Work only in `/home/shzd/Projects/workspaces/visaguy_workspace` and the `the_visaguy` feature worktree at `/home/shahzad/visa-tracker-worktrees/the_visaguy`.
- Do not modify `processflo`, `fileflo`, `passport_extractor`, or `visa_tracker` source in this task.
- Do not implement OCR, MRZ parsing, FileFlo queued inspection, or full lifecycle synchronization (TASK-006 owns lifecycle).
- Do not run migrations or tests on site `visaguy`. Use a dedicated isolated test site when available; otherwise mark runtime validation deferred to TASK-010.
- Do not commit secrets, production data, passport samples, or sensitive raw data.
- Do not push to any Git remote.
- Do not require or run `bench build --app the_visaguy` unless the bench Node runtime issue recorded in TASK-001 is resolved.

## Exclusions

- Frontend SPA screens and session-in-memory handling (TASK-009).
- Tracking lifecycle and status synchronization (TASK-006).
- End-to-end verification, production migration, and rollout (TASK-010).
- Runtime verification blocked by missing `root_password` or missing dedicated test site; defer to TASK-010.

## Expected changes

- `the_visaguy/the_visaguy/visa_tracking/services/lookup_service.py` (extend TASK-005 seam with key-version support and canonicalization)
- `the_visaguy/the_visaguy/visa_tracking/services/session_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/rate_limit_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/audit_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/response_service.py`
- `the_visaguy/the_visaguy/visa_tracking/services/status_service.py` (extend public timeline helper)
- `the_visaguy/the_visaguy/visa_tracking/api/verification.py`
- `the_visaguy/the_visaguy/visa_tracking/api/status.py`
- `the_visaguy/the_visaguy/visa_tracking/utils/security.py`
- `the_visaguy/the_visaguy/visa_tracking/utils/constants.py` (session bounds, rate-limit constants)
- `the_visaguy/the_visaguy/doctype/visa_tracking_application/test_visa_tracking_application.py` (security test additions)
- `the_visaguy/the_visaguy/doctype/visa_tracker_settings/test_visa_tracker_settings.py` (settings validation additions)
- `the_visaguy/hooks.py` (whitelist or module registration only if required)
- `ongoing/visa-tracking-implementation/05f-task-007-implementation.md`

## Validation

### Static validation

- [ ] Each new `.py` file compiles with `python -m py_compile` in the bench Python environment.
- [ ] `the_visaguy.__file__` resolves inside the feature worktree when the worktree is first on `PYTHONPATH`.
- [ ] No Guest permission is granted to `Visa Tracking Application`, `Passport Extraction`, `Visa Tracking Status Log`, or internal DocTypes.
- [ ] No raw passport number, DOB, or session token is returned by the verification or status API source paths.
- [ ] No HMAC key value is present in source, fixtures, or test files.
- [ ] `git status --short` in the feature worktree is clean after all changes are committed locally.

### Runtime validation (defer if test site unavailable)

- [ ] A dedicated test site exists and has `the_visaguy` installed.
- [ ] `bench --site <test-site> migrate` succeeds with the new API and service modules.
- [ ] All security tests from Section 8 pass.
- [ ] No migration or test runs on site `visaguy`.

### Runtime deferral note

If the bench still lacks a configured `root_password` key or no dedicated test site is available, record runtime validation as deferred to TASK-010. Static validation and local commits are still required for this task.

## Definition of done

- Guest verification and status APIs are implemented as whitelisted methods in `the_visaguy`.
- HMAC lookup over normalized passport+DOB uses a site-config-only key and supports versioned rotation.
- Short-lived opaque Redis sessions are created on successful verification and enforce TTL/single-use or refreshable semantics.
- Rate limiting, temporary lockout, CORS restriction, PII-free audit logging, response masking, and constant-shape behavior are implemented and tested.
- Static validation passes.
- Changes are committed locally in the feature worktree; no push is performed.
- `visaguy` is not migrated or tested on.
- Implementation evidence is recorded in `ongoing/visa-tracking-implementation/05f-task-007-implementation.md`.
- TASK-007 is ready for TASK-009 to consume the public APIs and for TASK-010 to run end-to-end security validation.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Worktree mismatch**: the feature worktree path or branch differs from `/home/shahzad/visa-tracker-worktrees/the_visaguy` / `feat/visa-tracker`.
2. **Missing dependency**: TASK-005 or TASK-006 schema/seams are not available in the worktree.
3. **Redis unavailable**: the bench Redis cannot be reached through Frappe's cache API and no safe session backend exists.
4. **Missing architecture decision**: an implementation question arises that is not answered by FEAT-001, ADR-005, or `01-architecture-and-data-model.md`.
5. **Permission denial**: any required repository, bench, or site operation is denied by host policy or user approval.
6. **Unsafe test-site demand**: a stakeholder requires running migrations or tests on `visaguy` instead of a dedicated isolated test site.
