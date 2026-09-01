---
id: TASK-010
feature: FEAT-001
title: End-to-end verification and rollout
status: in-progress
repositories:
  - visaguy_workspace
  - the_visaguy
  - fileflo
  - passport_extractor
  - visa_tracker
  - processflo
owners: []
depends_on:
  - TASK-002
  - TASK-003
  - TASK-004
  - TASK-005
  - TASK-006
  - TASK-007
  - TASK-008
  - TASK-009
  - ADR-003
  - ADR-004
  - ADR-005
expected_files:
  - ongoing/visa-tracking-implementation/10-task-010-planning.md
  - ongoing/visa-tracking-implementation/11-task-010-evidence.md
created: 2026-07-21
updated: 2026-07-23
---

# TASK-010: End-to-end verification and rollout

## Objective

Serve as the final integration and quality gate for FEAT-001 by reconciling implementation evidence from TASK-002 through TASK-009, running safe static and runtime validation on an isolated dedicated test site, verifying the React SPA build pipeline, executing an end-to-end/security/manual acceptance matrix, and producing a rollback-aware rollout plan. This task is planning and evidence-recording only; it must not edit application code, push commits, deploy to production, run migrations or tests on site `visaguy`, or handle secrets/PII.

## Context

FEAT-001 implementation is split across four application repositories plus one read-only design reference. TASK-002 through TASK-009 deliver specific increments:

- TASK-002 — `passport_extractor` data model, controller, and tests.
- TASK-003 — PaddleOCR/MRZ extraction pipeline.
- TASK-004 — FileFlo queued passport detection.
- TASK-005 — tracking data model, settings, custom fields, and fixtures.
- TASK-006 — tracking lifecycle and status synchronization.
- TASK-007 — public verification/status API and security controls.
- TASK-008 — frontend scaffold and design parity.
- TASK-009 — public tracking SPA flow.

TASK-010 is the final gate. It reconciles the status of every preceding task, unblocks the runtime verification that TASK-002 deferred because the bench lacked a configured database `root_password`, and produces a complete, reviewable rollout package. Any unresolved blocker must be recorded explicitly rather than worked around by using the active `visaguy` site.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- `tasks/completed/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- `tasks/in-progress/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md`
- `tasks/ready/visa-tracking/TASK-003-passport-ocr-and-mrz-pipeline.md`
- `tasks/ready/visa-tracking/TASK-004-fileflo-queued-passport-detection.md`
- `tasks/ready/visa-tracking/TASK-005-tracking-data-model-and-settings.md`
- `tasks/ready/visa-tracking/TASK-006-tracking-lifecycle-and-status-sync.md`
- `tasks/ready/visa-tracking/TASK-007-public-api-and-security-controls.md`
- `tasks/ready/visa-tracking/TASK-008-frontend-scaffold-and-design-parity.md`
- `tasks/ready/visa-tracking/TASK-009-frontend-tracking-flow.md`
- Feature worktrees on the remote bench:
  - `/home/shahzad/visa-tracker-worktrees/the_visaguy` on branch `feat/visa-tracker`
  - `/home/shahzad/visa-tracker-worktrees/fileflo` on branch `feat/visa-tracker`
  - `/home/shahzad/visa-tracker-worktrees/passport_extractor` on branch `feat/visa-tracker`
- Local frontend repository: `/home/shzd/Projects/tridz/visa_tracker`
- Remote Frappe bench: `/home/shahzad/bench` on `erpcode.tridz.in:2257`
- Active site (read-only reference): `visaguy`
- Dedicated test site (create only when safe): `visa-tracker-test.localhost`

## Required behaviour

### 1. Pre-flight evidence reconciliation

1.1. Read the current status of TASK-002 through TASK-009 and record whether each is `completed`, `runtime-blocked`, or otherwise incomplete.

1.2. For each preceding task, collect:

- final commit SHA(s) in the relevant feature worktree,
- which validation items passed statically,
- which validation items remain runtime-deferred,
- any recorded blockers or deviations.

1.3. Produce a reconciliation table in `ongoing/visa-tracking-implementation/11-task-010-evidence.md` showing task, repository, branch, base SHA, final SHA, static status, runtime status, and open blockers.

1.4. If any task other than TASK-002 has outstanding runtime verification that TASK-010 is intended to unblock, surface it in the same evidence document.

### 2. Dedicated isolated test site

2.1. Inspect `/home/shahzad/bench/sites/common_site_config.json` for the presence of a database `root_password` key. Record only whether the key is present; never print, copy, or expose its value.

2.2. **If the key is present**, create a new dedicated test site named `visa-tracker-test.localhost`. Use this site for all backend migrations, app installations, queue configuration, and tests.

2.3. **If the key is absent**, do not create the site, do not request the password, do not guess it, and do not reuse site `visaguy`. Record the exact blocker in `ongoing/visa-tracking-implementation/11-task-010-evidence.md` and stop runtime validation. The task remains `ready` with a documented blocker; it does not become `completed`.

2.4. If site creation fails for any other reason (permissions, disk space, existing site conflict, Redis/DB unavailable), record the exact error and stop; do not fall back to `visaguy`.

2.5. On the dedicated site, install only the apps required for FEAT-001 verification: Frappe, ERPNext, and the four feature apps (`the_visaguy`, `fileflo`, `passport_extractor`, plus any dependencies evidenced in TASK-001). Do not install unrelated apps from the `visaguy` site.

### 3. Backend migration and static validation on the dedicated site

3.1. With feature worktrees first on `PYTHONPATH`, run `bench --site visa-tracker-test.localhost migrate` for each changed app as needed. Record the result.

3.2. Verify that the following DocTypes and fixtures are present after migration:

- `passport_extractor`: `Passport Extraction`
- `the_visaguy`: `Visa Tracker Settings`, `Visa Tracking Status`, `Visa Tracking Application`, `Visa Tracking Status Log`
- `the_visaguy`: custom fields on Lead, Customer, and `PF Process File`
- `the_visaguy`: initial `Visa Tracking Status` records seeded via fixtures or installation logic

3.3. Verify that `passport_extractor` remains dependency-free: no imports from `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, or Visa Tracking Application.

