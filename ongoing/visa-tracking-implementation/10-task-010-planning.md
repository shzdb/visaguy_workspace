# TASK-010 Rollout and Rollback Plan — FEAT-001 Visa Tracking

> Date: 2026-07-22
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-010 — End-to-end verification and rollout
> Companion evidence: `ongoing/visa-tracking-implementation/11-task-010-evidence.md`

**This document is procedural only.** It does not authorize, schedule, or perform any push, release, production migration, deployment, worker restart, DNS/CORS change, or secret provisioning. Every step below requires explicit human approval and execution outside this task. As of this writing the mandatory runtime gate is **blocked by a genuine TASK-005 app defect** (`the_visaguy` cannot migrate on any site — see the companion evidence document §4.6), so no rollout may begin.

---

## 1. Pre-rollout checklist (all must be green before any rollout step)

| # | Gate | Current state (2026-07-22) |
|---|------|-----------------------------|
| 1 | TASK-002 through TASK-009 implementation evidence reconciled | Pass — see `11-task-010-evidence.md` §2 reconciliation table |
| 2 | Dedicated-site runtime evidence reviewed | **Blocked — new app-level blocker** — site `visa-tracker-test.localhost` exists (created 2026-07-22 by phase 09a) and `erpnext`/`crm`/`insights`/`processflo`/`fileflo` installed cleanly on 2026-07-22; **`the_visaguy` migration fails on any site** due to two genuine TASK-005 defects (evidence §4.6): DocType folders placed outside any module folder, and status fixture records missing `name`/`modified`. Corrective required before rollout |
| 3 | Frontend gates (lint, tsc, Vitest, production build, bundle scan) | Pass — see evidence §6 |
| 4 | Human visual design-parity approval (`visa_tracker` vs `visaguy-website-client`) | **Provisionally accepted** — project owner, 2026-07-22: current design language accepted; beautification/polish deferred to a planned follow-up (evidence §7 item 18) |
| 5 | `visa_tracker_lookup_hmac_key` configured on the target bench (value never recorded in this workspace) | Not configured/verified — key name only; value provisioning is a human step |
| 6 | `visa_tracker_audit_hmac_key` (optional dedicated audit IP-hashing key) decision | Open — falls back to the lookup key when unset |
| 7 | `visa_tracker_allow_localhost_origins` unset/disabled on production | Must be verified at rollout; this is a development-only CORS override |
| 8 | Redis available with short and long queues configured and workers running | Bench has Redis (sessions/rate limits depend on it); queue topology for `passport_extractor` long-running OCR jobs must be confirmed by the operator |
| 9 | PaddleOCR model files preloaded and reachable by worker processes | **Resolved (runtime-verified 2026-07-22)** — `paddleocr 3.7.0`; models `PP-OCRv6_medium_det`, `PP-OCRv6_medium_rec`, `PP-LCNet_x1_0_textline_ori` preloaded in the bench user's cache; engine init via the app's `_get_engine()` verified (09b); real-engine OCR exercised green in the 61/61 dedicated-site suite (09c). Production workers still need the same preload on their host |
| 10 | PyMuPDF installed in the bench environment | **Resolved (runtime-verified 2026-07-22)** — `pymupdf 1.28.0` importable as `fitz` in the bench env (09a). Must also be present on the production bench before rollout |
| 11 | Bench Node.js ≥ 18 for `bench build` | **Known environmental issue** — bench active Node is 12.22.9 (TASK-001 phase 04b); required if any app asset build is run during deployment |
| 12 | Full site/database backup of the production target taken immediately before migration | Human step |
| 13 | Rollback owner and approver identified (see §6.4) | Human step |

## 2. Application and migration order (production target)

Dependency direction (ADR-003): `fileflo` emits a generic event; `the_visaguy` imports the `passport_extractor` public service and observes FileFlo/PF Process File events. Migrate in dependency order:

> **CRITICAL PREREQUISITE (found by runtime phase, 2026-07-22):** the current `the_visaguy` feature HEAD `d20cc6d4` **cannot migrate on any site** — the five Visa Tracking DocType folders sit in a top-level `doctype/` folder that Frappe's module-folder scan never discovers, and the six `visa_tracking_status.json` fixture records lack `name`/`modified`, aborting fixture import with `KeyError: 'name'` (evidence §4.6). The TASK-005 corrective (move the five folders into `the_visaguy/the_visa_guy/doctype/`; add `name`+`modified` to the fixture records) must land **before** any rollout step below.

