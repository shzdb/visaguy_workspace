---
id: TASK-038
feature: FEAT-001
title: Realtime alerts for visa tracking in the desk
status: blocked
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

## Blocked on

Owner decisions Q1–Q3 below.

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
and, where decided in Q1, writes a Notification Log.

| # | When | Who sees it | What |
|---|---|---|---|
| A1 | A save enqueues tracking | The user who saved (toast after the save response, `msgprint(alert=True)`) | "Visa tracking: checking the passport for this file." Only when the job is newly enqueued; roles per Q2. |
| A2 | The ensure job ends | Everyone with the file open (realtime) | Toast with the outcome message (the TASK-031 messages), coloured green / orange / red. |
| A3 | Extraction ends `Needs Review` / `Failed` / `Verified` | Everyone with the file open; Notification Log per Q1 | "Passport needs review", "Passport extraction failed: <reason>", "Passport verified". |
| A4 | Application created and linked | Everyone with the file open | Toast "Visa Tracking Application created" and the form reloads if it has no unsaved changes, so the link, section and buttons update. |
| A5 | Client status recomputed | Everyone with the Process File or the Application open | Toast "Client status is now <public title>" and reload if not dirty. |
| A6 | Review flag (duplicate identity, applicant row, destination) | Everyone with the file open; Notification Log per Q1 | Toast in red with the TASK-031 message. |
| A7 | Opening an unlinked Process File | The viewer | Per Q3: a headline in the Visa Tracking section with the current reason (diagnose mode, read-only). |

Client side: one listener in the TASK-031 client script
(`frappe.realtime.on("visa_tracking_update", ...)`), registered once per
form (remove it on unload), that checks `docname`, calls
`frappe.show_alert`, and `frm.reload_doc()` when `!frm.is_dirty()`.

## Owner decisions needed

- **Q1 — bell notifications (Notification Log).** Realtime toasts reach
  only people who have the form open. For events that need action (A3
  Needs Review / Failed, A6), who gets a bell notification?
  Options: the Process File's `custom_designated_to` user; all Operations
  Team Leads; nobody (toasts and the coverage report only).
  Recommendation: `custom_designated_to`, falling back to nobody.
- **Q2 — A1 save toast.** Show it to every user who saves, or only to the
  three tracking roles? Recommendation: tracking roles only.
- **Q3 — A7 headline.** Show the reason when an unlinked Process File is
  opened? It costs one read-only server call per form load of an unlinked
  file. Recommendation: yes.

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
  values in payloads; Notification Log recipients per Q1.
- Test site: with a Process File form open in a browser, save → A1 toast;
  run the jobs → A2/A4 toasts and automatic reload; change workflow →
  A5 toast; review flag → A6.

## Definition of done

Validation passes and the commit SHA is recorded here.
