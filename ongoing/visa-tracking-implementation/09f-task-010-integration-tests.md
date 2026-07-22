# 09f — TASK-010 Integration Test Implementation (visa_tracking)

> Date: 2026-07-22
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Scope: implement the 27 placeholder integration test bodies in the
> `the_visaguy` feature worktree (test code only), add the two missing
> standalone-tier site guards, run all tiers, commit, report.
> Worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`, branch
> `feat/visa-tracker`, base HEAD `ccbd63240d952979a62ceb408e987ff9e3c4c0cd`.
> Site: `visa-tracker-test.localhost` (dedicated, non-production).

---

## 1. Outcome summary

- **22 of 27 placeholder bodies implemented** and passing on the dedicated site.
- **5 bodies left as skips with updated, honest defect reasons** — blocked by
  two genuine app defects found while implementing (§4). Per the task
  contract, no app code was modified.
- 2 standalone-tier site guards added (`test_lookup_service.TestLookupService`,
  `test_settings.TestSettings`) — the standalone tier now skips cleanly
  instead of erroring.

## 2. Per-file implementation summary

All integration tests run unmocked against the real database, real bench
redis (`frappe.cache()`), and the live `Visa Tracker Settings` Single. All
identity data is synthetic (`P0000000`, `P9999999`, `1990-01-01`,
`203.0.113.x`, `Test Person`). Fixture extractions are walked through the
controller-enforced transitions `Queued -> Processing -> Extracted ->
Verified` with a real private PNG `File` (generated with Pillow 11.3.0,
present in the bench env; fake bytes fail downstream parsers).

Where a class creates tracking documents, per-test fixture cleanup
(setUp/tearDown row-tracking + `frappe.db.delete`) was added because
`FrappeTestCase` rolls back only at **class** level
(`frappe/tests/utils.py`: `setUpClass` commits, `addClassCleanup(_rollback_db)`),
so tests within one class share a transaction — and the autoname defect
(§4.1) allows only one row per tracking DocType at a time.

| File | Bodies | What is asserted |
|---|---|---|
| `visa_tracking/tests/test_audit_service.py` | 1 skipped | `test_audit_rows_written_and_append_only` — skip with defect evidence (§4.1): append-only needs ≥ 2 audit rows; the second insert is silently swallowed |
| `visa_tracking/tests/test_fileflo_inspection.py` | 1 implemented | Synthetic FF File Collection → FF Document → private PNG File, field_id `passport_front` (live settings). `run_fileflo_inspection` creates exactly one `Queued` `Passport Extraction` with provenance + recorded `last_job_id`; re-delivery returns `reused`, no second record (matrix items 1, 3) |
| `visa_tracking/tests/test_lifecycle_service.py` | 4 implemented | Verified extraction → exactly one application per identity hash, one creation log row, Lead links (item 6); PF `custom_client_status` save → exactly one log row, idempotent re-save/re-sync (item 7); `correct_tracking_status` (as Administrator/System Manager) records reason, syncs PF via recursion-safe write, guard released, one log row (item 7); repeated verified event via `handle_verified_extraction` does not duplicate applications or log rows (items 6, 7) |
| `visa_tracking/tests/test_security_utils.py` | 1 implemented | `validate_cors` against the live Single: exact match (+ trailing slash) allowed; other/suffix/spoofed-scheme origins, `*`, `null`, empty, `None` rejected; localhost rejected because `visa_tracker_allow_localhost_origins` is unset (item 11) |
| `visa_tracking/tests/test_response_service.py` | 1 implemented | Payload built from live documents: exact `STATUS_PAYLOAD_KEYS` allowlist, masked name/passport, live support link, timeline entry keys; serialized payload contains no passport/DOB/internal names/lookup hash (item 16) |
| `visa_tracking/tests/test_session_service.py` | 1 implemented | Real-redis round trip: create (TTL ≤ configured 900 s), resolve returns minimal payload, hard max-lifetime kill for an over-aged session, explicit delete invalidates; redis keys cleaned up (item 8) |
| `visa_tracking/tests/test_status_service.py` | 2 implemented, 1 skipped | Two identical `update_tracking_status` calls append exactly one log row with source provenance; inactive synthetic status (`TASK010_INACTIVE`) rejected by resolve and update, no trace left. `test_public_timeline_respects_configured_limit` skipped — needs ≥ 2 log rows (§4.1) |
| `visa_tracking/tests/test_reconciliation_service.py` | 2 implemented | Missing-extraction report flags the synthetic collection row (identifiers only) and stops flagging after inspection creates the extraction; status-mismatch report returns the synthetic divergent PF/VTA pair and mutates nothing (doc state, log rows, extraction counts compared before/after) (item 17) |
| `visa_tracking/tests/test_rate_limit_service.py` | 1 implemented | Real-redis lockout: `record_failure` up to the configured maximum (5), `is_allowed` False, `Retry-After`-bounded remaining TTL, `reset_failures` restores; key contains no raw values; keys cleaned for back-to-back runs (item 10) |
| `visa_tracking/tests/test_public_api.py` | 1 implemented, 1 skipped (+ helper) | Guest denied read on the three internal DocTypes (`has_permission` False; `get_list` raises or returns empty) (item 15). `test_valid_verification_then_status_round_trip` skipped (§4.2). `make_tracking_application` helper implemented |
| `the_visa_guy/doctype/visa_tracker_settings/test_visa_tracker_settings.py` | 4 implemented | Live Single validation: `max_session_lifetime_minutes` bounds (0/1441 throw; 1/1440 pass), blank `frontend_base_url` rejected while public tracking enabled, wildcard/non-http(s) origin rejected, blank `generic_failure_message` rejected. In-memory only; original values restored |
| `the_visa_guy/doctype/visa_tracking_application/test_visa_tracking_application.py` | 4 implemented, 2 skipped (+ helper) | Full `verify_identity` round trip through a synthetic JSON request context: token-only success shape, no PII/hash in the body, token resolves in real redis (items 8, 16); wrong passport → byte-identical generic failure, failure counted, one redacted audit row (item 9); 5 failures → lockout with `Retry-After` (item 10); Guest denial on all five tracking DocTypes + zero Guest DocPerm/Custom DocPerm rows (item 15). `test_status_response_is_allowlisted_and_masked` (§4.2) and `test_audit_rows_contain_no_pii` (§4.1) skipped |
| `visa_tracking/tests/test_lookup_service.py` | guard added | `setUpClass` site guard on `TestLookupService` (mirrors the established pattern) |
| `visa_tracking/tests/test_settings.py` | guard added | `setUpClass` site guard on `TestSettings` |

## 3. Site-config prerequisites (verified, all synthetic/non-production)

- `visa_tracker_lookup_hmac_key` and `visa_tracker_audit_hmac_key` present in
  the test site's `site_config.json` (presence-only check; values never read
  or recorded). — **configured-unverified** (values), **runtime-verified**
  (lookup/audit hashing works against them).
- `visa_tracker_allow_localhost_origins` NOT set — asserted by the CORS test.
- `Visa Tracker Settings` Single: `enabled=1`, `enable_public_tracking=1`,
  `enable_passport_extraction=1`, `frontend_base_url=https://tracker-test.example.com`,
  `generic_failure_message` set, `default_lead_status=APPLICATION_RECEIVED`,
  `passport_field_ids=passport_front`, `maximum_failed_attempts=5`,
  `lockout_minutes=15`, `session_expiry_minutes=15`,
  `max_session_lifetime_minutes=60`, `status_history_limit=20`,
  `support_link=https://tracker-test.example.com/support`. — **runtime-verified**.
