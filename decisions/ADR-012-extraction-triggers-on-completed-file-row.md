# ADR-012: Passport Extraction Triggers on a Completed FileFlo Row, Not on Upload

## Status

Accepted

Narrows ADR-004's "asynchronous processing boundary" subsection and the
required behaviour of TASK-004. ADR-004 otherwise remains in force,
including its reusable-app, private-audit-history, and verified-data
ownership sections. ADR-003's repository ownership split is unchanged:
`fileflo` still knows nothing about passports.

## Context

Until this change, passport extraction started as soon as a FileFlo
submission was persisted. The FileFlo post-persistence extension event
(`fileflo_extension_handlers`, TASK-004) fires after `add_form_data`
commits, `the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection`
enqueues the short-queue inspection, and the inspection created a
`Passport Extraction` for every row whose `field_id` matched
`Visa Tracker Settings.passport_field_ids` — regardless of what a human had
since done with that row.

Three things about the real FileFlo flow make "on persistence" the wrong
moment:

1. **A guest upload lands as `Uploaded`, not as an approved document.**
   `FF File Collection File.status` is a Select with `Uploaded`,
   `Completed`, `Rejected`. Staff review the uploaded file and mark the row
   `Completed` (approved) or `Rejected` (must be reuploaded). Extracting on
   persistence means OCR runs against files that staff have not looked at
   and may be about to reject.

2. **Reject → reupload produced repeated extraction churn.** Every
   reupload re-persisted the row and re-triggered extraction, so a client
   who uploaded the wrong page three times produced three extractions, the
   last of which was not necessarily the one staff approved.

3. **A race dropped dependant extractions entirely.** Inspection sometimes
   ran before the row's `document` link was written, so
   `resolve_fileflo_file` returned `FF_DOCUMENT_NOT_LINKED`
   (`visa_tracking/utils/provenance.py:65`) and the row was skipped. Nothing
   re-inspected when the link appeared moments later, so the extraction was
   simply never created. This was observed as missing dependant Passport
   Extractions.

An earlier fix for (3) — re-inspecting the collection when the `document`
link is written — was implemented and then **dropped by owner decision**.
It addressed the race but not (1) or (2), and it added a second trigger
edge whose only job was to compensate for the first one firing too early.

## Decision

**A configured passport row enters extraction exactly when its
`FF File Collection File.status` becomes `Completed`.** Nothing else
triggers extraction: not upload, not the `document` link being written, not
`Rejected`.

- `the_visaguy` subscribes to `FF File Collection File` via `doc_events`:
  - `on_update` → `visa_tracking.handlers.fileflo_collection_handlers.on_update`,
    which acts only when `status == "Completed"` **and**
    `has_value_changed("status")`, so re-saving an already-completed row is
    inert.
  - `after_insert` → `...fileflo_collection_handlers.after_insert`, for a
    row created already `Completed`.
- The handler stays inside ADR-004's synchronous boundary: it reads the
  row's own fields, checks the settings predicate and the configured
  `passport_field_ids`, then enqueues
  `visa_tracking.jobs.inspect_fileflo_collection` with
  `enqueue_after_commit=True` and a deterministic
  `job_id` of `visa-tracking-fileflo-inspect::<collection>::<row>`, guarded
  by `is_job_enqueued`. It opens no file, computes no hash, and imports no
  OCR code. Any exception is swallowed into `frappe.log_error` so a handler
  fault can never fail a staff member's save.
- The inspection itself is the second gate: `run_fileflo_inspection` skips
  any matched row whose status is not `Completed`, recording
  `{"action": "skipped", "reason": "ROW_NOT_COMPLETED"}` in its processed
  list. This keeps the rule true no matter which path enqueued the job.
- The backfill job (`jobs.enqueue_missing_fileflo_extractions`) and the
  read-only missing-extraction report (`reconciliation_service`) both add
  `"status": "Completed"` to their `FF File Collection File` filters, so
  neither can resurrect a row the trigger rule deliberately excluded.
- **The FileFlo generic extension event is retained, not removed.** It is
  still dispatched and still enqueues inspection; it is now simply a
  no-op for rows that are not yet `Completed`. It remains the correct
  generic seam for other consumers, and keeping it means the `fileflo` and
  `visaguy_crm` sides need no change for this decision.

Because the completion edge is a deliberate human act that happens after
the document row is fully written, it also closes the
`FF_DOCUMENT_NOT_LINKED` race in (3) as a side effect rather than by a
compensating re-inspection.

## Consequences

### Positive

- OCR runs once, on the file a human approved — the same file the case is
  actually processed against.
- Reject → reupload cycles cost nothing until approval, and produce exactly
  one extraction for the approved document.
- The dependant race is closed without a second compensating trigger.
- Worker load drops: no OCR for rejected or superseded uploads.
- The trigger edge is now legible to operations — "did anyone mark the
  passport row Completed?" is a question staff can answer.

### Negative

- **Extraction now depends on a manual step.** If staff never mark the row
  `Completed`, no extraction, no `Visa Tracking Application`, and no public
  tracking — silently, from the client's point of view. This is a new
  operational dependency and the first thing to check when a case has no
  tracking; see the runbook's diagnostic order.
- Two trigger paths now coexist (the FileFlo extension event and the
  `FF File Collection File` doc_events), both funnelling into the same
  idempotent inspection. That is deliberate but is more surface than one
  path.
- Time-to-extraction is no longer bounded by upload; it is bounded by staff
  review latency.
- Any historical row already `Completed` before this change is picked up
  only by the backfill job, not retroactively by the trigger.

## Alternatives considered

- **Re-inspect when the `document` link is written.** Implemented, then
  dropped. It fixed the race only, left OCR running on unreviewed and
  rejected files, and existed solely to compensate for triggering too
  early.
- **Trigger on upload and discard the extraction if the row is later
  rejected.** Rejected: wastes OCR on files staff will not use and leaves
  the case with extraction history it never approved.
- **Move the completion rule into `fileflo`.** Rejected: `fileflo` must
  stay unaware of passports and of `Visa Tracker Settings` (ADR-003).
- **Poll for completed rows on a schedule instead of hooking.** Rejected:
  adds latency and duplicates what the backfill job already covers as a
  safety net.

## Revisit when

Staff review stops being a reliable gate (for example, if a channel is
introduced where documents are auto-approved), `FF File Collection File`
gains additional statuses, FileFlo's approval model changes, or the
operational dependency on the `Completed` transition proves to be a
recurring cause of missing tracking applications.