0. **Prerequisite apps** (validated on the dedicated site 2026-07-22, install order used there): `erpnext` (ERPNext `Lead`/`Customer`), `crm` (Frappe CRM `CRM Lead`), `processflo` (owns `PF Process File`), and `insights` (`the_visaguy` fixtures reference `Insights Query`/`Insights Chart` DocTypes) must be installed **before** `the_visaguy`. This erpnext checkout declares no `required_apps` (`payments` not demanded). On the production site all four are already installed — this step is a verification, not an action.
1. **Merge/land feature branches** (human git step, outside this task): `feat/visa-tracker` into each repository's deployed base branch —
   - `passport_extractor`: base `07b8cab40cd4054b39a78f23a271d7201e71baa0` → feature HEAD `3486fccd8fc8272f93ee97d049b951d201296cad` (includes correctives 09b `cbea2159` and 09c `3486fccd`)
   - `fileflo`: base `6683010e89d9209363e6ba3881f4a90a47420bd2` (`fix/mandatory-file` is the deployed base) → feature HEAD `fa1d6b38351ef1dfc5e9a4bb66ddae22b26f7866`
   - `the_visaguy`: base `e690b5b1ac897874fb33439fa429e2aee103cc3e` (`main`) → feature HEAD `d20cc6d49cfae6c47749f8b5a94df0fa38546979` **+ the TASK-005 corrective commit** (pending)
   - `processflo`: **no change** (integration target only; its pre-existing unrelated dirty file `processflo/generate_file_collection.py` must be reconciled by its owner independently — do not deploy that dirty state blindly).
2. **Update code on the bench** to the landed revisions (human deploy step).
3. **Install/migrate in this order** on the target site:
   1. `passport_extractor` — `bench --site <site> install-app passport_extractor` if not yet installed, then `bench --site <site> migrate`. Creates the `Passport Extraction` DocType and `Passport Extractor User` role.
   2. `fileflo` — `bench --site <site> migrate` (no new DocTypes; adds the generic after-commit extension event only).
   3. `the_visaguy` — `bench --site <site> migrate`. Creates `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`, `Visa Tracker Audit Log`; imports fixtures (below).
4. **Verify post-migration state** before enabling anything:
   - All five DocTypes exist; no Guest permission rule on any tracking/extraction DocType.
   - Six initial `Visa Tracking Status` records present and active (fixture order 1–6).
   - Custom fields present on `Lead`, `CRM Lead`, `Customer` (`custom_passport_extraction`, tracking link) and `PF Process File` (`custom_visa_tracking_application`, `custom_client_status`).

## 3. Fixture, configuration, and queue steps

1. Fixtures import automatically with `the_visaguy` migrate (registered in `the_visaguy/hooks.py`): `Custom Field`, `Property Setter`, `Client Script`, `Role`, `Custom DocPerm`, `Visa Tracking Status`.
   - **Operational note (runtime-verified 2026-07-22):** Frappe v15 imports **every** `*.json` file in the app's `fixtures/` folder (sorted), not only hook-listed ones, and every fixture record must carry `name` and `modified` keys — a missing key aborts the whole migration (`KeyError: 'name'`). Fixture files for DocTypes of uninstalled apps are skipped only when the import raises `ImportError`/`DoesNotExistError`.
2. The `PF Process File` client script fixture hides/disables `custom_client_status` when no tracking application is linked — confirm it is active post-migration.
3. Configure `Visa Tracker Settings` (desk, human step):
   - `enabled = 0` and `enable_public_tracking = 0` initially (dark-launch posture).
   - Set `default_lead_status`, `process_file_created_status`, exact passport `field_id` list (one per line), `frontend_base_url` (exact https origin of the deployed SPA — required before public tracking can be enabled), session/rate-limit/lockout bounds, `generic_failure_message`, `support_link`.
   - Set the server-side HMAC key in site config (`visa_tracker_lookup_hmac_key`); never commit or record the value.
4. Queue workers: restart bench workers after migration so the new job modules load (`the_visaguy.visa_tracking.jobs.inspect_fileflo_inspection` on the short/default queue; `passport_extractor.passport_extractor.jobs.run_passport_extraction` on the **long** queue — OCR is heavyweight). Confirm a long-queue worker exists and has memory headroom for PaddleOCR; preload/warm the PaddleOCR models on workers.
5. Scheduler: no scheduler entries were added by the feature; reconciliation functions (`reconcile_missing_extractions`, `reconcile_status_mismatches`) are report-only entry points — schedule them only by explicit human decision later.

## 4. Frontend artifact handoff

- Build artifact: `visa_tracker/dist/` produced by `npm run build` at commit `717c62d402287849b30a1fd25d3760edfb727747` (this run: `dist/index.html` 0.76 kB, `dist/assets/index-*.js` 424.96 kB / 136.31 kB gzip, `dist/assets/index-*.css` 28.07 kB; no sourcemaps emitted).
- Required build-time configuration: `VITE_API_BASE_URL` pointing at the Frappe site origin that serves the whitelisted methods (see `.env.example`; placeholder only in the repo).
- The artifact contains only the three whitelisted `/api/method/the_visaguy.visa_tracking.api.*` paths, no `/api/resource/*`, no mock data, no secrets, no backend host literals (bundle scan, evidence §6.5).
- Deployment target (static host, CDN, or Frappe website route) is a human infrastructure decision; CORS requires the deployed origin to exactly match `Visa Tracker Settings.frontend_base_url`.
- `visa_tracker` currently has **no git remote** (per FEAT-001 scope); publishing the repository is a separate human decision.

