# ADR-003: FileFlo Consumer-Agnostic Post-Persistence Extension Point

## Status

Accepted

## Context

The visa tracking feature (FEAT-001) needs to react to passport files submitted through FileFlo. FileFlo is a generic document-collection app used by `visaguy_crm`, `visaguy_business`, and `visaguy_website`; it has no concept of visas, passports, leads, or tracking.

Three options existed for the integration:

1. Add passport detection directly into FileFlo.
2. Have `the_visaguy` hook FileFlo's `FF File Collection` DocType through `doc_events`.
3. Give FileFlo a generic extension point that any app can subscribe to.

Option 1 couples a generic app to one product domain. Option 2 works but puts consumer-specific matching logic on the synchronous save path of a widely used DocType, and every new consumer adds another hook.

There is also a performance constraint: FileFlo submission latency must not materially increase, and OCR is far too heavy to run in a request.

## Decision

- FileFlo exposes one generic, consumer-agnostic extension point: a `fileflo_extension_handlers` hook list, dispatched by `fileflo/events.py:dispatch_after_commit_extension_event`.
- The dispatcher performs no business logic. It iterates registered handlers and calls `frappe.enqueue(handler, queue="short", enqueue_after_commit=True)`.
- FileFlo ships the hook list empty and contains no reference to any consumer app.
- Consumers subscribe from their own `hooks.py`. `the_visaguy` registers `the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection`.
- **All** consumer logic runs in the queue — including cheap field-ID matching. The synchronous path may only pass stable identifiers and return.

## Consequences

### Positive

- FileFlo stays domain-free and reusable; its diff for FEAT-001 contains no VisaGuy identifier.
- Submission latency is unaffected regardless of how many consumers subscribe or how expensive their work is.
- `enqueue_after_commit=True` guarantees handlers never observe uncommitted state.
- New consumers require no change to FileFlo.

### Negative

- Debugging spans a queue boundary; a failed handler does not surface in the submitting user's request.
- Handlers must be individually idempotent, because FileFlo makes no delivery guarantees beyond enqueueing.
- A misbehaving handler can saturate the `short` queue for unrelated work.

## Alternatives considered

- **Passport logic inside FileFlo.** Rejected: couples a generic app to one product domain and makes FileFlo un-reusable.
- **`doc_events` on `FF File Collection` from `the_visaguy`.** Rejected: puts consumer matching on the synchronous save path of a shared DocType, and does not generalise.
- **Synchronous field-ID match, queued OCR only.** Rejected: even settings loading and field comparison were deemed too much work for the request transaction, and it leaks consumer config concerns into the save path.

## Revisit when

FileFlo needs ordered or transactional delivery to consumers, a consumer requires a synchronous response to block submission, or queue saturation from extension handlers becomes an observed problem.
