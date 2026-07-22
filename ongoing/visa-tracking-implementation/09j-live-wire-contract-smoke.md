# Live Wire-Contract Smoke — Public Tracking API vs Frontend Contract

> Date: 2026-07-22
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Phase: TASK-010 runtime — live HTTP wire-contract verification (verification-only; no code changed anywhere)
> Backend: site `visa-tracker-test.localhost` on `erpcode.tridz.in`, app code from worktree `/home/shahzad/visa-tracker-worktrees/the_visaguy` @ `910914e2c8286a356af5a37e9d7e8b14d2e48545` (branch `feat/visa-tracker`, worktree-first `PYTHONPATH`)
> Contract under test (authoritative): `/home/shzd/Projects/tridz/visa_tracker/src/test/contract/wireContract.ts` @ `a6a07a9a`
> Backend contract docs: `tasks/completed/visa-tracking/TASK-007-public-api-and-security-controls.md`, `ongoing/visa-tracking-implementation/08c-task-007-implementation.md`
> Executor scope: read/probe/report only. No application repository, the frontend contract, the remote worktree, or any config was modified. Synthetic data only (`P0000000`/`1990-01-01`, `P9999999`, `P1234567`, "John Doe"; loopback-only HTTP).

**Verdict: the live HTTP wire surface matches the frontend contract on every probed field. Zero contract mismatches.** All three Guest endpoints, all envelopes, the 9-key status allowlist, the 4-key timeline item shape, masking, constant generic failure, non-enumerating logout, POST-only rejection, Guest resource denial, CORS allow/deny, and lockout with `Retry-After: 900` were exercised over real HTTP against real Redis and real MariaDB — **runtime-verified**.

---

## 1. Expected wire contract (as read from `wireContract.ts`)

Transport: all three endpoints are `POST`-only, request content-type `application/json`, at:

- `CONTRACT_VERIFY_PATH = /api/method/the_visaguy.visa_tracking.api.verification.verify_identity`
- `CONTRACT_STATUS_PATH = /api/method/the_visaguy.visa_tracking.api.status.get_tracking_status`
- `CONTRACT_LOGOUT_PATH = /api/method/the_visaguy.visa_tracking.api.status.logout`

verify request `{"passport_number": str, "date_of_birth": str}` →

- success: `{"success": true, "message": "Verification successful.", "data": {"session_token": str}}`
- failure (every failure mode): constant HTTP-200 `{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}` (`genericFailureEnvelope`; message configurable via settings, default matches).

status request `{"session_token": str}` → success `{"success": true, "message": "Status retrieved.", "data": {...}}` with EXACTLY these 9 keys (`STATUS_RESPONSE_KEYS`): `applicant_name_masked, passport_number_masked, destination, visa_type, current_status, public_message, last_updated, timeline, support_link`. Timeline items have EXACTLY keys (`TIMELINE_ITEM_KEYS`): `status, message, effective_on, icon`. Missing optional values are `""`/`[]`, never `null` (§4.8 constant-shape). Forbidden keys anywhere (`FORBIDDEN_STATUS_RESPONSE_FIELDS`): `date_of_birth, dob, passport_number, applicant_name, session_token, lookup_hash, verification_lookup_hash, lead, customer, process_file`. Failures: the same generic failure envelope.

logout request `{"session_token": str}` → constant `{"success": true, "message": "Logged out.", "data": null}` whether or not the token existed (non-enumerating).

Contract header constant: `CONTRACT_RETRY_AFTER_HEADER = "Retry-After"`; frontend mock uses `MOCK_RETRY_AFTER_SECONDS = 900`.

## 2. How the site was served

- Pre-check (`ps aux`): many other users' benches serve on loopback, but **no web process existed for `/home/shahzad/bench`** — only its three redis instances (13008/11008/12008). Nothing was disturbed.
- First attempt with `cwd=/home/shahzad/bench` failed: Frappe's logger opens `../logs/<name>.log` relative to cwd (FileNotFoundError `/home/shahzad/logs/database.log`). Corrected by running with `cwd=/home/shahzad/bench/sites`.
- Final serving command (runtime-verified):

