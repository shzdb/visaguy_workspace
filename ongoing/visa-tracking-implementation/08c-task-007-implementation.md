# TASK-007 Implementation Report — Public API and Security Controls

> Date: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-007 — Public API and security controls
> Repository: `the_visaguy`
> Worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy` (branch `feat/visa-tracker`)

## Verdicts

- **the_visaguy start SHA:** `9222302035c2c077ed91662cc49af784dac3119f` (clean at TASK-006 HEAD; entry gate satisfied)
- **the_visaguy final SHA:** `d20cc6d49cfae6c47749f8b5a94df0fa38546979` (`feat: add secure public tracking APIs`)
- **API/security static verdict:** pass — 199 tests collected (197 pass, 10 deferred-integration skips, 2 pre-existing site-bound errors identical to the TASK-006 baseline), all static gates green.
- **Runtime verdict:** deferred — no dedicated test site; `root_password` still absent from bench `common_site_config.json`. Deferred to TASK-010.
- **TASK-007 verdict:** static-complete, runtime-deferred.

## Entry gate evidence

- Worktree HEAD was `9222302…` on `feat/visa-tracker` with `git status --short` empty before any edit (matches the TASK-006 report).
- Single authorized commit only; no push, no other git mutation; `passport_extractor`, `processflo`, `fileflo`, frontend, and original checkouts untouched; site `visaguy` never touched.

## Endpoints and exact schemas

All three methods are `frappe.whitelist(allow_guest=True, methods=["POST"])` and return a raw werkzeug `Response` (Frappe's `handler.py` passes `Response` instances through unwrapped — source-verified), so the wire schema is exactly:

### `the_visaguy.visa_tracking.api.verification.verify_identity`

Request (JSON body only, `application/json`, ≤ 16 KB, query/form never consulted):

```json
{ "passport_number": "string", "date_of_birth": "string" }
```

Success (HTTP 200, plus `Access-Control-Allow-Origin: <approved origin>` and `Vary: Origin`):

```json
{ "success": true, "message": "Verification successful.", "data": { "session_token": "<opaque token>" } }
```

Generic failure (HTTP 200, constant shape for every failure mode — invalid request, CORS, disabled, rate-limited/lockout, not-found, closed/disabled record, server error):

```json
{ "success": false, "message": "Unable to verify. Please check your details and try again.", "data": null }
```

The message is configurable via `Visa Tracker Settings.generic_failure_message` with the safe default above. On lockout the identical body is returned with a `Retry-After: <seconds>` header. Failure bodies were asserted byte-identical across `not_found`, `invalid_request`, and `disabled` reasons in tests.

### `the_visaguy.visa_tracking.api.status.get_tracking_status`

Request: `{ "session_token": "string" }`. Success (HTTP 200, strict allowlist, constant shape — empty strings/arrays, never `null`):

```json
{
  "success": true,
  "message": "Status retrieved.",
  "data": {
    "applicant_name_masked": "J****e",
    "passport_number_masked": "P0****00",
    "destination": "United Arab Emirates",
    "visa_type": "Tourist Visa",
    "current_status": "Working on Your Application",
    "public_message": "We are preparing your application for submission.",
    "last_updated": "2026-07-21T09:30:00",
    "timeline": [
      { "status": "Application Received", "message": "Your application has been received.", "effective_on": "2026-07-18T10:00:00", "icon": "inbox" }
    ],
    "support_link": "https://example.com/support"
  }
}
```

Failures: the same generic failure shape as verification (HTTP 200). No 401/410 semantics exist in the TASK-007 contract; every failure is the constant HTTP-200 generic shape (asserted in tests).

### `the_visaguy.visa_tracking.api.status.logout`

Request: `{ "session_token": "string" }`. Deletes the Redis session (tolerant of unknown tokens). Response is the constant `{ "success": true, "message": "Logged out.", "data": null }` whether or not the token existed (non-enumerating). Note: TASK-007 §5.3 marked logout "not required for the first release", but the dispatch prompt explicitly ordered "verification/status/logout APIs" — implemented per the prompt; deviation recorded below.

## Security-control matrix

| Control | Implementation | Evidence |
|---|---|---|
| HMAC lookup | `lookup_service.compute_lookup_hash(_candidates)`: HMAC-SHA256 over `canonical_passport | canonical_dob`; passport uppercased with whitespace/separators (`[\s\-_.]+`) stripped; DOB normalized to ISO `YYYY-MM-DD` via `frappe.utils.getdate` (accepts strings/`date`/`datetime`; blank/invalid → `frappe.ValidationError` → generic failure) | pure tests (source-wired) |
| Key storage | Key value only in `frappe.conf` under key name `visa_tracker_lookup_hmac_key`; name-only in code; missing key → `frappe.ValidationError` when `raise_on_missing=True`; plain SHA/unsalted prohibited | source-wired, secret scan pass |
| Version rotation | `DEFAULT_LOOKUP_HASH_VERSION = "v1"`; `ACTIVE_LOOKUP_HASH_VERSIONS` tuple; verification queries `verification_lookup_hash in <candidates>` so old-version records survive rotation windows | pure tests (source-wired) |
| Opaque sessions | `session_service`: `secrets.token_urlsafe(32)` (≥ 32 bytes entropy, no claims/identifiers); Redis key `visa_tracker:session:<token>` via `frappe.cache()`; value = `{tracking_application, created_at}` only | pure tests (source-wired) |
| Session lifecycle | Refreshable sliding TTL (`session_expiry_minutes`, default 15) bounded by hard max lifetime (`max_session_lifetime_minutes`, default 60); past max lifetime session deleted, re-verification required; logout deletes key; no cookies set or read | pure tests incl. 60-minute refresh sequence (source-wired) |
| Rate limit / lockout | `rate_limit_service`: Redis key `visa_tracker:failed:<bucket>`; composite client key = keyed-HMAC buckets of origin scope + source IP + lookup target (no raw IP/passport/DOB/token in any key); lockout after `maximum_failed_attempts` (default 5) for `lockout_minutes` (default 15); **success does not reset the counter**; fixed (non-sliding) window TTL preserved on increments; `is_allowed`/`record_failure`/`get_failure_count`/`reset_failures`/`get_lockout_remaining_seconds` all provided; locked-out requests short-circuit before any DB query | pure tests incl. TTL manipulation, recovery, concurrent-key evaluation (source-wired) |
| CORS | `utils.security.validate_cors`: exact match to `Visa Tracker Settings.frontend_base_url` (trailing slash normalized both sides); `*`/`null`/missing rejected; empty config fails closed; opt-in localhost dev mode via config key name `visa_tracker_allow_localhost_origins` restricted to localhost/127.0.0.1/::1; CORS rejection returns the generic failure with no CORS-specific signal and no `Access-Control-Allow-Origin` header | pure tests (source-wired) |
| Request validation | JSON-only content type, 16 KB body cap, object-only JSON; query params and form bodies never read; non-POST rejected by whitelist `methods=["POST"]` | pure tests + registry assertion (source-wired) |
| Response allowlist/masking | `response_service`: exact 9-key payload + 4-key timeline entries; name mask `first + "****" + last` (blank → `*****`, len-1 → `X****`); passport mask `first2 + "****" + last2` (<5 chars → `********`); missing optionals → `""`/`[]`, never `null`; no DOB, full passport, file URLs, MRZ/OCR, internal names, Lead/Customer/PF IDs, notes, correction reasons, hashes, or token (beyond initial verification) | pure tests incl. serialized-payload forbidden-value scans (source-wired) |
| Audit trail | New `Visa Tracker Audit Log` DocType (append-only; System Manager read+delete only; no Operator/Manager/Guest access); events `verification_succeeded`/`verification_failed` (reason categories `not_found`/`cors`/`rate_limited`/`invalid_request`/`disabled`/`error`), `status_fetched`, `session_closed`; IP stored only as keyed HMAC (`visa_tracker_audit_hmac_key`, falling back to the lookup key; never unsalted, empty when unconfigured); tracking application reference only on success; audit insert failures swallowed with a static PII-free `log_error` | pure tests + schema assertions (source-wired) |
| Operational errors | All `frappe.log_error` call sites carry static titles + endpoint constants only (grep-verified); unexpected errors → generic failure | static scan (source-wired) |
| Guest boundary | No Guest role in any tracking DocType JSON or `custom_docperm.json` (test-asserted); no Guest DocType resource access introduced; whitelisted methods are the only public surface; lifecycle stays in TASK-006 services — API layer is authorization/validation/serialization only | pure tests + fixture scan (present/source-wired) |
| Lifecycle ownership | Status content resolved read-only via `status_service.get_public_display_timeline` (visible rows only, settings `status_history_limit`, internal fields never selected) and settings/DocType reads; no status writes in API code | source-wired |

## Configuration key names (never values)

- `visa_tracker_lookup_hmac_key` — HMAC key for lookup hashing (pre-existing TASK-005 key name).
- `visa_tracker_audit_hmac_key` — optional dedicated audit IP-hashing key; falls back to the lookup key.
- `visa_tracker_allow_localhost_origins` — opt-in localhost-only CORS override for dedicated local development.

New `Visa Tracker Settings` fields: `max_session_lifetime_minutes` (default 60), `generic_failure_message` (safe default), `support_link`. Settings controller now requires an explicit http(s) `frontend_base_url` (no wildcards) when public tracking is enabled, validates the new bounds, and rejects a blank generic failure message.

## Changed files (commit `d20cc6d`)

New:

- `the_visaguy/visa_tracking/api/__init__.py`, `api/verification.py`, `api/status.py`
- `the_visaguy/visa_tracking/services/session_service.py`, `rate_limit_service.py`, `audit_service.py`, `response_service.py`
- `the_visaguy/visa_tracking/utils/security.py`
- `the_visaguy/doctype/visa_tracker_audit_log/{__init__.py,visa_tracker_audit_log.json,visa_tracker_audit_log.py}`
- `the_visaguy/visa_tracking/tests/test_session_service.py`, `test_rate_limit_service.py`, `test_response_service.py`, `test_security_utils.py`, `test_audit_service.py`, `test_public_api.py`

Modified:

- `the_visaguy/visa_tracking/services/lookup_service.py` — canonicalization hardening + `compute_lookup_hash_candidates` (signature of `compute_lookup_hash` unchanged; TASK-006 lifecycle caller unaffected).
- `the_visaguy/visa_tracking/services/status_service.py` — added `get_public_display_timeline`.
- `the_visaguy/visa_tracking/utils/constants.py` — session/rate-limit/mask/message/key-name constants.
- `the_visaguy/visa_tracking/utils/settings.py` — `max_session_lifetime_minutes` bounds; `get_audit_hash_key`.
- `the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.json` — three new fields.
- `the_visaguy/doctype/visa_tracker_settings/visa_tracker_settings.py` — public-tracking security validation.
- `the_visaguy/doctype/visa_tracker_settings/test_visa_tracker_settings.py` — skip-guarded settings additions.
- `the_visaguy/doctype/visa_tracking_application/test_visa_tracking_application.py` — skip-guarded security additions incl. §8.4 known-fake-hash helper stub.
- `the_visaguy/visa_tracking/tests/test_lookup_service.py` — pure canonicalization/rotation tests appended.

`the_visaguy/hooks.py` intentionally unchanged: whitelisted methods resolve by dotted path; no registration needed.

## Tests and static gates

All run on the bench host with worktree-first `PYTHONPATH` (`the_visaguy` wt : `passport_extractor` wt : `bench/apps/frappe`) and bench Python 3.10.

| Gate | Result |
|------|--------|
| Combined pure suite at final SHA | **199 tests: 197 pass, 10 skipped** (deferred integration classes), **2 errors** — the pre-existing site-bound `test_lookup_service.TestLookupService` / `test_settings.TestSettings` `IncorrectSitePath` errors, byte-identical to the TASK-006 baseline (no new site-bound errors introduced) |
| New pure tests (sessions, rate limit, responses, CORS/validation, audit, public API, lookup canonicalization) | 117 new tests collected (82 → 199), all green; covers valid verification, generic mismatch/not-found/disabled/malformed equivalence, CORS allow/deny/wildcard/null, lockout after N failures + TTL recovery + Retry-After, HMAC versioning, opaque token entropy/opacity, TTL expiry, hard max lifetime, logout invalidation, idempotent refresh, masking constant shapes, response allowlist/exclusions/null-free shape, timeline bound, audit redaction, missing-key fail-safe, POST-only + guest registration, no-Guest schema/fixture boundary |
| `py_compile` on all new/modified `.py` | Pass |
| `the_visaguy.__file__` resolves inside feature worktree | Pass |
| Whitelist resolution: all 3 dotted paths import, callable, in `frappe.guest_methods`, `methods == ["POST"]` | Pass (importlib check) |
| DocType/fixture JSON validity (settings + audit log) | Pass |
| Dependency scan: no `fileflo`/`processflo`/`passport_extractor` imports in new modules | Pass |
| Secret scan: no key values; config key names only; only synthetic in-memory values (`P0000000`, `1990-01-01`, `203.0.113.10`, `synthetic-*`) in tests | Pass |
| PII/log scan: `passport_number`/`date_of_birth` appear only as field reads feeding HMAC or masking; all `log_error` sites static | Pass |
| `git diff --check` | Pass |
| Full diff review | TASK-007 scope only; TASK-005/006 seams preserved |
| `git status --short` after commit | Clean |

## Deferred runtime checks (TASK-010)

- Dedicated test site creation (blocked: bench `common_site_config.json` has no `root_password` key) and `bench --site <test-site> migrate` with the new `Visa Tracker Audit Log` DocType and settings fields.
- Skip-guarded `FrappeTestCase` integration classes now written in all six new pure-test modules plus both DocType test files (all `SkipTest`-guarded; must never run against `visaguy`): end-to-end verification → session → status round trip, lockout against real Redis, Guest `/api/resource/*` denial, audit row inspection, settings validation.
- No migration, test, or build ran on site `visaguy`.

## Evidence labels

- **source-wired** — whitelisted methods, service call chains, security controls, and response schemas evidenced in committed code and pure tests.
- **present** — DocType/fixture permission surfaces, settings fields consumed.
- **configured-unverified** — `visa_tracker_lookup_hmac_key`, `visa_tracker_audit_hmac_key`, `visa_tracker_allow_localhost_origins` config keys (names only); `Visa Tracker Settings` values.
- **runtime-verified** — SSH access, worktree state, Frappe 15 handler/whitelist/Redis-wrapper source behavior, pure-test and static-gate execution. No runtime Frappe site behavior verified (deferred).

## Deviations

- Report written to `ongoing/visa-tracking-implementation/08c-task-007-implementation.md` per the dispatch prompt; the task file's `expected_files` lists `05f-task-007-implementation.md`. Discrepancy noted; lifecycle files not moved (coordinator's responsibility).
- **Logout API added**: the dispatch prompt explicitly ordered "verification/status/logout APIs" although TASK-007 §5.3 marks logout "not required for the first release". Implemented as `api.status.logout` with a constant non-enumerating response and `session_closed` audit event.
- **New `Visa Tracker Audit Log` DocType** (not in `expected_files`): §3.9 allows "DocType or structured log" and §6.3 requires append-only records not editable by `Visa Tracker Operator` with System Manager read/delete for retention — a DocType with System-Manager-read/delete-only permissions is the cleanest fulfillment.
- **Three new `Visa Tracker Settings` fields** (`max_session_lifetime_minutes`, `generic_failure_message`, `support_link`) added beyond the listed expected files; required by §3.7, §4.6, and §5.3.
- Failure-counter semantics per §3.5 default: success does **not** reset the counter; fixed-window TTL (documented choice).
- CORS comparison normalizes a single trailing slash on both sides (documented loosening of "exact match"); everything else is strict.
- The lookup hash is computed before the lockout check (§3.6 lists lockout first) because the composite client key requires the target bucket; no DB work happens before the lockout gate.
- `last_updated`/`effective_on` are emitted as ISO-8601 strings without a timezone suffix (naive server time); constant shape guaranteed.
- No 401/410 statuses: the contract specifies the constant HTTP-200 generic failure for every failure mode; the prompt's "401/410 semantics as specified" resolves to "none specified".
