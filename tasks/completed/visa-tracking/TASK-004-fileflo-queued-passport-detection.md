---
id: TASK-004
feature: FEAT-001
title: FileFlo post-persistence event and queued passport detection
status: completed
repository: fileflo, the_visaguy
owners: []
depends_on:
  - TASK-002
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# FileFlo post-persistence event and queued passport detection

## Objective

Detect passport uploads submitted through FileFlo without slowing the submission request and without teaching FileFlo anything about VisaGuy.

## Required behaviour

### Synchronous FileFlo path

The post-save handler may only receive stable identifiers, enqueue an inspection job with `enqueue_after_commit=True`, and return. It must not load settings, compare field IDs, hash or open the file, import PaddleOCR, parse MRZ, resolve Lead or Customer, or create a tracking application.

### Short queue inspection

The inspection worker must reload the persisted FileFlo record; load cached `Visa Tracker Settings`; stop when the feature is disabled; compare the persisted field ID to configured exact field IDs; validate that the value is a supported private file; compute an idempotency key; avoid duplicate extraction requests; create the `Passport Extraction`; and enqueue long-running OCR after commit.

## Constraints

- FileFlo must remain consumer-agnostic. Its only change is a generic extension point.
- Field-ID matching is exact; wildcards are excluded from the first release.
- Exactly one extraction per persisted file version.

## Validation

- A configured passport field creates exactly one extraction.
- A non-configured field creates none.
- Resubmitting the same field does not duplicate work.
- FileFlo submission latency is not materially increased.

## Definition of done

Detection is fully asynchronous and idempotent, and FileFlo carries no VisaGuy-specific code.

## Implementation evidence

`tridz-dev/FileFlo`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `7bbfb9a` | 2026-07-21 | feat: add generic post-persistence extension event |
| `c7244a4` | 2026-07-22 | fix: carry field_id onto rows created by the multi-upload path |

`7bbfb9a` adds `fileflo/events.py:dispatch_after_commit_extension_event`, a `fileflo_extension_handlers` hook list (empty by default in `fileflo/hooks.py`), a change to `fileflo/data_collection.py`, and `fileflo/tests/test_events.py` (143 lines). The dispatcher performs no business logic — it iterates registered handlers and calls `frappe.enqueue(handler, queue="short", enqueue_after_commit=True)`.

`c7244a4` adds `fileflo/tests/test_field_id_roundtrip.py` (101 lines).

`tvgglobal/the_visaguy`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `34cb477` | 2026-07-21 | feat: queue passport extraction from FileFlo |

Subscription in `the_visaguy/hooks.py`:

```
fileflo_extension_handlers = [
    "the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection",
]
```

Supporting modules: `visa_tracking/services/fileflo_inspection_service.py`, `visa_tracking/utils/idempotency.py` (56 lines), `visa_tracking/services/extraction_orchestrator.py`, `visa_tracking/tests/test_fileflo_inspection.py`.

The consumer-agnostic boundary held exactly as specified: FileFlo's diff contains no VisaGuy identifier.