- 6 active `Visa Tracking Status` records (names == status codes).
- Nothing was reconfigured; no settings were changed by this task.

## 4. Genuine app defects found (NOT fixed — test-code-only contract)

### 4.1 TASK-005 schema defect: unbraced `format:` autonames produce literal names — **runtime-verified**

- `visa_tracking_application.json`: `"autoname": "format:VTA-.YYYY.-.#####"`
- `visa_tracking_status_log.json`: `"autoname": "format:VTL-.YYYY.-.#####"`
- `visa_tracker_audit_log.json`: `"autoname": "format:VTAL-.YYYY.-.#####"`

This Frappe version's `_format_autoname`
(`apps/frappe/frappe/model/naming.py:572`) substitutes only **braced**
parameters (`{YYYY}`, `{#####}`). The unbraced patterns above are returned
verbatim, so every record of these DocTypes gets the same literal name
(e.g. `VTA-.YYYY.-.#####`). The first insert succeeds; every subsequent
insert raises `DuplicateEntryError (1062)` — reproduced on the site
(exact traceback: `frappe.exceptions.DuplicateEntryError: ('Visa Tracking
Application', 'VTA-.YYYY.-.#####', ...)`). In the audit path the duplicate
is silently swallowed by `audit_service._safe_insert_event`, so audit rows
after the first are **lost without error**.

Production impact: only one tracking application, one status log row, and
one audit row can ever exist per site. Blocks test bodies:
`test_audit_rows_written_and_append_only`,
`test_audit_rows_contain_no_pii`,
`test_public_timeline_respects_configured_limit`
(all need ≥ 2 rows of the affected DocTypes).

### 4.2 TASK-007 defect: `NameError` in the public display timeline — **runtime-verified**

`visa_tracking/services/status_service.py:254` —
`get_public_display_timeline` builds each entry with
`"effective_on": _iso_or_empty(effective_on)`, but `effective_on` is not
defined in that scope (the loop variable is `row`). Any call with ≥ 1
timeline row raises `NameError: name 'effective_on' is not defined`
(reproduced on the site; full traceback recorded). `api/status.py
get_tracking_status` (line 134) calls it inside a try/except that degrades
to the constant generic failure, so **the public status endpoint always
fails for real applications** (creation always appends one visible log
row). Blocks test bodies:
`test_valid_verification_then_status_round_trip`,
`test_status_response_is_allowlisted_and_masked`.

## 5. Suite counts (all on `visa-tracker-test.localhost`, worktree-first PYTHONPATH)