```bash
cd /home/shahzad/bench/sites && \
PYTHONPATH=/home/shahzad/visa-tracker-worktrees/the_visaguy:/home/shahzad/visa-tracker-worktrees/fileflo:/home/shahzad/visa-tracker-worktrees/passport_extractor \
nohup ../env/bin/python -c "from werkzeug.serving import run_simple; from frappe.app import application; run_simple('127.0.0.1', 8899, application, threaded=True)" > /tmp/wire_serve.log 2>&1 &
```

- Bind: `127.0.0.1:8899` only (`ss -ltnp` confirmed). All probes used `curl -sS -i http://127.0.0.1:8899/...` with header `Host: visa-tracker-test.localhost`; happy-path probes also sent `Origin: https://tracker-test.example.com`.
- Sanity: `GET /` with the site Host header → `200` before any probing (runtime-verified).
- Server was killed after probing; port verified free (§7).

## 3. Seeded synthetic data (all synthetic; deleted afterwards)

Seed script `/tmp/seed_wire.py` (throwaway, since removed) run as `cd /home/shahzad/bench/sites && PYTHONPATH=<worktree-first> ../env/bin/python /tmp/seed_wire.py` with `frappe.init(site='visa-tracker-test.localhost', sites_path='.')`.

- `Passport Extraction` `PEX-2026-00003`: `passport_number=P0000000`, `date_of_birth=1990-01-01`, surname/given `Doe`/`John`, inserted as `Queued` (controller mandate) then `db.set_value` → `Verified`; mandatory `passport_file` satisfied by a synthetic `File` (`synthetic-wire-smoke.txt`, 47-byte placeholder text, not a passport).
- `Visa Tracking Application` `VTA-2026-00013`: `passport_extraction=PEX-2026-00003`, `applicant_display_name="John Doe"`, `destination="United Arab Emirates"`, `visa_type="Tourist Visa"`, `tracking_enabled=1`, `application_closed=0`, `current_status=WORKING_ON_APPLICATION`, `current_public_message="We are preparing your application for submission."`, `status_updated_on=<t2>`, `verification_lookup_hash` computed via `lookup_service.compute_lookup_hash` (present, version `v1`) — reload-verified.
- Two `Visa Tracking Status Log` rows (`visible_to_client=1`): `VTL-2026-00014` `APPLICATION_RECEIVED` @ `2026-07-19 19:32:39.826642`, message "Your application has been received."; `VTL-2026-00015` `WORKING_ON_APPLICATION` @ `2026-07-22 19:32:39.826642`, message "We are preparing your application for submission."
- Live `Visa Tracker Settings` read-back (runtime-verified): `enabled=1`, `enable_public_tracking=1`, `frontend_base_url='https://tracker-test.example.com'`, `session_expiry_minutes=15`, `max_session_lifetime_minutes=60`, `maximum_failed_attempts=5`, `lockout_minutes=15`, `status_history_limit=20`, `generic_failure_message='Unable to verify. Please check your details and try again.'` (identical to contract default), `support_link='https://tracker-test.example.com/support'`.
- Live `Visa Tracking Status` rows used: `APPLICATION_RECEIVED` (icon `inbox`), `WORKING_ON_APPLICATION` (icon `tool`) — both active.

## 4. Probe results L1–L9 (summary; raw evidence in Appendix A)

