# Visa Tracker — branch switch + install/migration verification

Goal (user): switch the respective repos to the visa tracking branch so the
feature can be tested on the main `visaguy` site; verify the app is installed
and that all code and migrations are in place.

## Ground facts (verified — do not re-derive)

- Executor: `claude -p "$(cat prompts/<file>)" --model sonnet --permission-mode bypassPermissions --add-dir /home/shzd/Projects/workspaces/visaguy_workspace`
- SSH: `ssh -p 2257 shahzad@erpcode.tridz.in`. Bench: `/home/shahzad/bench`.
  Use bare `bench` with an explicit `--site`. Never `which bench` /
  `bench --version` / `bench --help`.
- FEAT-001 code lives in REMOTE WORKTREES, not in the bench's app checkouts:
  - `/home/shahzad/visa-tracker-worktrees/the_visaguy` @ `910914e`
  - `/home/shahzad/visa-tracker-worktrees/passport_extractor` @ `3486fccd`
  - `/home/shahzad/visa-tracker-worktrees/fileflo` @ `fa1d6b38`
  - frontend LOCAL `/home/shzd/Projects/tridz/visa_tracker` @ `a6a07a9a`
  All on branch `feat/visa-tracker`. **Nothing has ever been pushed.**
- Dedicated test site `visa-tracker-test.localhost` is migrated at `910914e`.
- Site `visaguy` is PRODUCTION. Read-only unless the user explicitly authorizes
  a change. `erpcode.tridz.in` is a SHARED host — other users' `bench serve`
  processes run there; verify `ps` ownership is `shahzad` before killing.
- Prior handoff: `../visa-tracking-implementation/HANDOFF.md`.
- Open security finding (rate-limit DOB enumeration) is unresolved; see §4 there.

## Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 1 | recon: branch + install + migration state | 01-recon.md | done |
| 2 | triage + user decision (orchestrator) | 02-triage.md | done — awaiting user decision |
| 3 | switch branches / install / migrate | 03-switch.md | done — deployed + verified |
| 4 | final report | (orchestrator) | done |

## Outcome

Deployed to production `visaguy`. 4/4 tracking tables present, zero schema drift
vs the test site (29 cols), 6 status fixtures loaded, 3 whitelisted endpoints
present, `list-apps` shows all three at `HEAD` (detached — expected).
`Visa Tracker Settings` is EMPTY on visaguy, so the feature FAILS CLOSED and is
inert; configuring it is the remaining step and also activates the open
rate-limit enumeration gap. No visa_tracking errors in the prod error log.
`after_migrate` hooks were still running at report time (schema phase complete).

## Deploy facts (phase 3, established)

- User AUTHORIZED production deploy to `visaguy` on 2026-07-22 after being told
  it changes live code, writes the prod DB, and ships the open rate-limit gap.
- Prod DB backup: `/home/shahzad/bench/sites/visaguy/private/backups/20260722_202735-visaguy-database.sql.gz`
- Bench app checkouts moved to DETACHED HEAD at the feature commits (clean):
  `the_visaguy 910914e` (was `main` e690b5b), `passport_extractor 3486fcc`
  (was `develop` 07b8cab), `fileflo fa1d6b3` (was `fix/mandatory-file` 6683010).
  Detached because branch `feat/visa-tracker` is held by the linked worktrees.
  Verified: each old HEAD is an ANCESTOR of the new one — pure fast-forward.
- CORRECTED PATHS (the first prompt had these wrong):
  module `the_visaguy/the_visaguy/visa_tracking/`; doctypes under
  `the_visaguy/the_visaguy/the_visa_guy/doctype/`; Frappe module "The Visa Guy";
  5 doctypes = 4 tables + `Visa Tracker Settings` (Single, no table).
- First dispatch (`03-switch.txt`) died on a 10-min client timeout after the
  checkouts, before/during migrate. Re-dispatched as `03b` with nohup+poll.

## Decisions log

- 2026-07-22: New orchestration opened. Phase 1 is strictly READ-ONLY because
  the user's stated target (`visaguy`) is production and the feature branches
  are unpushed local-only work.

## Post-configuration verification (2026-07-22, read-only)

- User states `visaguy` is a DEVELOPMENT bench served at
  https://visaguy.erpcode.tridz.in — not production as HANDOFF.md §8 asserted.
  Update the feature docs; the "READ-ONLY production" directive is wrong.
- `frontend_base_url = http://localhost:5173` is CORRECT for local-frontend
  testing. It is used in exactly one place (`utils/security.py:38`
  `get_approved_origin`) as the sole approved CORS origin; exact-match against
  the browser's `Origin` succeeds. Sessions are opaque Redis bearer tokens sent
  in the JSON body (`api/status.py` `_parse_token_payload`), NOT cookies — so
  there is no SameSite/credentials issue. Preflight passes via site_config
  `allow_cors: "*"`. An earlier report claimed this value broke the feature;
  that was wrong.