| Suite | Before | After |
|---|---|---|
| `run-tests --app the_visaguy --skip-test-records` (run 1) | 248 ran / 221 pass / 27 skipped / 0 failures / 0 errors | **248 ran / 243 pass / 5 skipped / 0 failures / 0 errors — `OK (skipped=5)`** |
| `run-tests --app the_visaguy --skip-test-records` (run 2, back-to-back) | — | **248 ran / 243 pass / 5 skipped / 0 failures / 0 errors — `OK (skipped=5)` (identical; no cross-run pollution)** |
| `run-tests --app fileflo --skip-test-records` | 6 ran / 6 pass | **6 ran / 6 pass — unchanged** |
| Standalone (`visa_tracking/tests`, no site) | 199 ran / 187 pass / 10 skipped / 2 errors | **199 ran / 187 pass / 12 skipped / 0 errors — `OK (skipped=12)`** |

"Before" counts were measured this dispatch by stashing the worktree
changes and re-running both suites (not transcribed from earlier reports).
Logs on the bench host: `/tmp/task010_run1.log`, `/tmp/task010_run2.log`,
`/tmp/task010_fileflo.log`, `/tmp/task010_standalone.log`,
`/tmp/task010_onsite_base.log`, `/tmp/task010_standalone_base.log`.

Note on totals: the brief's "275 ran" target does not match reality — full
collection for `--app the_visaguy` at HEAD `ccbd632` + these test changes
is **248 tests** (verified by module-level collection: 239 across the 14
touched modules + 9 in the app's other test modules; the baseline suite
also ran 248). The 5 remaining skips are the defect-blocked bodies in §4;
all other placeholder skips are gone.

One pure-tier repair was required alongside the guards: the two newly
guarded classes used to error standalone in `FrappeTestCase.setUpClass`,
and that partial failure left `frappe.local.flags` initialized — which the
whitelisted-API wrapper (`typing_validations`) needs. With clean skips,
37 pure `test_public_api` tests errored standalone on
`AttributeError: flags`. `ApiTestBase.setUp` now initializes
`frappe.local.flags` explicitly (test infrastructure only; no assertion
logic changed).

## 6. E2E matrix items closed (evidence doc §7)

- Item 1 (FileFlo trigger): **runtime-verified** — `test_synthetic_fileflo_submission_creates_one_queued_extraction`.
- Item 2 (non-configured field does not trigger): remains pure-tier only (not in the 27 bodies).
- Item 3 (idempotent re-delivery): **runtime-verified** — same test (second inspection `reused`, count stays 1).
- Item 6 (lifecycle Lead/link + created status): **runtime-verified** — `test_verified_extraction_creates_one_application_per_identity`, `test_repeated_verified_event_does_not_duplicate_applications`.
- Item 7 (PF sync + correction): **runtime-verified** — `test_pf_client_status_change_appends_exactly_one_log_row`, `test_correction_updates_process_file_without_recursion`.
- Item 8 (HMAC verify → opaque redis session): **runtime-verified** — `test_valid_verification_returns_token_only`, `test_session_round_trip_against_bench_redis`.
- Item 9 (generic failure): **runtime-verified** — `test_invalid_combination_matches_not_found_shape`.
- Item 10 (rate limit/lockout): **runtime-verified** — `test_lockout_against_bench_redis`, `test_lockout_after_maximum_failed_attempts`.
- Item 11 (CORS): **runtime-verified** — `test_cors_against_live_settings`.
- Item 15 (Guest raw-data denial): **runtime-verified** — `test_guest_cannot_access_resource_endpoints`, `test_guest_resource_endpoints_are_denied`.
- Item 16 (response boundary): **runtime-verified at payload level** — `test_status_payload_against_live_documents`; the API-level variant is **blocked** by defect §4.2.
- Item 17 (reconciliation): **runtime-verified** — both reconciliation tests.
- Audit append-only/no-PII runtime coverage: **blocked** by defect §4.1 (pure-tier coverage remains).

## 7. Commits

- `088430f486d82eafcc11cadb19c8310afb46421f` —
  `test(visa_tracking): implement TASK-010 integration test bodies`
  (14 test files changed, +1444/−37; feature worktree, branch
  `feat/visa-tracker`, environment-default Git identity, no push).
  `git status --short` verified clean after commit.

## 8. Remaining issues / follow-ups

1. **Corrective needed for §4.1** (schema): change the three autonames to
   braced form (e.g. `format:VTA-{YYYY}-{#####}`) or plain series
   (`VTA-.YYYY.-.#####`, which expands correctly — proven by
   `Passport Extraction`'s working `PEX-.YYYY.-.#####`), then re-migrate.
   Until then the three skipped audit/timeline bodies cannot run.
2. **Corrective needed for §4.2**: `status_service.py:254` should read
   `row.get("effective_on")`. Until then the public status endpoint is
   broken for all real applications and the two API-level status tests
   stay skipped.
3. After both correctives: implement the 5 skipped bodies (the fixture
   helpers are already in place) and re-run.
4. The brief's 275-test target was miscalibrated; exact measured counts
   are recorded in §5.
