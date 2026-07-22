# TASK-010 Evidence and Verdict — FEAT-001 End-to-End Verification

> Date: 2026-07-22 (static phases A/D/E executed first dispatch; runtime Phase B/C executed second dispatch, same date — this document was **updated**, not rewritten wholesale)
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-010 — End-to-end verification and rollout
> Prompt: `ongoing/visa-tracking-implementation/prompts/10-task-010-final-verification.txt`
> Executor scope: read/verification/evidence only. No application code edited, no commits, no push, no deploy. Only this file and `10-task-010-planning.md` were written. Site writes were limited to the dedicated nonproduction site `visa-tracker-test.localhost` (app installs/migrations only; synthetic data only).
> **Overall verdict: TASK-010 is NOT complete — runtime-blocked by a genuine TASK-005 app defect.** The previous environmental blocker (absent `root_password`, no dedicated site) is resolved; the dedicated-site runtime gate now executes, and `the_visaguy` migration fails reproducibly on any site for two code-level reasons (§4.6). Exact next action in §10. Rollout plan is procedural only and authorizes nothing.

---

## 1. Entry gate

- TASK-004 (`fa1d6b38`, `34cb477`), TASK-006 (`92223020`), TASK-007 (`d20cc6d4`), TASK-009 (`717c62d4`) all have clean committed implementation SHAs and reports — verified independently in §2/§3. TASK-002/TASK-003 runtime is now **closed**: correctives 09b (`cbea2159`) and 09c (`3486fccd`) fixed the controller/preprocessor defects found by 09a; passport_extractor suite is **61/61 green** on the dedicated site (09c, re-verified independently by the coordinator). Entry gate satisfied; no unexpected dirty repository found.
- Correction to the prompt applied: the task file lives at `tasks/in-progress/visa-tracking/TASK-010-end-to-end-verification-and-rollout.md` (the prompt's `tasks/ready/` path is stale). Lifecycle moves are left to the coordinator.
- Second dispatch correction applied: `root_password` **is present** in `sites/common_site_config.json` (count-only check) — the PRESENT branch was taken (§4).

## 2. Reconciliation table (TASK-002…TASK-009)

| Task | Repository | Branch | Base SHA | Final SHA | Static checks | Runtime checks | Blockers / deviations |
|------|-----------|--------|----------|-----------|---------------|----------------|------------------------|
| TASK-002 | `passport_extractor` | `feat/visa-tracker` | `07b8cab40cd4054b39a78f23a271d7201e71baa0` | `3486fccd8fc8272f93ee97d049b951d201296cad` (via `034f1c17`, `cbea2159`) | Pass (47 fields, exact statuses, permlevel-1 raw fields, compile, imports, forbidden-dep scan) | **Pass — 61/61 on dedicated site** (09a→09b→09c; coordinator re-verified) | Closed by correctives 09b/09c |
| TASK-003 | `passport_extractor` | `feat/visa-tracker` | `2f25c0d5` | `3486fccd` (same HEAD) | Pass (lazy imports, MRZ pure tests, error-code redaction) | **Pass — OCR pipeline runtime-verified** (61/61 incl. real-engine tests; models preloaded §8) | Closed; PyMuPDF now installed (§8) |
| TASK-004 | `fileflo` | `feat/visa-tracker` | `6683010e89d9209363e6ba3881f4a90a47420bd2` | `fa1d6b38351ef1dfc5e9a4bb66ddae22b26f7866` | Pass (6 pure tests re-run green §5; boundary scans §3) | **Blocked** — fileflo installed on dedicated site, but trigger-level runtime needs `the_visaguy` migrated | TASK-005 defects (§4.6) |
| TASK-004 | `the_visaguy` | `feat/visa-tracker` | `f7ad8c05` | `34cb47754e9b31324ac81f64bd923cef7b22c082` | Pass (18 pure tests; hook resolution) | **Blocked** | Same; enqueue path uses `passport_extractor.passport_extractor.jobs...` (recorded deviation) |
| TASK-005 | `the_visaguy` | `feat/visa-tracker` | `e690b5b1ac897874fb33439fa429e2aee103cc3e` | `f7ad8c0518a6442cbb33136b84dba524f2909ecd` | Pass (schema/fixture JSON, no-Guest perms, compile, hook registration) — **static tier missed the two defects below** | **FAILED — migration fails on any site** (§4.6) | **Defect A: DocType folder placement; Defect B: fixture records missing `name`/`modified`** |
| TASK-006 | `the_visaguy` | `feat/visa-tracker` | `34cb477` | `9222302035c2c077ed91662cc49af784dac3119f` | Pass (82-test combined suite; doc_events merge verified §3) | **Blocked** | TASK-005 defects (§4.6) — lifecycle runtime needs the five DocTypes |
| TASK-007 | `the_visaguy` | `feat/visa-tracker` | `92223020` | `d20cc6d49cfae6c47749f8b5a94df0fa38546979` | Pass (199-test suite re-run §5; guest-method registration verified §3) | **Blocked** | Same; logout API + Audit Log DocType + 3 settings fields added per dispatch prompt (recorded deviations) |
| TASK-008 | `visa_tracker` (local, no remote) | `main` | `20b8c45` | `a21bbd5083a4c2c9bf9b462697d0965e543423f0` | Pass (lint/tsc/build) | n/a (design shell; no backend calls) | None |
| TASK-009 | `visa_tracker` (local, no remote) | `main` | `a21bbd50` | `717c62d402287849b30a1fd25d3760edfb727747` | Pass (lint/tsc/16 Vitest/build re-run §6) | **Blocked** for live-backend E2E; unit/component level pass | Constant HTTP-200 generic-failure contract: mid-flow session expiry indistinguishable from generic failure (§7, §8) |

TASK-002/TASK-003 runtime is closed. All remaining runtime deferrals trace to the TASK-005 migration defects in §4.6 — `the_visaguy` cannot be migrated on any site until corrected, which blocks the lifecycle/API/E2E runtime evidence for TASK-004 (trigger seam), TASK-006, and TASK-007.

## 3. Repository state and dependency-boundary verification (re-verified this run, 2026-07-22)

Commands were read-only (`git rev-parse`, `git branch --show-current`, `git status --short`, `git log`, `grep`) over `ssh -p 2257 shahzad@erpcode.tridz.in`.

### 3.1 Feature worktrees — all at expected HEADs, all clean (runtime-verified)

| Worktree | HEAD | Branch | Status |
|---|---|---|---|
| `/home/shahzad/visa-tracker-worktrees/passport_extractor` | `3486fccd8fc8272f93ee97d049b951d201296cad` | `feat/visa-tracker` | clean |
| `/home/shahzad/visa-tracker-worktrees/fileflo` | `fa1d6b38351ef1dfc5e9a4bb66ddae22b26f7866` | `feat/visa-tracker` | clean |
| `/home/shahzad/visa-tracker-worktrees/the_visaguy` | `d20cc6d49cfae6c47749f8b5a94df0fa38546979` | `feat/visa-tracker` | clean |
| `/home/shzd/Projects/tridz/visa_tracker` | `717c62d402287849b30a1fd25d3760edfb727747` | `main` | clean |

Commit chains confirmed: passport_extractor `6746d04 → 2f25c0d → a13fa3c → 034f1c1 → cbea215 → 3486fccd` (last two are correctives 09b/09c); fileflo `fa1d6b3`; the_visaguy `f7ad8c0 → 34cb477 → 9222302 → d20cc6d`; visa_tracker `20b8c45 → a21bbd5 → 717c62d`.

### 3.2 Read-only repositories unchanged (runtime-verified)

- Original checkouts: `the_visaguy` `main` @ `e690b5b1`, `fileflo` `fix/mandatory-file` @ `6683010e`, `passport_extractor` `develop` @ `07b8cab4` — all clean.
- `processflo` `develop` @ `2f2b5657d20a778159dce0b2268c2a676ad66627`, dirty **only** in the pre-existing unrelated `processflo/generate_file_collection.py` — left untouched (installing the processflo app on the test site does not modify the checkout).
- `/home/shzd/Projects/tridz/visaguy-website-client` `main` @ `3b066f6baa7291fa3f778e8d7c1d70e236f0db80`, clean — unmodified.

### 3.3 Dependency boundaries (source-wired; re-scanned in the static phase)

- `passport_extractor`: **zero** matches for `the_visaguy|fileflo|processflo|Visa Tracking|PF Process File|FF File Collection|Lead|Customer` in `.py`/`.json`/`.md` — ADR-003/ADR-004 boundary holds.
- `fileflo` production source: **zero** matches for `the_visaguy|passport_extractor|processflo|Visa Tracker|Visa Tracking|Passport Extraction` and zero `passport`/`MRZ` terminology outside tests; the only hits are the intentional forbidden-imports guard string list in `fileflo/tests/test_events.py` (matches TASK-004 report).
- `the_visaguy`: **zero** `from/import fileflo|processflo` statements; `passport_extractor` references limited to the allowed public seam — function-local `from passport_extractor.passport_extractor.utils import validate_passport_file` in `services/extraction_orchestrator.py:60`, the worker dotted-path string `passport_extractor.passport_extractor.jobs.run_passport_extraction` (`:86`), and docstrings. `the_visaguy` observes FileFlo/PF events only through hooks (§3.4).

### 3.4 Hook and public-API wiring (source-wired)

- `the_visaguy.hooks.fileflo_extension_handlers == ['the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection']`.
- `doc_events['PF Process File'].on_update == ['the_visaguy.handlers.whatsapp_message.send_process_file_updates', 'the_visaguy.visa_tracking.handlers.process_file_handlers.on_update']` — existing mapping preserved, new handler appended.
- `Lead` and `CRM Lead` doc_events both registered (TASK-001 04a §3.4: both are source-wired in the deployed flow), plus `Customer` (`after_insert`, `on_update`) and `Passport Extraction` (`on_update`) mappings.
- `frappe.guest_methods` after importing the API modules contains exactly `verify_identity`, `get_tracking_status`, `logout` under `the_visaguy.visa_tracking.api.*`; all three decorators are `@frappe.whitelist(allow_guest=True, methods=["POST"])` in source (`verification.py:45`, `status.py:77`, `status.py:158`).

### 3.5 Secret/PII scans (false positives reviewed)

- Feature diffs (base→HEAD) of all three remote worktrees: 0 private-key blocks, 0 AWS-style keys, 0 MRZ-like 44-character strings (`grep -c` counts only; no values printed).
- HMAC secrets appear as configuration key **names** only (`visa_tracker_lookup_hmac_key`, `visa_tracker_audit_hmac_key`, `visa_tracker_allow_localhost_origins`) — configured-unverified, values never present in any repository or this workspace.
- Test fixtures use synthetic values only (`P0000000`, `P12345678`, `1990-01-01`, `203.0.113.10`, masked samples `A1****23`/`J****e`).
- Local frontend bundle scan: see §6.5 — clean.
- This runtime phase added **no** configuration values: the synthetic site-config step (§5 of the dispatch) was never reached because migration failed first (§4.6). No synthetic HMAC key was set; none is recorded anywhere.

## 4. Phase B — dedicated-site gate and runtime install execution (this run)

### 4.1 Gate checks

| Check | Command (redacted) | Result | Label |
|-------|--------------------|--------|-------|
| Config file exists | `test -f /home/shahzad/bench/sites/common_site_config.json` | exists | configured-unverified |
| `root_password` key present | `grep -c '"root_password"' /home/shahzad/bench/sites/common_site_config.json` | **1 — key PRESENT** | configured-unverified |
| Redis services | TCP `PING` to ports 13008/11008/12008 | `+PONG` on all three | runtime-verified |
| PyMuPDF | `import fitz` in bench env | `pymupdf 1.28.0` (09a) | runtime-verified |
| PaddleOCR/models | engine init via app `_get_engine()` (09b) | `paddleocr 3.7.0`, models `PP-OCRv6_medium_det/rec`, `PP-LCNet_x1_0_textline_ori` preloaded in bench user cache | runtime-verified |

Only key presence was inspected; the file was never printed and no value of any kind was read, copied, or stored. **PRESENT branch taken.**

### 4.2 Site reuse and isolation proof (before any write)

- `ls /home/shahzad/bench/sites` → `visa-tracker-test.localhost` exists (created 2026-07-22 by phase 09a); site dir contains `locks/ logs/ private/ public/ site_config.json touched_tables.json`; `site_config.json` keys: `allow_tests` (true), `db_name`, `db_password`, `db_type`, `encryption_key` (key names only; no value read).
- Pre-work installed apps (`bench --site visa-tracker-test.localhost list-apps`): **frappe 15.113.0 + passport_extractor 0.0.1 only** — a dedicated, nonproduction test database. Site `visaguy` was never targeted by any command in this phase.
- The site was **reused, not dropped/recreated**, per the dispatch.

### 4.3 Required apps (from TASK-001 evidence 04a/04b + the_visaguy hooks/fixtures)

| App | Why required | Evidence |
|-----|--------------|----------|
| `erpnext` (15.106.0, `version-15`) | ERPNext `Lead` and `Customer` — doc_events + 4 custom fields | 04a §3.4; `fixtures/custom_fields.json` |
| `crm` (2.0.0-dev, `tridz-dev`) | Frappe CRM `CRM Lead` — doc_events + 2 custom fields | 04a §3.4; hooks.py doc_events |
| `processflo` (0.0.1) | Owns `PF Process File` — doc_events + 2 custom fields | 04a; hooks.py doc_events |
| `insights` (2.2.14) | `the_visaguy` fixtures reference `Insights Query`/`Insights Chart` DocTypes | `fixtures/insights_*.json`, hooks.py fixtures list |
| `fileflo` (feature worktree) | FF File Collection generic after-commit event | TASK-004 |
| `the_visaguy` (feature worktree) | Feature app | TASK-005/006/007 |

No `required_apps` is declared in any of these apps' hooks; this erpnext checkout does not declare `payments` (checked hooks.py directly). Install order used: `erpnext → crm → insights → processflo → fileflo → the_visaguy`, each with worktree-first `PYTHONPATH` (`fileflo : the_visaguy : passport_extractor` worktrees).

### 4.4 Install results (runtime-verified)

| Step | Result |
|------|--------|
| `install-app erpnext` | **rc=0** — DocTypes synced, customizations for Address/Contact updated |
| `install-app crm` | **rc=0** — DocTypes synced, Email Template custom fields installed |
| `install-app insights` | **rc=0** |
| `install-app processflo` | **rc=0** |
| `install-app fileflo` | **rc=0** — from feature worktree at `fa1d6b3` |
| `install-app the_visaguy` | **rc=1 — FAILED** (§4.6) |
| `bench migrate` | **rc=1 — FAILED** at the same point (full log on bench host: `/tmp/vt_migrate_full.log`; contains no PII/secrets) |
| Post-failure `list-apps` | frappe, passport_extractor, erpnext, crm, insights, processflo, fileflo, the_visaguy (registry entry only — see §4.6 state) |

`Lead`, `CRM Lead`, `Customer`, `PF Process File`, `FF File Collection` DocTypes all exist on the site after these installs (SQL, runtime-verified).

### 4.5 Post-failure site state (read-only SQL, runtime-verified)

| Check | Result |
|-------|--------|
| `tabDocType` rows matching `Visa Track%` | **0** — the five the_visaguy DocTypes were never created |
| `tabVisa Tracking Status` table in `information_schema` | **absent** |
| Feature custom fields (`custom_passport_extraction`, `custom_visa_tracking_application`, `custom_client_status` on Lead/CRM Lead/Customer/PF Process File) | **8 present** (imported from fixtures before the crash; Custom Field creation issues DDL, which commits implicitly) |
| `tabCustom DocPerm` rows | 8 present (same batch) |
| Legacy the_visaguy DocTypes (`Quality Feedback`, `Raw Lead`) | present — synced normally from their module folders |
| `tabInstalled Application` | includes `the_visaguy 0.0.1 main` (registry row written before the failure) |
| `Passport Extractor User` role | present (from passport_extractor install) |

The state is consistent and retry-safe: once the §4.6 defects are corrected, re-running install/migrate will create the missing DocTypes and re-import fixtures idempotently. No site surgery was performed or is needed.

### 4.6 GENUINE TASK-005 DEFECTS — migration of `the_visaguy` at `d20cc6d` fails on any site

**Defect A — the five Visa Tracking DocTypes are in a folder Frappe never scans.** The DocType folders `visa_tracker_settings`, `visa_tracking_status`, `visa_tracking_application`, `visa_tracking_status_log`, `visa_tracker_audit_log` live at the app top level `the_visaguy/the_visaguy/doctype/`. Each declares `"module": "The Visa Guy"`, whose module folder is `the_visaguy/the_visaguy/the_visa_guy/` — which has **no** `doctype/` subfolder. Frappe's `sync_for` (`frappe/model/sync.py:51–105`) discovers DocTypes only under the folders of modules listed in `modules.txt` (`The Visa Guy, Communications, Utility, Feedback, TVG Core, TVG Business, TVG CRM`); the top-level `doctype/` folder is not scanned. Confirmed at runtime: after both `install-app` and `migrate` completed the "Updating DocTypes for the_visaguy" pass, zero `Visa Track%` DocType records or tables exist, while legacy DocTypes in real module folders (`feedback/doctype/quality_feedback`, `tvg_crm/doctype/raw_lead`) synced fine. Static tiers could not catch this: Python imports (`the_visaguy.doctype.visa_tracking_status.visa_tracking_status`) resolve regardless of Frappe's file discovery, so all 199 pure tests and `py_compile` pass.

**Defect B — the `Visa Tracking Status` fixture records lack `name` (and `modified`).** All 6 records in `the_visaguy/fixtures/visa_tracking_status.json` carry only field data (`status_code`, `status_name`, …) — verified key-by-key; every other fixture file in the app (`custom_field(s)`, `custom_docperm`, `roles`, `client_scripts`, `custom_html_block`, `insights_*`, `workspace`) has `name` on every record. Frappe's fixture importer unconditionally reads `doc["name"]` (`frappe/modules/import_file.py:125`), so both `install-app the_visaguy` and `bench migrate` abort with `KeyError: 'name'` inside `sync_fixtures → import_doc → import_file_by_path` (exact traceback captured; reproduced twice). The DocType's `autoname: field:status_code` does not help — the importer requires the literal key before any autoname logic runs. Frappe v15 imports **every** `*.json` in `fixtures/` (sorted): files before `visa_tracking_status.json` imported (some persisted via DDL implicit commit); `workspace.json` sorts after it and was not imported.

**Impact:** the_visaguy migration fails identically on this test site and would fail on production — this is a mandatory corrective before any rollout. All `the_visaguy`-dependent runtime verification (post-migration checks, on-site suites, E2E/security runtime items) is blocked by it. Per the executor contract no app code was edited and no workaround (e.g. hand-seeding the six statuses) was applied — that would mask the defect.

## 5. Backend automated tests

### 5.1 Static/pure tier (static phase, re-verified at the time at committed HEADs)

| Suite | Result | Label |
|-------|--------|-------|
| `fileflo` pure tests | **6 ran, OK** | runtime-verified (execution), source-wired (behavior) |
| `passport_extractor` pure classes | 24 pass (2 site-bound integration classes errored without a site — the then-recorded condition) | runtime-verified (execution) |
| `the_visaguy` `visa_tracking/tests` | 199 ran: 197 pass, 10 skipped, 2 pre-existing site-bound errors | runtime-verified (execution) |

### 5.2 Runtime tier on the dedicated site

| Suite | Result this phase | Label |
|-------|-------------------|-------|
| `passport_extractor` full suite | **61 ran, 61 pass, 0 errors, 0 failures** — `Ran 61 tests in 264.060s — OK` at HEAD `3486fccd` (09c; independently re-verified by the coordinator; OCR integration tests exercise the real PaddleOCR engine with preloaded models) | **runtime-verified** |
| `run-tests --app the_visaguy` | **Blocked — not executable**: the app's DocTypes do not exist on the site (§4.6 Defect A); FrappeTestCase classes would error on missing tables and pure-class results are already recorded. The previously site-bound errors (`test_lookup_service.TestLookupService`, `test_settings.TestSettings`, 4 tracking DocType modules) are now **explained**: they remain blocked by the TASK-005 placement defect, not by the environment | — |
| `run-tests --app fileflo` | Blocked for the same phase reason (run-tests bootstraps the full site context; fileflo's 6 tests are pure and already green at `fa1d6b3`, §5.1). Trigger-level runtime needs `the_visaguy` migrated (§4.6) | — |

**§4.5 of the task satisfied:** no test was executed against site `visaguy` at any point in either phase.

## 6. Frontend gates (static phase, local, `/home/shzd/Projects/tridz/visa_tracker` @ `717c62d4`)

| Gate | Command | Result | Label |
|------|---------|--------|-------|
| Lint | `npm run lint` (oxlint) | **Pass** — 0 errors, 1 warning (`react(only-export-components)` fast-refresh hint in `SessionContext.tsx`, pre-existing pattern) | runtime-verified |
| Type check | `npx tsc --noEmit` | **Pass** | runtime-verified |
| Unit/component tests | `npm test` (Vitest + RTL + MSW) | **16/16 pass** (3 files): client contract/normalization/generic/lockout/expired/no-PII-logging; form validation/focus/lockout; session context no-storage-writes | runtime-verified |
| Production build | `npm run build` | **Pass** — `dist/index.html` 0.76 kB, `dist/assets/index-*.js` 424.96 kB (136.31 kB gzip), `dist/assets/index-*.css` 28.07 kB; no sourcemaps emitted | runtime-verified |
| Build-output scan | `grep` over `dist/` | **Clean** — see §6.5 | runtime-verified |

### 6.5 Build-output secret/PII/endpoint scan

- Endpoint literals in the bundle: exactly the three whitelisted paths `/api/method/the_visaguy.visa_tracking.api.{verification.verify_identity,status.get_tracking_status,status.logout}`; **no `/api/resource/*`**.
- Host literals: only library documentation/namespace URLs (`json-schema.org`, `react.dev`, `reactrouter.com`, `w3.org`, `base-ui.com`, `localhost` dev hint). **No backend host, no real endpoint base URL** (`VITE_API_BASE_URL` is build-time config; repo carries only the `.env.example` placeholder, which does not appear in the bundle).
- `localStorage`: 0 hits. `sessionStorage`: 1 hit — React Router scroll-restoration internals (no user data). `document.cookie`: 1 hit — Axios built-in XSRF helper, dead code (XSRF not configured); the app never writes cookies (test-asserted).
- Mock fixtures (`A1****23`, `J****e`, fake token): 0 hits — MSW/mocks fully excluded from the production bundle.
- Secret-like long literals: only React internal constant names (`__CLIENT_INTERNALS_DO_NOT_USE_OR_WARN_...`, `__DOM_INTERNALS_DO_NOT_USE_OR_WARN_...`). No keys, tokens, or PII.

## 7. E2E / security / manual acceptance matrix

Statuses: `pass` / `fail` / `blocked` / `not-run`. "Static evidence" = pure tests and source wiring at committed HEADs; this does not substitute for runtime verification. All runtime `blocked` items now trace to the §4.6 TASK-005 defects (previously: absent dedicated site — resolved).

| # | Area / case | Status | Evidence |
|---|-------------|--------|----------|
| 1 | FileFlo: configured passport field triggers inspection job | `blocked` (runtime — §4.6); static: pass | 18 pure tests; hook wiring §3.4 — source-wired; fileflo app itself installed cleanly (§4.4) |
| 2 | FileFlo: non-configured field does not trigger | `blocked` (runtime — §4.6); static: pass | pure tests — source-wired |
| 3 | FileFlo: idempotent re-delivery returns existing extraction | `blocked` (runtime — §4.6); static: pass | pure tests (idempotency-key dedup) — source-wired |
| 4 | Extraction: valid MRZ → `Verified` | **`pass` (runtime)** | 61/61 dedicated-site suite incl. real-engine synthetic-MRZ cases at `3486fccd` (09c) — **runtime-verified** |
| 5 | Extraction: invalid/low-confidence → `Needs Review`; public file rejected | **`pass` (runtime)** | same suite (corrupted check digit, rotations, missing MRZ, public-file rejection) — **runtime-verified** |
| 6 | Lifecycle: Lead-only default status; PF link populates tracking link + created-status | `blocked` (runtime — §4.6); static: pass | 82→199 pure suite §5.1 — source-wired |
| 7 | Lifecycle: Client Status update → current status + exactly one log row; direct correction syncs without recursion | `blocked` (runtime — §4.6); static: pass | pure tests incl. recursion-guard — source-wired |
| 8 | Public API: HMAC verify → opaque Redis session | `blocked` (runtime — §4.6); static: pass | pure tests (token entropy/opacity, TTL, max lifetime) — source-wired; no `visa_tracker_lookup_hmac_key` value configured (configure step not reached) |
| 9 | Public API: invalid passport/DOB → generic failure (constant HTTP-200 body) | `blocked` (runtime — §4.6); static: pass | pure tests asserting byte-identical failure bodies — source-wired |
| 10 | Public API: rate limit + lockout after configured failures; `Retry-After` | `blocked` (runtime — §4.6); static: pass | pure tests (TTL, recovery, concurrency) — source-wired |
| 11 | Public API: CORS rejects disallowed origins | `blocked` (runtime — §4.6); static: pass | pure tests (wildcard/null/missing rejected, fail-closed) — source-wired; `frontend_base_url` unset (configure step not reached) |
| 12 | Frontend: SPA builds; form submits passport+DOB | `pass` (build + component tests); live-backend E2E `blocked` | §6 gates; MSW-based form tests — runtime-verified at test level |
| 13 | Frontend: status page shows masked name/passport, status, message, timeline | `pass` (component tests); live-backend E2E `blocked` | Vitest/RTL + MSW — runtime-verified at test level |
| 14 | Frontend: no sensitive values in URL/localStorage/analytics | `pass` (static + test assertions + bundle scan) | §6.5; direct test assertions (08d) — runtime-verified |
| 15 | Security/PII: raw OCR/MRZ not readable by Guest | `blocked` (runtime — §4.6 for tracking DocTypes); extraction side: schema-level pass | permlevel-1 fields + 0 Guest rules on `Passport Extraction` **runtime-verified on the dedicated site** (09a SQL); tracking DocTypes pending migration |
| 16 | Security/PII: public response boundary; no internal identifiers | `blocked` (runtime — §4.6); static: pass | response-allowlist pure tests incl. serialized-payload forbidden-value scans — source-wired |
| 17 | Reconciliation: missing-extraction and status-mismatch reports | `blocked` (runtime — §4.6); static: pass | report-only pure tests — source-wired |
| 18 | Manual: visual design parity vs `visaguy-website-client` (desktop + mobile) | **`pass` — provisional human acceptance recorded** | Human decision (relayed by the workspace coordinator): reviewer **project owner**, date **2026-07-22**, decision **provisional acceptance** of the current design language; visual beautification/polish **deferred to a planned follow-up**. No additional review evidence invented |
| 19 | Manual: browser smoke of built SPA against a live backend | `not-run` | No HTTP serving of the dedicated site was established in this phase (backend itself not migratable yet, §4.6); production site `visaguy` may not be used |

No executed matrix item failed. Items 4/5 converted to runtime-pass via the 09c suite; the remainder of the runtime matrix awaits the §4.6 corrective.

## 8. Unresolved defects, blockers, and carried deviations

1. **Blocker (mandatory gate, NEW — found by this runtime phase):** TASK-005 Defects A+B (§4.6) — `the_visaguy` cannot migrate on any site: (A) the five Visa Tracking DocType folders sit in a top-level `doctype/` folder that Frappe's module-folder scan never discovers; (B) the six `visa_tracking_status.json` fixture records lack `name`/`modified`, aborting fixture import with `KeyError: 'name'`. Requires a TASK-005 corrective task (same pattern as 09b/09c), then re-dispatch of the TASK-010 runtime remainder.
2. **Resolved since the static phase (previously blockers):** `root_password` key configured on the bench (present, count-only); dedicated site `visa-tracker-test.localhost` created by 09a and safely reused; PyMuPDF `pymupdf 1.28.0` installed in the bench env; PaddleOCR 3.7.0 with models `PP-OCRv6_medium_det/rec` and `PP-LCNet_x1_0_textline_ori` preloaded and engine-init verified (09b); bench redis services (13008/11008/12008) running.
3. **Environmental (unchanged):** bench active Node.js 12.22.9 < 18 — `bench build` fails; only relevant if app asset builds run during deployment.
4. **TASK-009 contract deviation (carried):** the backend returns constant HTTP-200 generic failures for every failure mode; mid-flow session expiry is indistinguishable from generic failure. Accepted per TASK-007 contract; flagged for product awareness.
5. **Report filename deviations (carried):** 08a/08b/08c/08d report paths differ from task files' `expected_files` (`05c/05e/05f/05g`); content is complete. Coordinator reconciliation item.
6. **TASK-007 scope deviations (carried, recorded in 08c):** logout API added per dispatch prompt; new `Visa Tracker Audit Log` DocType; three new `Visa Tracker Settings` fields.
7. **`visa_tracker` has no git remote** — per FEAT-001 scope; publishing is a human decision.
8. **Human visual-parity approval:** provisional acceptance recorded 2026-07-22 (§7 item 18); the deferred polish/beautification follow-up still needs scheduling by the project owner.
9. **Site-name drift (resolved):** TASK-002/09a referred to `passport-extractor-test.localhost`; TASK-010 specifies `visa-tracker-test.localhost` — the latter exists and was used throughout.

## 9. Validation checklist mapping (task file §Validation)

- [x] TASK-002…009 status and commit evidence reconciled (§2, §3).
- [x] `root_password` presence/absence recorded without exposing any value (§4.1 — PRESENT).
- [~] Dedicated site with required apps — site proven dedicated/nonproduction; `erpnext`, `crm`, `insights`, `processflo`, `fileflo` installed and migrated; **`the_visaguy` blocked by §4.6 defects**.
- [x] Present-key branch executed; absent-key branch not applicable; no attempt to use `visaguy` (§4, §5).
- [ ] Backend migrations/DocTypes/fixtures `present` on dedicated site — **blocked for the_visaguy** (§4.5/§4.6); passport_extractor schema verified present (09a).
- [~] Backend automated tests on dedicated site — passport_extractor **61/61 runtime-verified**; the_visaguy/fileflo on-site suites **blocked** (§5.2).
- [x] Frontend lint, type-check, production build pass (§6).
- [x] E2E/security/manual matrix documented and executed as far as the dedicated site allows (§7 — items 4/5 runtime-pass; 18 human-accepted; rest blocked by §4.6).
- [x] No sensitive value in build output, fixtures, or evidence documents (§3.5, §6.5; no config values were set or recorded this phase).
- [x] Rollout/rollback plans documented and explicitly exclude unauthorized push/deploy (`10-task-010-planning.md`).
- [x] TASK-002 runtime checks **unblocked** — 61/61 on the dedicated site (09a–09c, re-verified).

## 10. Verdict and next actions

**Rollout readiness: NOT READY.** Static gates pass, TASK-002/003 runtime is closed (61/61), the dedicated site is live with five of six required apps cleanly installed, and human visual-parity holds provisional acceptance. One mandatory gate now blocks everything else: **the TASK-005 migration defects (§4.6)** — `the_visaguy` at `d20cc6d` cannot be migrated on any site, so the post-migration verification, the the_visaguy/fileflo on-site suites, and runtime matrix items 1–3, 6–11, 15–17 cannot execute. FEAT-001 and TASK-010 must **not** be marked complete. TASK-010 stays in `tasks/in-progress/` (lifecycle reconciliation is the coordinator's action).

Exact next actions for the workspace-maintainer/coordinator:

1. **Dispatch a TASK-005 corrective task** (feature worktree, branch `feat/visa-tracker`, same pattern as 09b/09c):
   - Move the five DocType folders `visa_tracker_settings`, `visa_tracking_status`, `visa_tracking_application`, `visa_tracking_status_log`, `visa_tracker_audit_log` from `the_visaguy/the_visaguy/doctype/` into the module folder `the_visaguy/the_visaguy/the_visa_guy/doctype/` (matching their declared module "The Visa Guy"), preserving all file contents; update any workspace/import path references if the move changes them (Python imports under `the_visaguy.doctype.*` will change to `the_visaguy.the_visa_guy.doctype.*` — sweep the test modules and any `doctype` dotted-path strings).
   - Add `"name"` (one per status, matching `autoname: field:status_code`, i.e. the `status_code` value) and `"modified"` (a fixed timestamp, matching the other fixture files' convention) to all six records in `the_visaguy/the_visaguy/fixtures/visa_tracking_status.json`.
   - Re-run `install-app the_visaguy` + `migrate` on `visa-tracker-test.localhost` and the full pure suite; commit locally only (no push), environment-default Git identity.
2. **Re-dispatch the TASK-010 runtime remainder** after the corrective lands: post-migration verification (task §3.2), on-site suites (task §4.2–4.3), synthetic site configuration (HMAC key + `frontend_base_url` test origin), and runtime matrix items 1–3, 6–11, 15–17 (+19 if HTTP serving is safely available).
3. **Project owner:** schedule the deferred visual-polish follow-up (provisional acceptance already recorded, §7 item 18).
4. Only after all mandatory items pass: coordinator moves TASK-010 to `tasks/completed/` and sets FEAT-001 `status: completed`.