- `passport_field_ids = "Niloofar Toreihi"` is INVALID — it is matched against
  `FF File Collection File.field_id` (`jobs.py:55`). Real field_id values on
  the site: `passport` (1), `testfile123` (23), `yahoo123` (19),
  `filetest123` (18), NULL (32309). Extraction is inert until corrected.
- `require_manual_verification` is DEAD CONFIG — zero non-test references in
  the entire app. The live auto-verification switches are
  `auto_create_tracking_application=1` and `auto_link_verified_passport=1`
  (used at `lifecycle_service.py:171`). Both already on.
- Auto-link target custom fields verified present on `visaguy` and identical to
  the test site: `custom_visa_tracking_application` +
  `custom_passport_extraction` on Lead / CRM Lead / Customer, and
  `custom_visa_tracking_application` on PF Process File.

## fileflo field_id defect (2026-07-23)

Symptom: lead CRM-LEAD-2026-00080, form filled, no Visa Tracking Application.
Evidence: 0 rows in Visa Tracking Application / Passport Extraction /
Visa Tracker Audit Log; no visa_tracking entries in Error Log. Chain never ran.

Two distinct causes:

1. DESIGN — nothing creates an application at form-fill. The only caller of
   `create_tracking_application` is `passport_extraction_handlers.py:45`
   (on Passport Extraction update). There is NO CRM Lead visa_tracking hook.
   Chain: form -> fileflo dispatch -> enqueue_fileflo_inspection -> match by
   field_id -> Passport Extraction -> create_tracking_application.

2. DEFECT (fixed) — `field_id` was destroyed for multi-upload fields.
   `data_collection.py` multi-upload branch appended replacement
   FF File Collection File rows WITHOUT `field_id`, then deleted the
   template-derived row that held it. Single-upload path mutates in place and
   kept it. Exactly correlated in live data: Emirates Id (multiple=0) kept
   `testfile123`; Passport and Residence Visa Copy (multiple=1) came through
   NULL despite the template carrying `passport` / `yahoo123`.
   Fixed on `feat/visa-tracker` @ `c7244a4` (one line + regression test
   `fileflo/tests/test_field_id_roundtrip.py`). Suite 8/8; the new test fails
   with `KeyError: 'field_id'` when the fix is reverted (verified by reverting).

Also note: `document_fetch` copies template rows into a collection only when
the collection is empty (else it throws "Document Already Exists"), so existing
collections never pick up later template changes.

State: fileflo bench checkout on branch `feat/visa-tracker` @ `c7244a4`
(rebased onto main `1746f81`). `visaguy` cache cleared. Template
FFTP-Schengen-Primary-Lead-00135 Passport row has field_id `passport`;
`passport_field_ids` setting = `passport`.

PENDING: backfill `field_id='passport'` on row `as7qri56j6` (the uploaded
"Passport - 1" row of collection Shahzad-TVGUC-0180600543) to make the existing
collection testable — blocked by the local harness permission classifier, not
attempted further.

## ROOT CAUSE (2026-07-23): the live form endpoint is visaguy_crm, not fileflo

CRM-LEAD-2026-00081 / collection Shahzad-TVGUC-0180600547: still 0 Passport
Extraction, 0 Visa Tracking Application, 0 audit rows, no RQ jobs.

The form does NOT call `fileflo.data_collection.add_form_data`. It calls
`visaguy_crm.data_collecting_form.add_form_data` (whitelisted, extra
`form_submitted` arg) — a FORK of fileflo's upload logic that has diverged.
Proof: uploaded rows are written with `multiple=0, max_allowed=1` and
`"<base> - <n>"` numbering derived from `existing_count`, which is visaguy_crm's
logic; fileflo's writes `multiple=data["multiple"]`. Collections also carry
`custom_applicant_name` / `custom_customer`, set only by visaguy_crm.

Two independent breaks in that fork:

1. `field_id` dropped. Its multi-upload branch appends uploaded rows without
   `field_id`, then REMOVES the template-derived input row
   (`ff_file_collection.remove(existing_input_row)`) and re-creates it, also
   without `field_id`. That is why BOTH Passport rows are NULL while Emirates Id
   (multiple=0, single path, mutated in place) keeps `testfile123`.

2. The extension event is NEVER dispatched. `dispatch_after_commit_extension_event`
   has ZERO references anywhere in visaguy_crm. So `enqueue_fileflo_inspection`
   never runs -> no RQ job -> no extraction -> no tracking application.
   Break 2 alone fully explains the absent RQ jobs.

Consequence: the FEAT-001 integration was wired into fileflo's `add_form_data`,
but live traffic bypasses it entirely. The fileflo fix `c7244a4` is correct in
itself but does not affect this flow.

visaguy_crm is a FOURTH repo, on `main` @ `b59c3ef`, clean, not part of the
feat/visa-tracker branch set. Fix requires a product decision (see report):
duplicate the two changes into the fork, or refactor the fork to delegate to
fileflo. Also undecided: dispatch on every save vs only when form_submitted==1.