3.4. Verify that `fileflo` remains dependency-free of `passport_extractor` and `Visa Tracker Settings`.

3.5. Verify that `the_visaguy` imports `passport_extractor` only through its public service API and observes FileFlo/PF Process File events only through documented hooks.

### 4. Backend automated tests on the dedicated site

4.1. Run `bench --site visa-tracker-test.localhost run-tests --app passport_extractor` and record pass/fail counts.

4.2. Run `bench --site visa-tracker-test.localhost run-tests --app the_visaguy` for FEAT-001 test modules and record pass/fail counts.

4.3. Run `bench --site visa-tracker-test.localhost run-tests --app fileflo` for FEAT-001 test modules and record pass/fail counts.

4.4. If any test suite fails, record the failing test names and high-level failure reasons. Do not alter production data or retry on `visaguy`.

4.5. Confirm that no test was executed against site `visaguy`.

### 5. Frontend lint, build, and unit tests

5.1. In `/home/shzd/Projects/tridz/visa_tracker`, run the lint command recorded in `package.json` and capture the result.

5.2. Run the TypeScript type-check command and capture the result.

5.3. Run the production build command and confirm that `dist/` is produced without errors.

5.4. If the repository has unit or component tests, run them and record the result.

5.5. Inspect build output for accidental inclusion of secrets, full passport numbers, or internal API endpoints. Record the finding.

### 6. End-to-end, security, and manual acceptance matrix

6.1. Design and document an E2E test matrix in `ongoing/visa-tracking-implementation/11-task-010-evidence.md` covering at least:

| Area | Cases |
|------|-------|
| FileFlo upload | Configured passport field triggers inspection job; non-configured field does not; idempotent re-delivery returns existing extraction. |
| Extraction pipeline | Valid MRZ produces `Verified` extraction; invalid/low-confidence produces `Needs Review`; public file is rejected. |
| Tracking lifecycle | Lead-only stage uses default Lead status; Process File linking populates tracking Link and created-status; Client Status update changes current status and creates exactly one log row; direct correction synchronizes without recursion. |
| Public API | HMAC verification returns opaque Redis session; invalid passport/DOB returns generic failure; rate limiting and lockout trigger after configured failures; CORS rejects disallowed origins. |
| Frontend | SPA builds; form submits passport+DOB; status page displays masked name, masked passport, status, message, timeline; no sensitive values in URL/localStorage/analytics. |
| Security/PII | Raw OCR/MRZ not readable by Guest; public response boundary enforced; no internal identifiers exposed. |
| Reconciliation | Configured FileFlo uploads missing extraction are reported; PF/tracking status mismatches are reported. |

6.2. Execute the matrix that can be safely run against the dedicated test site and local frontend dev server or build preview. Record each result as `pass`, `fail`, `blocked`, or `not-run` with evidence labels.

