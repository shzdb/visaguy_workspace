---
id: TASK-022
feature: FEAT-001
title: Link PF Process Files to their Visa Tracking Application
status: completed
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-014
created: 2026-09-13
updated: 2026-10-23
---

# TASK-022: Link PF Process Files to their Visa Tracking Application

Recorded after the fact. The owner did this work on the bench on 2026-09-03
and 2026-09-07. This document records it against the source.

## Objective

Make the public status endpoint return a primary's dependants, by linking
each `PF Process File` to the `Visa Tracking Application` it belongs to.

## Context

`api/status.py` builds `dependants` only when
`Visa Tracking Application.process_file` is set. Nothing set it:
`lifecycle_service.link_process_file_to_tracking()` had no caller. Brief:
`ongoing/process-file-tracking-link/PROMPT.md`. Ownership rule: ADR-014.

## Changes

`the_visaguy` `b99dea7` (2026-09-03, "fix dependants display in visa tracking apis"):

- `hooks.py` — `PF Process File` `after_insert` →
  `process_file_handlers.after_insert`; `FF File Collection` `on_update` →
  `fileflo_collection_handlers.on_collection_update` (see ADR-012
  amendment); `Visa Tracking Status` added to `fixtures`.
- `handlers/process_file_handlers.py` — `after_insert` links a new Process
  File; `on_update` retries the link when `file_collection` or
  `custom_lead_file_collection` changes on an unlinked Process File.
- `services/lifecycle_service.py` — the resolver implements ADR-014 (either
  collection field, Lead Link never used, flag on more than one match);
  `_find_process_file_for_file_collection` and
  `_maybe_link_process_file_for_application` link from the application side
  on create and on reuse.
- `handlers/fileflo_collection_handlers.py` — parent-collection trigger and
  one inspection job id per collection (ADR-012 amendment).
- Tests in `test_lifecycle_service.py`, `test_fileflo_inspection.py`,
  `test_pf_process_file_status_trigger.py`.

`the_visaguy` `d59614f` (2026-09-07, "fix: write PF tracking link without a mid-flight save"):

- `link_process_file_to_tracking(name, document=None)` writes the Link with
  `db.set_value(update_modified=False)` and mirrors it onto the caller's
  document. The earlier `pf.save()` broke Lead-to-Process-File conversion
  with `TimestampMismatchError`.
- Tests in `test_lifecycle_service.py` and
  `test_pf_process_file_status_trigger.py`.

## Validation

- 2026-09-13, pure tier
  (`python -m unittest discover -s the_visaguy/visa_tracking/tests`):
  **286 run, 19 skipped, 2 errors.** Both errors are the known
  `TestProcessFileHandler` site-context errors (`AttributeError: site`),
  recorded before this work.
- 2026-09-13, data on site `visaguy` (read-only query): 4 of 3,875
  `PF Process File` rows have `custom_visa_tracking_application`; 4 of 11
  `Visa Tracking Application` rows have `process_file`. The linking path
  runs on real data.
- On-site tier, 2026-09-14
  (`bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`,
  bench Redis started for the run and stopped after): first run 382 tests,
  3 errors in `TestRepairClientStatusDriftIntegration`. The `after_insert`
  link hook saved the application while the fixture held a stale copy.
  Fixture fixed in `the_visaguy` `8cf4c64`; re-run **382 tests, OK**.

## Owner decisions (2026-09-13)

- **No backfill.** The 3,871 unlinked Process Files are older files created
  before linking existed. They stay unlinked by design. Only Process Files
  created or changed from now on are linked.
- **Reinstate the drift sweep.** `the_visaguy` `6221926` ("fix: schedule the
  client status drift sweep hourly again") puts
  `jobs.run_client_status_reconciliation_sweep` back under `hourly` in
  `scheduler_events` and replaces the stale "no PF Process File is linked"
  comment. `repair_client_status_drift` filters on
  `custom_visa_tracking_application is set`, so the older unlinked files
  are never scanned. Validation: `scheduler_events` parsed with `ast`
  shows the `hourly` entry; pure tier unchanged at 286 run / 19 skipped /
  2 known errors. Pushed 2026-09-14.

## What remains

1. ~~Re-run the on-site tier.~~ Done 2026-09-14, 382 OK (see Validation).
2. `6221926` and `8cf4c64` pushed 2026-09-14. Deploy. The deploy's migrate registers the hourly
   Scheduled Job Type.

## Completion (2026-10-23)

Moved to `completed` by a workspace maintenance pass.

- **Deployment evidence:** owner confirmation, 2026-10-23: everything merged
  to `main` up to the 2026-10-20 go-live is deployed on live, including
  tridz-dev/passport_extractor#5 and tvgglobal/the_visaguy#47, and the
  `visa_tracker` frontend is live.
- **Merge evidence (GitHub compare, 2026-10-23):** every commit listed in
  this task is contained in `main` as of the go-live: `the_visaguy`
  `4f3d063`, `passport_extractor` `a2f5a4a`, `visaguy_crm` `daa863e`,
  `visa_tracker` `654b9f0`, `fileflo` `main`.
- **Validation:** as recorded above in this task (pure and on-site suites on
  `visa-tracker-test.localhost`).
- **Known limitations:** owner checks other than deployment that are listed
  under "What remains" (browser or desk checks, printed patch counts) were
  not recorded in the workspace.