| Probe | Expectation | Result | Evidence |
|---|---|---|---|
| L1 verify happy path | 200 verify-success envelope + opaque token | **PASS** | `{"success": true, "message": "Verification successful.", "data": {"session_token": "tOQPLvXKdZi725Hg4b1ydADAxPL89Q9K6za809aeS7E"}}` — 43-char urlsafe token (32 bytes entropy). Redis session payload observed via helper: `{'tracking_application': 'VTA-2026-00013', 'created_at': ...}` — opaque, no identity data. |
| L2 verify wrong identity (`P9999999`) | constant-200 generic failure; no enumeration signal vs L1 | **PASS** | Byte-shape identical to `genericFailureEnvelope`; same HTTP 200; no distinguishing header/body signal. |
| L3 status with L1 token | exact 9-key allowlist, 4-key timeline items, masking, no forbidden fields, no nulls | **PASS** | See field-by-field table §5.2 — all match. |
| L4a status `{}` (missing token) | generic failure | **PASS** | 105-byte generic body, HTTP 200. |
| L4b status bogus token | generic failure | **PASS** | identical body. |
| L4c status expired session | generic failure | **PASS** | Helper set the real Redis session key TTL to 2s (`cache.set_value(key, payload, expires_in_sec=2)`); status with that token → generic failure. Confirmed genuine expiry, not an artifact: a *fresh* token issued and used immediately afterwards succeeded (see Appendix A.4 note). Helper-side "key still present after 4s" readings were Frappe's per-process `frappe.local.cache` memoization in the helper process, not Redis state (source-verified in `redis_wrapper.py`: `get_value` without `expires=True` memoizes in-process; each HTTP request is a fresh `frappe.local`). |
| L5a logout valid token | constant `{"success": true, "message": "Logged out.", "data": null}` | **PASS** | exact constant body. |
| L5b status reusing logged-out token | generic failure | **PASS** | generic failure envelope. |
| L5c logout never-existed token | same constant body (non-enumerating) | **PASS** | byte-identical to L5a. |
| L6 GET on all 3 endpoints | rejected | **PASS** | `403 FORBIDDEN` `frappe.exceptions.PermissionError: Not permitted` for verify, status, and logout (bodies identical framework error shape). See observation O2. |
| L7 GET `/api/resource/Visa Tracking Application` as Guest | denied, no data leak | **PASS** | `403 FORBIDDEN`, `"_error_message": "No permission for Visa Tracking Application"`; no rows returned. |
| L8a verify, `Origin: https://evil.example.com` | generic failure AND no permissive CORS header | **PASS** | 200 generic failure; **no** `Access-Control-Allow-Origin` header at all; no `Vary`. |
| L8b verify, allowed Origin | success + exact ACAO | **PASS** | `Access-Control-Allow-Origin: https://tracker-test.example.com`, `Vary: Origin` (exact origin echo, no wildcard). |
| L8c OPTIONS preflight | record actual | **RECORDED** | `200 OK`, `Content-Type: text/plain; charset=utf-8`, empty body, **no CORS headers** — see finding F1. |
| L8d verify, no `Origin` header | generic failure (missing origin rejected) | **PASS** | 200 generic failure. |
| L9 lockout, third passport `P1234567` (done LAST) | after 5 failures, attempts rejected with generic failure + `Retry-After` | **PASS** | Attempts 1–5: generic failure, no `Retry-After`. Attempts 6–7: identical generic failure **plus `Retry-After: 900`** (= `lockout_minutes=15` × 60; matches contract mock's 900). Body shape never changed. |

## 5. Field-by-field comparison

### 5.1 verify — success envelope (L1, L8b)

| Contract field | Expected | Actual (live) | Match |
|---|---|---|---|
| HTTP status | 200 | 200 | ✅ |
| `success` | `true` | `true` | ✅ |
| `message` | `"Verification successful."` | `"Verification successful."` | ✅ |
| `data` | object | object | ✅ |
| `data.session_token` | string (opaque) | `"tOQPLvXKdZi725Hg4b1ydADAxPL89Q9K6za809aeS7E"` (43-char urlsafe; redis payload contains only `tracking_application` + `created_at`) | ✅ |
| extra keys | none | none | ✅ |

### 5.2 generic failure envelope (L2, L4a, L4b, L4c, L5b, L8a, L8d, L9×7)

| Contract field | Expected | Actual (live) | Match |
|---|---|---|---|
| HTTP status | 200 (constant) | 200 in every failure probe | ✅ |
| `success` | `false` | `false` | ✅ |
| `message` | `"Unable to verify. Please check your details and try again."` | byte-identical string | ✅ |
| `data` | `null` | `null` | ✅ |
| shape constancy | byte-identical across failure modes | 105-byte body, identical across `not_found` (L2/L9), `invalid_request` (L4a/L4b), `expired session` (L4c), `logged-out session` (L5b), `cors` (L8a/L8d) | ✅ |
| enumeration signal L1 vs L2 | none | none (status, shape, headers except ACAO-echo on success are identical) | ✅ |

### 5.3 status — success envelope (L3)

Live body (verbatim):

```json
{"success": true, "message": "Status retrieved.", "data": {"applicant_name_masked": "J****e", "passport_number_masked": "P0****00", "destination": "United Arab Emirates", "visa_type": "Tourist Visa", "current_status": "Working on Your Application", "public_message": "We are preparing your application for submission.", "last_updated": "2026-07-22T19:32:39.826642", "timeline": [{"status": "Working on Your Application", "message": "We are preparing your application for submission.", "effective_on": "2026-07-22T19:32:39.826642", "icon": "tool"}, {"status": "Application Received", "message": "Your application has been received.", "effective_on": "2026-07-19T19:32:39.826642", "icon": "inbox"}], "support_link": "https://tracker-test.example.com/support"}}
```

| Contract field | Expected | Actual (live) | Match |
|---|---|---|---|
| `success` / `message` | `true` / `"Status retrieved."` | same | ✅ |
| key set of `data` | EXACTLY the 9 `STATUS_RESPONSE_KEYS` | exactly those 9, no more, no fewer | ✅ |
| `applicant_name_masked` | masked, e.g. `"J****e"` | `"J****e"` (raw "John Doe" absent) | ✅ |
| `passport_number_masked` | masked, e.g. `"P0****00"` | `"P0****00"` (raw `P0000000` absent) | ✅ |
| `destination` | string | `"United Arab Emirates"` | ✅ |
| `visa_type` | string | `"Tourist Visa"` | ✅ |
| `current_status` | string | `"Working on Your Application"` (display `status_name`) | ✅ |
| `public_message` | string | `"We are preparing your application for submission."` | ✅ |
| `last_updated` | ISO-ish string, non-empty | `"2026-07-22T19:32:39.826642"` (naive, microseconds — see O4) | ✅ |
| `timeline` | array, newest-first, ≥2 entries | 2 entries, newest-first | ✅ |
| timeline item keys | EXACTLY `status, message, effective_on, icon` | exactly those 4 in both items | ✅ |
| timeline `effective_on` | populated, ISO-ish | `"2026-07-22T19:32:39.826642"`, `"2026-07-19T19:32:39.826642"` — non-empty (D4 path working at 910914e) | ✅ |
| timeline `icon` | string | `"tool"`, `"inbox"` (from `Visa Tracking Status.display_icon`) | ✅ |
| `support_link` | string | `"https://tracker-test.example.com/support"` (settings value) | ✅ |
| null optional values | never `null` | no `null` anywhere in `data` | ✅ |
| forbidden fields | none of the 10 `FORBIDDEN_STATUS_RESPONSE_FIELDS` anywhere | none present (body scanned; raw DOB `1990-01-01`, raw passport, internal name `VTA-2026-00013`, hash, token all absent) | ✅ |

### 5.4 logout (L5a, L5c)

| Contract field | Expected | Actual (live) | Match |
|---|---|---|---|
| HTTP status | 200 | 200 | ✅ |
| body | `{"success": true, "message": "Logged out.", "data": null}` | byte-identical for both a real token and a never-existed token (57-byte body) | ✅ |
| invalidation | token dead after logout | L5b reuse → generic failure | ✅ |

### 5.5 Mismatches found

**None.** Every contract field, constant message, key set, and shape matched on the live wire.

## 6. Findings / observations (NOT contract mismatches)

- **F1 — CORS preflight is not answered with CORS headers (operational gap, runtime-verified).** `OPTIONS` on the verify endpoint returns `200 OK` `text/plain` empty body with **no** `Access-Control-Allow-Origin`/`Access-Control-Allow-Methods`/`Access-Control-Allow-Headers`. The actual POST responses carry the correct exact-origin `Access-Control-Allow-Origin` + `Vary: Origin` (L8b), and disallowed/missing origins get the generic failure with no ACAO (L8a/L8d) — the app-level control is correct. But a browser issuing a cross-origin `POST` with `Content-Type: application/json` always preflights first, and a preflight without ACAO makes the browser block the call. If the TASK-009 SPA is served from `https://tracker-test.example.com` while the API lives on another origin, live browser calls will fail unless the deployment puts a same-origin proxy in front or the preflight is answered. `wireContract.ts` says nothing about preflight, so this is not a contract mismatch; it is flagged for TASK-010 rollout planning.
- **O2 — Framework error surface on rejected requests (runtime-verified).** The L6 `403` bodies and the L7 `403` body include full Python tracebacks with server paths (`apps/frappe/frappe/handler.py`, etc.), and the `Server` header discloses `Werkzeug/3.0.6 Python/3.10.12`. This is Frappe framework/developer-mode behavior on this test site, outside the app's contract surface; worth hardening (disable developer mode / front with nginx error handling) before any non-loopback exposure.
- **O3 — Framework Guest cookies (runtime-verified).** Every API response sets `sid=Guest; system_user=no; full_name=Guest; user_id=Guest; user_image=` cookies. These are Frappe's framework-level Guest session cookies; the tracking session token is **never** set or read via cookies (contract §5.4 satisfied). No action.
- **O4 — Timestamp format (runtime-verified, previously documented).** `last_updated`/`effective_on` are naive ISO-8601 **with microseconds** (`2026-07-22T19:32:39.826642`); the contract samples show second precision. Same type (string, ISO-parseable); the 08c report already documents naive-no-timezone as a recorded deviation. Not treated as a mismatch.
- **O5 — Failure-side ACAO asymmetry (runtime-verified).** Failure responses to the *allowed* origin (L2, L4, L9) do carry `Access-Control-Allow-Origin: https://tracker-test.example.com`; failure responses to disallowed/missing origins carry none (L8a/L8d). This is correct CORS behavior.

## 7. E2E matrix impact (`11-task-010-evidence.md` §7)

| Matrix item | Previous status | This phase |
|---|---|---|
| 8 — Public API: HMAC verify → opaque Redis session | `blocked` | **runtime-closed** (L1 + Redis payload inspection) — runtime-verified |
| 9 — invalid passport/DOB → constant HTTP-200 generic failure | `blocked` | **runtime-closed** (L2, byte-shape, no enumeration) — runtime-verified |
| 10 — rate limit + lockout; `Retry-After` | `blocked` | **runtime-closed** (L9, real Redis, `Retry-After: 900` after 5 failures) — runtime-verified |
| 11 — CORS rejects disallowed origins | `blocked` | **runtime-closed** (L8a/L8b/L8d) — runtime-verified; preflight caveat recorded as F1 |
| 15 — raw OCR/MRZ not readable by Guest | extraction side already runtime-pass | **additional runtime evidence**: Guest `GET /api/resource/Visa Tracking Application` → 403, zero rows (L7). The tracking-DocType resource boundary is now runtime-verified for the probed endpoint; other internal DocType endpoints were not probed in this phase. |
| 16 — public response boundary; no internal identifiers | `blocked` | **runtime-closed** (L3: exact 9-key allowlist, 4-key timeline items, masking, no forbidden fields, no nulls) — runtime-verified |
| 19 — browser smoke of built SPA against a live backend | `not-run` | **NOT closed.** This phase established and probed the live HTTP surface (a prerequisite), but no browser/visual rendering was exercised. Item 19 remains `not-run`. |

Not in the §7 matrix but runtime-verified here for the first time: POST-only rejection (L6), session expiry (L4c), logout invalidation + non-enumerating logout (L5), status success envelope shape (L3).

## 8. Cleanup performed (all runtime-verified)

- Killed the werkzeug server I started (PIDs 915104/915106); `ss -ltn` shows port 8899 free; `ps` shows no `run_simple` process. No pre-existing process was touched.
- Deleted via throwaway `/tmp/cleanup_wire.py` (since removed): `Visa Tracking Application` `VTA-2026-00013`; `Passport Extraction` `PEX-2026-00003`; status logs `VTL-2026-00014`, `VTL-2026-00015`; 24 `Visa Tracker Audit Log` rows generated by the probes (`VTAL-2026-00016`…`VTAL-2026-00039`); the synthetic `File` row and its physical file were cascade-deleted with the extraction (verified absent from `tabFile` and disk).
- Deleted 4 Redis keys I created: 2 `visa_tracker:session:*` (live tokens from L8b and the fresh-token check) and 2 `visa_tracker:failed:*` failure buckets (incl. the `P1234567` lockout bucket — no lockout state remains). Post-deletion scans returned empty.
- Removed all remote throwaway files: `/tmp/seed_wire.py`, `/tmp/expire_wire.py`, `/tmp/expire_wire2.py`, `/tmp/cleanup_wire.py`, `/tmp/wire_serve.log`.
- Worktree verified clean afterwards: `git status --short` empty, HEAD `910914e`, branch `feat/visa-tracker`.
- Deliberately left: Frappe framework Guest-session state (`sid=Guest` cookies are client-side; framework session cache entries, if any, are framework-managed and expire on their own); `sites/visa-tracker-test.localhost/private/files/synthetic_probe_53386f48.png` — a leftover from an earlier phase (mtime 11:51 local, before this session), not created by me; standard Frappe request/error log lines written during probing (framework logs, contain no PII — probe payloads are synthetic).

## 9. Evidence labels

- **runtime-verified** — every probe result L1–L9 (real HTTP responses, real Redis session/lockout behavior, real 403 denials), settings read-back, seed, cleanup, worktree state.
- **statically-verified (source-wired)** — the helper-process cache-memoization explanation for L4c (`frappe/utils/redis_wrapper.py` `get_value` semantics); seed-time field names from DocType JSONs and service modules read in the worktree.
- **unverifiable in this phase** — browser/visual behavior (matrix item 19), preflight impact on a real browser deployment (F1 is inferred from the recorded preflight response, not from a browser), internal DocType resource endpoints other than `Visa Tracking Application`.

---

## Appendix A — raw probe evidence (verbatim `curl -sS -i` output; all data synthetic)

### A.1 L1 — verify happy path

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:03:53 GMT
Content-Type: application/json
Content-Length: 130
Access-Control-Allow-Origin: https://tracker-test.example.com
Vary: Origin
Set-Cookie: sid=Guest; Expires=Wed, 29 Jul 2026 16:03:53 GMT; Max-Age=612000; HttpOnly; Path=/; SameSite=Lax
Set-Cookie: system_user=no; Path=/; SameSite=Lax
Set-Cookie: full_name=Guest; Path=/; SameSite=Lax
Set-Cookie: user_id=Guest; Path=/; SameSite=Lax
Set-Cookie: user_image=; Path=/; SameSite=Lax
Connection: close

{"success": true, "message": "Verification successful.", "data": {"session_token": "tOQPLvXKdZi725Hg4b1ydADAxPL89Q9K6za809aeS7E"}}
```

### A.2 L2 — verify wrong identity (`P9999999`)

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:03:53 GMT
Content-Type: application/json
Content-Length: 105
Access-Control-Allow-Origin: https://tracker-test.example.com
Vary: Origin
Set-Cookie: sid=Guest; Expires=Wed, 29 Jul 2026 16:03:53 GMT; Max-Age=612000; HttpOnly; Path=/; SameSite=Lax
Set-Cookie: system_user=no; Path=/; SameSite=Lax
Set-Cookie: full_name=Guest; Path=/; SameSite=Lax
Set-Cookie: user_id=Guest; Path=/; SameSite=Lax
Set-Cookie: user_image=; Path=/; SameSite=Lax
Connection: close

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

### A.3 L3 — status with valid token

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:04:10 GMT
Content-Type: application/json
Content-Length: 758
Access-Control-Allow-Origin: https://tracker-test.example.com
Vary: Origin
Set-Cookie: sid=Guest; Expires=Wed, 29 Jul 2026 16:04:10 GMT; Max-Age=612000; HttpOnly; Path=/; SameSite=Lax
Set-Cookie: system_user=no; Path=/; SameSite=Lax
Set-Cookie: full_name=Guest; Path=/; SameSite=Lax
Set-Cookie: user_id=Guest; Path=/; SameSite=Lax
Set-Cookie: user_image=; Path=/; SameSite=Lax
Connection: close

{"success": true, "message": "Status retrieved.", "data": {"applicant_name_masked": "J****e", "passport_number_masked": "P0****00", "destination": "United Arab Emirates", "visa_type": "Tourist Visa", "current_status": "Working on Your Application", "public_message": "We are preparing your application for submission.", "last_updated": "2026-07-22T19:32:39.826642", "timeline": [{"status": "Working on Your Application", "message": "We are preparing your application for submission.", "effective_on": "2026-07-22T19:32:39.826642", "icon": "tool"}, {"status": "Application Received", "message": "Your application has been received.", "effective_on": "2026-07-19T19:32:39.826642", "icon": "inbox"}], "support_link": "https://tracker-test.example.com/support"}}
```

### A.4 L4 — missing / bogus / expired token

L4a (`{}`):

```
HTTP/1.1 200 OK
Content-Length: 105
[Guest Set-Cookie headers + ACAO as above]

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

L4b (bogus token `bogus-token-never-issued-000000000000`): identical status line, headers, and body to L4a.

L4c (expired session): helper output, then the probe:

```
payload before: {'tracking_application': 'VTA-2026-00013', 'created_at': '2026-07-22T19:35:01.650049'}
TTL set to 2s; sleeping 3s

HTTP/1.1 200 OK
Content-Length: 105

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

Expiry cross-check: token `Ymx-4doQrmtOup-p3Buk7ABCCujnQllgmanWmGWhKdg` (same 2s-TTL procedure) also returned the generic failure, while token `OXFPCUOkBPA7uLGk3zAaQhNENJeD8-GQF3KVfI0Yisg` issued and used immediately returned the full L3 success body — so the failure is attributable to expiry, not to endpoint breakage.

### A.5 L5 — logout

L5a (valid token):

```
HTTP/1.1 200 OK
Content-Length: 57
Access-Control-Allow-Origin: https://tracker-test.example.com
Vary: Origin
[Guest Set-Cookie headers]

{"success": true, "message": "Logged out.", "data": null}
```

L5b (status reuse of logged-out token): generic failure body identical to A.4.

L5c (logout, never-existed token): status line, headers, and body byte-identical to L5a.

### A.6 L6 — GET instead of POST (all three endpoints)

All three returned the same status and framework error shape (traceback truncated here; full body is a 1524-byte JSON with `exception`, `exc_type`, `exc`, `_server_messages`):

```
HTTP/1.1 403 FORBIDDEN
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:08:43 GMT
Content-Type: application/json
Content-Length: 1524
[Guest Set-Cookie headers]

{"exception":"frappe.exceptions.PermissionError: Not permitted","exc_type":"PermissionError","exc":"[\"Traceback (most recent call last):\n  File \"apps/frappe/frappe/app.py\", line 120, in application\n ... frappe/handler.py\", line 84, in execute_cmd\n    is_valid_http_method(method)\n ... frappe.exceptions.PermissionError: Not permitted\n\"]","_server_messages":"[\"{\\\"message\\\": \\\"Not permitted\\\", \\\"title\\\": \\\"Message\\\", \\\"indicator\\\": \\\"red\\\", \\\"raise_exception\\\": 1 ...}\"]"}
```

### A.7 L7 — Guest `GET /api/resource/Visa Tracking Application`

```
HTTP/1.1 403 FORBIDDEN
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:08:43 GMT
Content-Type: application/json
Content-Length: 1832
[Guest Set-Cookie headers]

{"exception":"frappe.exceptions.PermissionError","exc_type":"PermissionError","exc":"[\"Traceback (most recent call last):\n ... frappe/model/db_query.py\", line 573, in check_read_permission\n ... frappe.exceptions.PermissionError\n\"]","_server_messages":"[\"{\\\"message\\\": \\\"User <strong>Guest</strong> does not have doctype access via role permission for document <strong>Visa Tracking Application</strong>\\\", \\\"title\\\": \\\"Message\\\"}\"]","_error_message":"No permission for Visa Tracking Application"}
```

No document data of any kind in the response.

### A.8 L8 — CORS

L8a (disallowed Origin `https://evil.example.com`) — note absence of any `Access-Control-*` header:

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:09:06 GMT
Content-Type: application/json
Content-Length: 105
[Guest Set-Cookie headers]
Connection: close

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

L8b (allowed Origin): `Access-Control-Allow-Origin: https://tracker-test.example.com`, `Vary: Origin`, body `{"success": true, "message": "Verification successful.", "data": {"session_token": "DNRmV9lFbPrIcdpyEVAWJ-62jnRraEPoAuOi6jFH7pU"}}`.

L8c (OPTIONS preflight with `Access-Control-Request-Method: POST`, `Access-Control-Request-Headers: content-type`):

```
HTTP/1.1 200 OK
Server: Werkzeug/3.0.6 Python/3.10.12
Date: Wed, 22 Jul 2026 14:09:06 GMT
Content-Type: text/plain; charset=utf-8
Content-Length: 0
Connection: close
```

L8d (no Origin header): generic failure, no `Access-Control-*` headers (same shape as L8a).

### A.9 L9 — lockout (`P1234567`, `maximum_failed_attempts=5`)

Attempts 1–5 (each):

```
HTTP/1.1 200 OK
Content-Length: 105

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

Attempts 6 and 7 (each):

```
HTTP/1.1 200 OK
Content-Length: 105
Retry-After: 900

{"success": false, "message": "Unable to verify. Please check your details and try again.", "data": null}
```

---

## Appendix C — Coordinator addendum: rate limiting does not constrain credential enumeration

**Added by the coordinator after independently re-running the live smoke.** The executor's L9 above is correct as far as it goes, but it probed only the *same-credential-pair* case. Extending it across buckets surfaces a genuine security gap that the passing L9 conceals.

**Severity: medium-high. Design-level, not a coding bug. NOT fixed — this is a TASK-007 security-model decision, not a coordinator call.**

### Root cause

`api/verification.py:102` sets `target_bucket = candidates[0][0]` — the lookup hash of passport **+ DOB** — and `rate_limit_service.build_client_key(origin_scope, source_ip, target_bucket)` composes the counter key from all three components. The failed-attempt counter is therefore scoped per *(origin, IP, exact credential pair)*.

### Empirical demonstration (real HTTP, real Redis, coordinator-run)

- **Case A — 7× the identical wrong pair (`P2222222` / `1990-01-01`):** lockout engaged exactly at attempt 6, consistent with `maximum_failed_attempts=5`, returning `Retry-After: 900` (= `lockout_minutes=15`). This reproduces the executor's L9 result. Works as designed.
- **Case B — 7× the same passport (`P3333333`) with an incrementing DOB (`1990-01-01`…`1990-01-07`):** lockout **never engaged**; 0 of 7 responses carried `Retry-After`. Each distinct DOB yields a different lookup hash, hence a fresh bucket whose counter never accumulates.

### Consequence

The limiter only throttles an attacker who repeats the *exact same wrong credential pair* — the one attack nobody actually mounts. An attacker who knows or guesses a passport number can enumerate DOBs from a single IP indefinitely without ever tripping lockout; an adult DOB space is roughly 36,500 candidates, entirely feasible unthrottled. The reverse case, enumerating passport numbers against a fixed DOB, is equally unconstrained.

Note the interaction with the (correct) constant-200 design: because every failure returns a byte-identical body, there is no external signal that throttling is absent. This gap cannot be noticed from client behavior — only by reading the key composition or probing across buckets, which is why it survived both the 248-test in-process suite and the executor's passing L9.

### Recommendation (not applied)

The per-identity bucket is defensible on its own terms: it stops an attacker from locking a legitimate applicant out of their own record. The gap is the absence of a complementary coarser counter. Suggested fix: add a second, independent per-IP (and optionally per-origin) failure counter with a higher threshold and its own lockout, evaluated alongside the existing per-identity counter. That preserves the anti-lockout-DoS property while closing enumeration. Requires a TASK-007 amendment and product sign-off.

### Coordinator cleanup for this addendum

Loopback server on port 9711 stopped (confirmed not listening); `/tmp/vtsmoke_*` files removed; worktree `910914e` clean. Lockout keys created by Case A expire naturally within 15 minutes on the disposable test site. The `bench serve` processes visible on this shared host belong to OTHER users (swafa, shahala, ameen, jezlan, vaishna, sanjusha, fathima, vyshnav) and were deliberately left untouched.