6.3. For manual-only steps (for example visual design parity review), document the exact reviewer, date, and approval status.

6.4. Use only synthetic/fake passport data and obviously fake PII in all tests. Do not use production data or real passport samples.

### 7. Evidence and status reconciliation

7.1. Update `ongoing/visa-tracking-implementation/11-task-010-evidence.md` with:

- final static validation results,
- dedicated test site creation result and exact blocker if skipped,
- migration results per app,
- automated test results per app,
- frontend lint/type-check/build/test results,
- E2E/security/manual matrix results,
- unresolved defects or blockers,
- verification labels (`present`, `source-wired`, `configured-unverified`, `runtime-verified`) for each claim.

7.2. If all preceding tasks, migrations, tests, frontend checks, and matrix items pass, update the FEAT-001 feature document metadata `status` to `completed` and move TASK-010 to `tasks/completed/visa-tracking/`.

7.3. If any item fails or the dedicated test site cannot be created, leave TASK-010 in `tasks/ready/visa-tracking/`, record the blocker, and do not mark FEAT-001 complete.

### 8. Rollback and rollout plan

8.1. Produce a rollout plan in `ongoing/visa-tracking-implementation/10-task-010-planning.md` that includes:

- pre-rollout checklist (all TASK-002 through TASK-009 complete, dedicated-site evidence reviewed, HMAC key configured, Redis queues configured, PaddleOCR models preloaded),
- order of app installs/migrations on the production target,
- fixture and custom-field installation steps,
- queue worker restart requirements,
- frontend deployment artifact (`visa_tracker/dist/`) handoff notes,
- post-rollout smoke tests.

8.2. Produce a rollback plan covering:

- how to disable `Visa Tracker Settings.enabled` and `enable_public_tracking` without data loss,
- how to revert each app to its pre-feature state if migration rollback is required,
- how to clear Redis session keys if abuse/lockout needs reset,
- who must approve rollback.

8.3. The plan must **not** authorize or execute any push, deploy, production migration, or release. It is a documented procedure for human approval and execution outside this task.

## Constraints