## Correction: migrate completed (2026-07-22 16:47:45 UTC)

Earlier reports that `bench --site visaguy migrate` was "still running" in
after_migrate hooks were WRONG. The poll used
`pgrep -u shahzad -f "site visaguy migrate"`, which matched the polling
shells themselves — their own command lines contain that literal string. The
loops matched themselves indefinitely.

Actual state: migrate log `/tmp/vg-migrate.log` last written 16:47:45 UTC,
final line `Queued rebuilding of search index for visaguy` (the normal terminal
line of a successful run). All post-migrate verification in `03-switch.md`
(4/4 tables, no schema drift, fixtures loaded) was therefore taken against a
COMPLETED migration, not a partial one. Exit code was not captured because the
run was nohup'd without status capture; completion is inferred from the log's
terminal line plus the verified schema outcome.

Lesson: when polling by process name, exclude the poller — match on the
executable/pid, or grep -v the wrapper — or the loop never terminates.

Leftover: polling shells PID 1080071 and 1083107 still spinning; kill blocked
by the local permission classifier, handed to the user.

## Chain now fires end to end (2026-07-23)

After `visaguy_crm` commit `b573e2c` (field_id preserved + extension event
dispatched on every save), a real form save produced a Passport Extraction and
OCR ran. The plumbing is proven; failures are now inside extraction.

### MRZ subtype defect (fixed)

`ocr/mrz_parser.py detect_mrz_candidates` gated on
`line1[:2] not in ("P<", "PV", "PC")`. ICAO 9303 fixes only position 1 as `P`;
position 2 is issuing-state discretion. A South African passport (type `PM`,
well-formed 44-char TD3) was discarded before parsing -> `NO_MRZ_FOUND`.
`PD`/`PS`/`PP` were rejected identically.

Fixed on `passport_extractor` `feat/visa-tracker` @ `0216829`: gate on
`line1[0] != "P"`. `parse_td3_mrz` already stored `document_type = line1[:2]`
verbatim, so no downstream change was needed.

Verification: full suite **63/63** with the fix (61 baseline + 2 new). With the
old whitelist restored the new test fails for subtypes M, D, S, P
(`AssertionError: 0 != 1`) — 4 failures — proving it catches the defect.
Run tests with `--skip-test-records`; without it, ERPNext test-record setup
dies on `LinkValidationError: Could not find Warehouse Type: Transit`.

### Repo state

| repo | branch | HEAD |
|---|---|---|
| fileflo | feat/visa-tracker | c7244a4 (rebased onto main 1746f81) |
| visaguy_crm | feat/visa-tracker | b573e2c (off main b59c3ef) |
| passport_extractor | feat/visa-tracker | 0216829 |
| the_visaguy | DETACHED | 910914e |

`the_visaguy` is still detached; put it on its branch with the same
detach-worktree-then-checkout step when convenient.

### Open

- PII: RESOLVED 2026-07-23 by owner decision. `test_passport_1.png` is a real
  document, retained deliberately; `visaguy` is the owner's own site. No purge.
  Note the workspace's "synthetic passport data only" rule does not reflect this
  and should be amended to scope it to shared/production sites.
- Rate-limit DOB-enumeration gap is live and now reachable (public tracking
  enabled).
- Stray polling shells PID 1080071 / 1083107 still spinning; kill blocked
  locally, handed to the user.


## Workspace reconciliation (2026-07-23)

Workspace updated to match implementation reality. Entry points for a fresh
agent, in order:

1. `features/ongoing/visa-tracking/README.md` -> "Implementation reality"
   section: the real integration seam, all five defects, the silent config gaps.
2. `docs/operations/visa-tracking-runbook.md`: required config keys, deploy and
   restart procedure, and the diagnostic order for "no tracking application".
3. ADR-006 (rollout to `visaguy` + `visaguy_crm` seam), ADR-007 (automatic
   verification), ADR-008 (CORS delegation).
4. `tasks/in-progress/visa-tracking/TASK-010`: what is verified, what is not,
   and the four blockers to closing it.

Task lifecycle changes: TASK-002 -> completed (runtime blocker resolved, 63/63).
TASK-011 created `ready` (auto-verification tests). TASK-012 and TASK-013 created
`blocked` (rate-limit hardening; upload-logic consolidation). Risks 18-22 added.
`HANDOFF.md` header corrected — its §8 "production and READ-ONLY" and
"synthetic data only" directives were superseded by owner decision.

`apply-visaguy-crm-fix.py` was removed from this directory: it is application
code, which `.agents/rules/project-rules.md` bars from the workspace. The change
it applied is committed as `visaguy_crm b573e2c`.

### Immediate next action

Run one fresh lead + form after restarting `bench start`. The first application
(`VTA-2026-00575`) predates the HMAC key and has a NULL
`verification_lookup_hash`, so the public lookup has still never succeeded
end to end. That is the one remaining unproven link in the chain.
