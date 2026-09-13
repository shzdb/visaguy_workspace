---
id: TASK-022
feature: FEAT-001
title: Link PF Process Files to their Visa Tracking Application
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-014
created: 2026-09-13
updated: 2026-09-13
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
- On-site tier: **not run.** The 2026-09-13 attempt could not start because
  Redis Queue on the bench refused connections. The last green on-site run
  (366, 2026-09-03) predates both commits.

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
  2 known errors. Committed locally, not pushed.

## What remains

1. Re-run the on-site tier on `visa-tracker-test.localhost` when Redis Queue
   is up: `bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`.
2. Push `the_visaguy` `feat/visa-tracker` (`6221926` is local), then deploy.
   The deploy's migrate registers the hourly Scheduled Job Type.
