---
id: TASK-044
feature: FEAT-001
title: Run passport OCR on its own passport_extraction queue
status: in-progress
repository: passport_extractor, the_visaguy
app_path: /home/shahzad/bench/apps/passport_extractor
owners: []
depends_on:
  - TASK-042
expected_files:
  - passport_extractor/passport_extractor/extraction_queue.py
  - passport_extractor/hooks.py
  - passport_extractor/passport_extractor/api.py
  - passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction_list.js
  - passport_extractor/passport_extractor/tests/test_extraction_queue.py
  - the_visaguy/the_visa_guy/doctype/visa_tracker_settings/visa_tracker_settings.json
  - the_visaguy/visa_tracking/services/extraction_orchestrator.py
created: 2026-10-19
updated: 2026-10-19
---

# TASK-044: Run passport OCR on its own queue

## Objective

Owner (2026-10-19): OCR runs on `long` and takes minutes per file. Give it a
dedicated queue with two workers, set up the way `frappe_conversions_api`
sets up `capi`, and give a way to move jobs already waiting on `long` to it.
This reverses the TASK-042 scope note "a separate worker queue is out of
scope".

## Owner decisions

- Queue `passport_extraction`, 2 workers, 1800 s timeout (slowest pilot file
  about 560 s; 1–2 GB memory per job).
- A stop-and-restart action for jobs already queued on `long`.

## Required behaviour

### passport_extractor (`extraction_queue.py`)

- `after_install` and `after_migrate` add
  `workers.passport_extraction = {timeout: 1800, background_workers: 2}` to
  `common_site_config.json` when it is missing. An existing entry is not
  changed.
- `get_extraction_queue()` returns `passport_extraction` when Frappe knows the
  queue, else `long`. `frappe.enqueue` raises on an unknown queue, so all
  enqueues go through it.
- `resolve_queue(queue)` keeps a known queue, else uses
  `get_extraction_queue()`.
- The Retry action (`create_retry_extraction`) uses the resolved queue
  instead of `long`.
- `requeue_pending_extractions(dry_run=1)`, System Manager only, list view
  button "Requeue Pending Extractions" (dry run, then confirm) and
  `bench execute`. For each `Queued` or `Processing` record:
  - job running now: left alone;
  - job waiting on another queue: cancelled and enqueued on the new queue;
  - job waiting on the new queue: left alone;
  - no live job (lost in a restart, failed, finished without result): set
    back to `Queued` (with a comment, since Processing → Queued is not a
    controller transition) and enqueued again.

### the_visaguy

- Visa Tracker Settings → Extraction Queue gains `passport_extraction` and
  defaults to it (the stored value on existing sites does not change).
- The orchestrator resolves the setting through `passport_extractor`, so an
  unconfigured queue falls back to `long` instead of breaking uploads.

## Live setup

See `features/ongoing/visa-tracking/08-go-live-checklist.md`, section
"Passport extraction queue".

## Validation

- Pure tests: `passport_extractor` `tests/test_extraction_queue.py`
  (config added and kept, resolution and fallback, requeue categories, dry
  run, System Manager, retry queue); `the_visaguy`
  `test_fileflo_inspection.py` (configured queue used, unconfigured falls
  back to `long`).
- Not run: the on-site suites and a real `bench migrate` on the test site.
  Switching the bench's installed checkouts needs the owner's permission
  (they are shared with `visaguy`).

## Results (2026-10-19)

- `passport_extractor` pure tests: 109 OK.
- `the_visaguy` pure tests: 720 run, 2 errors (the known
  `TestProcessFileHandler` site-context cases), 20 skipped.
- PRs: https://github.com/tridz-dev/passport_extractor/pull/5,
  https://github.com/tvgglobal/the_visaguy/pull/47

## Definition of done

- Pure tests pass; PRs open; owner runs the on-site suites after merge,
  deploys, and follows the live setup steps.