- Work only in `/home/shzd/Projects/workspaces/visaguy_workspace` and the explicitly named application worktrees/repositories.
- This task is planning and verification only. Do not implement new feature logic, DocTypes, APIs, OCR logic, or SPA screens.
- Do not push to any Git remote.
- Do not deploy to any environment.
- Do not run migrations, tests, or any write operation on active site `visaguy`.
- Do not create the dedicated test site unless the bench has a configured database `root_password` key.
- Do not request, print, copy, or expose any password, secret, or PII.
- Do not use real passport data or production data in any test.
- Do not alter unrelated dirty working trees (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`).
- Do not modify `visaguy-website-client`.
- Record only environment variable names and configuration key names, not values.

## Expected changes

- `ongoing/visa-tracking-implementation/10-task-010-planning.md` — rollout and rollback plan.
- `ongoing/visa-tracking-implementation/11-task-010-evidence.md` — reconciliation table, static/runtime validation results, E2E/security/manual matrix, and exact blocker if runtime validation is skipped.
- Possible metadata/status updates to `features/ongoing/visa-tracking/README.md` and TASK-010 itself if all gates pass.

No application code, schema, fixture, build output, or secret is committed from this task.

## Validation

- [ ] TASK-002 through TASK-009 status and commit evidence are reconciled.
- [ ] Presence or absence of the bench database `root_password` key is recorded without exposing the value.
- [ ] If the key is present, `visa-tracker-test.localhost` exists and has the required apps installed.
- [ ] If the key is absent, the exact blocker is recorded and no attempt was made to use site `visaguy`.
- [ ] Backend migrations succeed on the dedicated test site (when available) and required DocTypes/fixtures are `present`.
- [ ] Backend automated tests for `passport_extractor`, `the_visaguy`, and `fileflo` run on the dedicated test site and results are recorded.
- [ ] Frontend lint, type-check, and production build pass in `/home/shzd/Projects/tridz/visa_tracker`.
- [ ] E2E/security/manual acceptance matrix is documented and executed as far as the dedicated site allows.
- [ ] No sensitive value appears in build output, test fixtures, or evidence documents.
- [ ] Rollout and rollback plans are documented and explicitly exclude unauthorized push/deploy.
- [ ] TASK-002 runtime checks are unblocked or their deferral is explicitly recorded.

## Definition of done

- The task file itself is created at `tasks/ready/visa-tracking/TASK-010-end-to-end-verification-and-rollout.md` with status `ready`.
- Planning documents `10-task-010-planning.md` and `11-task-010-evidence.md` exist when this task is executed.
- All TASK-002 through TASK-009 evidence is reconciled.
- Dedicated test-site runtime validation is either completed on `visa-tracker-test.localhost` or blocked by a recorded, exact environmental condition.
- No migration, test, or write operation was performed on site `visaguy`.
- No push, deploy, secret, PII, or production data handling occurred.
- TASK-010 is moved to `tasks/completed/visa-tracking/` only when every validation item passes; otherwise it remains `ready` with documented blockers.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Missing implementation evidence**: a preceding task claims completion but cannot produce commit SHAs, test results, or static validation evidence.
2. **Unexpected dependency leak**: runtime/static inspection reveals `passport_extractor`, `fileflo`, or `visa_tracker` violates the dependency directions in ADR-003.
3. **Unsafe test-site fallback**: any tool, script, or instruction attempts to run FEAT-001 migrations or tests on site `visaguy`.
4. **Secret or PII exposure**: a password value, real passport number, MRZ text, or production PII appears in logs, evidence files, or build output.
5. **Unresolvable runtime blocker**: the dedicated test site cannot be created for a reason other than missing `root_password`, and no safe alternative exists.
6. **Permission denial**: any required repository, bench, or site operation is denied by host policy or user approval.

## Completion notes

TASK-010 is the final FEAT-001 gate. It does not implement feature code; it verifies that TASK-002 through TASK-009 are internally consistent, runtime-validated on an isolated test site, and ready for human-approved rollout. If the isolated test site remains unavailable because the bench lacks a configured `root_password`, the exact blocker is recorded and the task stays `ready` until the environment is unblocked.


## Progress and scope deviation (2026-07-23)

**Status remains `in-progress`.** Substantial evidence now exists, but this task
was executed outside its own stated constraints and its isolation guarantee is
weakened. Do not close it without reading this section.

### Authorised deviation from the stated scope

This task states it "must not edit application code, push commits, deploy to
production, run migrations or tests on site `visaguy`". During 2026-07-22/23 the
project owner explicitly authorised, and the work performed:

- deploying `feat/visa-tracker` to site `visaguy` and migrating it;
- editing application code in four repositories to fix defects found at runtime;
- adding a fifth repository, `visaguy_crm`, to the feature.

The owner also clarified that `visaguy` is a **development bench**, not
production — the premise behind the original prohibition was inaccurate. See
**ADR-006**, which records the deviation, the rollback points, and the database
backup taken beforehand. Commits remain **local and unpushed** in every
repository.

### What is now verified

- Schema on `visaguy`: 4/4 tracking tables, **zero drift** against
  `visa-tracker-test.localhost` (`tabVisa Tracking Application`, 29 columns
  both), 6/6 status fixtures loaded, 3 whitelisted endpoints present, custom
  fields present on Lead / CRM Lead / Customer / PF Process File.
- The full chain is **runtime-verified end to end** on real form traffic:
  form save -> `field_id` preserved -> extension event -> RQ inspection job ->
  `Passport Extraction` (OCR + MRZ parsed correctly from a real passport) ->
  `Visa Tracking Application` created and linked to the lead.
- Suites: `passport_extractor` 63/63, `fileflo` 8/8. Both re-verified by
  reverting each fix and confirming the new tests fail.
- CORS: preflight and actual request both correct from the local frontend
  origin after ADR-008.

### What is NOT yet verified

- **The public lookup has never succeeded end to end.** The first application
  (`VTA-2026-00575`) was created before the lookup HMAC key existed, so its
  `verification_lookup_hash` is NULL and `tracking_enabled` is 0. It cannot be
  repaired in place; a fresh run is required. This is the immediate next step.
- **Automatic verification (ADR-007) has no tests.** The code compiles and is
  deployed but its behaviour is unproven — see TASK-011.
- E2E matrix item 19, browser leg: wire conformance is proven, but no browser
  has driven the full flow against the live backend.
- `the_visaguy` suite (248 baseline) has not been re-run since the
  `response_service` CORS change.
- Rollout plan and rollback rehearsal remain unwritten.

### Blockers to closing this task

1. One clean end-to-end public lookup against a freshly created application.
2. TASK-011 (auto-verification tests).
3. A decision on risk 18 (rate-limit enumeration), which is **live and now
   reachable** — see TASK-012.
4. Owner decision on pushing four repositories of unpushed commits.