## 5. Post-rollout smoke tests (synthetic data only, human-executed)

1. Upload a synthetic passport image to a configured FileFlo field → exactly one `Passport Extraction` in `Queued`, one long-queue job; non-configured field → nothing; re-delivery → no duplicate.
2. Synthetic valid-MRZ image → `Extracted`/`Verified` path with check digits stored; invalid/low-confidence → `Needs Review`; public file → rejected.
3. Lead-only tracking application gets the configured default Lead status; PF Process File link populates the tracking link and created-status; one `Client Status` update → exactly one `Visa Tracking Status Log` row; direct correction syncs PF without recursion.
4. Public API from the approved SPA origin: valid synthetic passport+DOB → opaque session token; wrong DOB → identical generic failure body (HTTP 200); 5 failures → lockout with `Retry-After`; disallowed origin → generic failure with no CORS headers.
5. SPA end-to-end in a browser: verify → masked name/passport, status, message, timeline; confirm nothing sensitive in URL/localStorage/analytics.
6. Run both reconciliation reports and confirm empty/expected output.

## 6. Monitoring

- RQ dashboard / failed-job list for `inspect_fileflo_collection` and `run_passport_extraction`; bounded retry means `Failed` extractions need operator review (no automatic re-enqueue beyond limits).
- `Visa Tracker Audit Log` review for abuse patterns (`verification_failed` categories, lockouts).
- Worker memory on the long queue (PaddleOCR is heavy — FEAT-001 risk register).
- Frappe Error Log — all feature `log_error` call sites use static PII-free titles; any new title indicates an unexpected failure path.
- Public API traffic vs. rate-limit/lockout counters (Redis key families `visa_tracker:session:*`, `visa_tracker:failed:*`).

## 7. Rollback plan

### 7.1 Feature disable (no data loss, first response)

1. Set `Visa Tracker Settings.enabled = 0` — stops FileFlo inspection, extraction orchestration, and lifecycle automation (workers no-op at the settings gate).
2. Set `Visa Tracker Settings.enable_public_tracking = 0` — public APIs return the constant generic failure; no schema or data is removed.
3. Optionally purge live public sessions and abuse counters (see §7.3).
4. Take the SPA offline or revert the static deployment to the previous artifact.

All `Passport Extraction`, `Visa Tracking Application`, status-log, and audit rows are preserved; re-enabling resumes normal operation.

### 7.2 Code reversion (if migration rollback is required)

Frappe migrations are forward-only; DocTypes/tables created by the feature remain in the database after a code revert (data preservation). Reverting code means restoring each repository to its pre-feature revision on the bench and running `bench migrate` only after a verified backup:

| Repository | Pre-feature revision to restore |
|---|---|
| `the_visaguy` | `e690b5b1ac897874fb33439fa429e2aee103cc3e` (`main`) |
| `fileflo` | `6683010e89d9209363e6ba3881f4a90a47420bd2` (`fix/mandatory-file`) |
| `passport_extractor` | `07b8cab40cd4054b39a78f23a271d7201e71baa0` (scaffold) or uninstall the app |

Note: reverting `the_visaguy` while feature DocTypes/custom fields exist in the DB leaves orphaned schema; removing them requires either a site restore from the §1.12 backup or an explicit, approved cleanup migration. Orphaned tables are inert (no code references them) and preserve audit history.

### 7.3 Redis session invalidation

To reset abuse/lockout state or invalidate all public sessions (human operator, on the bench):

- Delete session keys matching `visa_tracker:session:*` — all public SPA sessions are immediately invalidated; users must re-verify.
- Delete failure/lockout keys matching `visa_tracker:failed:*` — lifts lockouts and resets rate-limit counters.
- Keys are namespaced and contain no raw passport/DOB/IP values (HMAC buckets only), so deletion is safe and non-exposing.

### 7.4 Approval authority

- Feature disable/enable toggles: operations owner + project owner.
- Redis key purges: bench administrator with project-owner approval.
- Code reversion / site restore: project owner approval, executed by the bench administrator, only after confirming the §1.12 backup.

---

## 8. Explicit non-authorizations

This plan does **not** authorize or perform: any git push, merge, or release; any production migration or app installation; any deployment or static-host change; any worker restart; any DNS or CORS change; provisioning or recording of any secret value; any use of site `visaguy` for validation; any use of real passport or production data. Rollout remains blocked until the TASK-005 corrective recorded in `11-task-010-evidence.md` §4.6 lands and the dedicated-site runtime remainder passes; human visual-parity holds provisional acceptance (2026-07-22) with a deferred polish follow-up.
