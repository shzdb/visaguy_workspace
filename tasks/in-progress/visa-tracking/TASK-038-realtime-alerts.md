---
id: TASK-038
feature: FEAT-001
title: Realtime alerts for visa tracking in the desk
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-031
  - TASK-032
  - TASK-033
expected_files:
  - the_visaguy/visa_tracking/services/alert_service.py
  - the_visaguy/visa_tracking/handlers/process_file_handlers.py
  - the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py
  - the_visaguy/visa_tracking/jobs.py
  - the_visaguy/fixtures/client_scripts.json
created: 2026-09-28
updated: 2026-09-28
---

# TASK-038: Realtime alerts for visa tracking in the desk

## Owner decisions (2026-09-28)

- Q1: **no bell notifications (Notification Log) for now.** Realtime toasts only.
- Q2: the save toast (A1) is shown **only to the three tracking roles**
  (Operations Associate, Operations Team Lead, System Manager).
- Q3: **no headline (A7 dropped).** A Process File is created only after its
  mandatory file rows are Completed (`visaguy_crm`
  `allocated_to_process_file.check_lead_verification`). Note: that check skips
  rows with a blank status and non-mandatory rows; the coverage report
  (TASK-035) covers those rare files.

## Current state (verified 2026-09-28, `the_visaguy` `3872390`, `passport_extractor` `84da2fe`)

- No `frappe.publish_realtime`, Notification Log or server-side alert in
  `the_visaguy.visa_tracking` or `passport_extractor`.
- Feedback exists only for direct clicks:
  - **Generate Visa Tracking** / **Retry passport extraction**: a dialog
    with the synchronous diagnosis, then "refresh in a few minutes".
  - Passport Extraction **Verify** / **Retry**: a toast.
- Everything that happens in a background job is silent until the user
  reloads:
  - a Process File save enqueues `ensure_tracking` — no feedback;
  - the extraction finishes (`Extracted`, `Needs Review`, `Failed`);
  - the application is created and linked (written with
    `db.set_value`, so Frappe sends no document update to the open form);
  - the client status is recomputed after a workflow change (queued job);
  - review flags (same passport twice in one Lead, applicant row not
    resolved, no destination) go only to Error Log, which operations users
    do not read.
- Infrastructure: socket.io runs on the bench (port 9069); one worker serves
  all queues; background jobs can publish realtime events through
  `redis_socketio`. Open forms join the document room
  (`doc:PF Process File/<name>`) automatically.

## Proposed behaviour

One service `alert_service.notify_process_file(process_file, outcome, **details)`
used by every step. It publishes
`frappe.publish_realtime("visa_tracking_update", {...}, doctype="PF Process File", docname=<pf>, after_commit=True)`
No Notification Log (Q1).

| # | When | Who sees it | What |
|---|---|---|---|
| A1 | A save enqueues tracking | The user who saved (toast after the save response, `msgprint(alert=True)`) | "Visa tracking: checking the passport for this file." Only when the job is newly enqueued; tracking roles only (Q2). |
| A2 | The ensure job ends | Everyone with the file open (realtime) | Toast with the outcome message (the TASK-031 messages), coloured green / orange / red. |
| A3 | Extraction ends `Needs Review` / `Failed` / `Verified` | Everyone with the file open | "Passport needs review", "Passport extraction failed: <reason>", "Passport verified". |
| A4 | Application created and linked | Everyone with the file open | Toast "Visa Tracking Application created" and the form reloads if it has no unsaved changes, so the link, section and buttons update. |
| A5 | Client status recomputed | Everyone with the Process File or the Application open | Toast "Client status is now <public title>" and reload if not dirty. |
| A6 | Review flag (duplicate identity, applicant row, destination) | Everyone with the file open | Toast in red with the TASK-031 message. |
| A7 | (dropped, Q3) | – | – |

Client side: one listener in the TASK-031 client script
(`frappe.realtime.on("visa_tracking_update", ...)`), registered once per
form (remove it on unload), that checks `docname`, calls
`frappe.show_alert`, and `frm.reload_doc()` when `!frm.is_dirty()`.

## Constraints

- No passport values in any message or notification.
- Every publish uses `after_commit=True`, so a client never reloads before
  the data is committed.
- A failure to publish never breaks a job or a save.
- Client messages to applicants (WhatsApp) are out of scope (soft-launch
  plan D7).

## Validation

- Pure tests: each step calls `notify_process_file` with the right outcome;
  publish arguments (event, doctype, docname, after_commit); no passport
  values in payloads; no Notification Log is written; A1 only for the
  three roles.
- Test site: with a Process File form open in a browser, save → A1 toast;
  run the jobs → A2/A4 toasts and automatic reload; change workflow →
  A5 toast; review flag → A6.

## Definition of done

Validation passes and the commit SHA is recorded here.

## Implementation (2026-09-28)

`the_visaguy` `d9644c4`, merged into `feat/visa-tracker` as `ed1590d` on the bench. Not pushed or deployed.

Evidence: 62 new pure tests (pure tier 618, only the 2 known errors). On
`visa-tracker-test.localhost` (rolled back, `publish_realtime` captured):
ensure job → `extraction_queued` (orange); extraction Needs Review →
`needs_review` (orange); verify → `application_created` (green); recompute →
`status_changed` (green) to both the Process File and the Application rooms;
every event `after_commit=True`; no passport values in any payload. Migrate
OK; full on-site suite 719 OK.

Deviations: the form listener is registered in `refresh` and removed in
`on_hide` (Frappe v15 forms have no unload event); A4/A6 are sent from
`handle_verified_extraction` with a notify flag.

## What remains

Browser check of the toasts and automatic reload (owner, on `visaguy`), push and deploy.
