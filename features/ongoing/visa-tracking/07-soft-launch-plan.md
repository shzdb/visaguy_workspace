# Visa tracking: soft launch plan

Status: draft, 2026-09-28. D1–D4 decided 2026-09-28; D5–D10 open.

## Goal

Run visa tracking in production for one to two weeks without marketing.
During that time, tracking is created for Process Files that staff work on
(ADR-016). At the end, decide whether to market the tracker to clients.

## Where things are (2026-09-28)

From the task records and a read-only check of the bench:

| Area | State |
|---|---|
| Extraction, tracking, public API, SPA (TASK-001 to TASK-009) | Built. |
| Derived client status (TASK-016), public title in the SPA (TASK-017) | In progress. Not deployed. |
| Process File linking (TASK-022), dependant rows (TASK-023) | Pushed. Not deployed. |
| Several applications per passport, case list, manual status (TASK-024 to TASK-027) | Pushed 2026-09-14. Not deployed. |
| Rate-limit hardening (TASK-012, risk 18) | In progress. The deployed limiter does not stop enumeration. |
| Auto-verification tests (TASK-011) | In progress. |
| `passport_extractor` on `visaguy` | Not installed. The owner will install it. |
| `passport_field_ids` on `visaguy` | Empty. |
| Legacy passport rows with a `field_id` | None. |
| Operations users with permission on tracking records | None (risk 45). |
| Desk path to verify an extraction | None (risk 46). |
| Tracker link sent to clients (WhatsApp, email, website) | None. |

## Owner decisions needed

| # | Decision | Recommendation | Blocks |
|---|---|---|---|
| D1 | Which Process File workflow states create tracking on save. | **Decided 2026-09-28:** every state except Rejected. Completed and Documents Delivered files are tracked. | – |
| D2 | Manual or automatic passport verification (`require_manual_verification`). | **Decided 2026-09-28:** always automatic; the setting is off. The Completed row is the human check. ADR-007 amendment. | – |
| D3 | Who can read tracking records. | **Decided 2026-09-28:** every role that can read `PF Process File` or `Lead` gets read on Application, Status and Status Log. Permissions live in `the_visaguy`. | – |
| D4 | Who can create tracking (**Generate Visa Tracking**, **Retry passport extraction**). | **Decided 2026-09-28:** `Operations Associate` and `Operations Team Lead` (and `System Manager`). | – |
| D5 | What the client sees for a Rejected (refused) file. ADR-010 leaves it unhandled. | Exclude Rejected files from tracking for the soft launch (D1). Decide the wording before marketing. | Marketing |
| D6 | Public titles and messages of the six statuses, and the ON_HOLD wording. | Business review of the `Visa Tracking Status` records before the pilot. | Pilot |
| D7 | During the soft launch, is the tracker link sent to any clients? | Yes, by hand, to 10–20 clients chosen by operations, so real client use is tested. | Phase 4 |
| D8 | Security gate before marketing. | TASK-012 deployed (risk 18). Required before the link is public. | Marketing |
| D9 | For legacy files, apply `process_file_created_status` when linking? | Configuration, not code: set `enable_process_file_created_transition` at deploy. Recommendation: off, so the timeline starts with the recomputed status. | Phase 2 |
| D10 | What happens to open files nobody saves during the soft launch. | Look at the coverage report on the last day. Run `ensure_tracking` once over them if coverage is too low (ADR-016 "Revisit when"). | Marketing |

## Gaps

### Must have before the soft launch

| Gap | Why | Task |
|---|---|---|
| Tracking is created on Process File save, for the primary and dependants | ADR-016. Without it, no legacy file is ever tracked. | TASK-031 |
| Manual **Generate Visa Tracking** and **Retry passport extraction** actions | Recovery when a job fails, without a developer. | TASK-031 |
| Legacy passport rows found by file name | No legacy row has a `field_id`. | TASK-031 |
| Operations can open the tracking link and use the status picker | Today every operations user gets a permission error. | TASK-034 |
| A labelled **Visa Tracking** section on the Process File, with the name shown in the link | Today the link sits in an unlabelled section among reference fields, and shows an ID. | TASK-032 |
| Application form ordered for reading: applicant, status, timeline, then references | Today the references come first and the timeline is not shown. | TASK-032 |
| Stale Lead / CRM Lead / Customer tracking fields hidden | ADR-015 stopped writing them; they can point at the wrong case. | TASK-032 |
| Retry, list filters and search on Passport Extraction | A failed extraction needs a retry without a developer, and support needs to find a record. | TASK-033 |
| Auto-verification tests | D2: verification is always automatic, and the ADR-007 code has no tests. | TASK-011 |
| Coverage report | The only way to measure the soft launch and find stuck files. | TASK-035 |
| One Error Log entry per file and reason | Otherwise every save of an unresolved file writes a new entry. | TASK-031 |

### Before marketing

| Gap | Why | Task |
|---|---|---|
| Rate-limit hardening | Risk 18: the deployed limiter does not stop enumeration of passport + DOB pairs. | TASK-012 |
| The tracker link in client messages | Clients can only find the tracker if someone tells them. Add it to the WhatsApp templates for "Process File created" and for status changes, and on the website. | New task after D7 |
| Rejected file wording | D5. | New task after D5 |
| Staff guide | One page for operations: the Process File section, what each reason in the coverage report means, and when to use each button. | Workspace doc |
| Support lookup | Support staff find a record from the passport number or name the client gives. | TASK-033 (search fields), TASK-032 |

### Later

- Show each dependant's tracking status in the Process File's
  "Dependent Details" table.
- Passport renewal during a case: a new passport creates a new application
  and flags "applicant passport changed". Decide whether the old one is
  closed.
- Close applications (`application_closed`) automatically after Documents
  Delivered plus N days, and a retention period for closed ones.
- Delete the hidden Lead-level fields with an explicit patch (risk 39).
- `field_id` on legacy templates, so the file-name match can be removed.

## Phases

### Phase 0: decisions (owner)

D1–D4 recorded 2026-09-28; TASK-031 and TASK-034 are `ready`. D5–D10
and the `Needs Review` question (risk 46) remain.

### Phase 1: build

Order: TASK-031 → TASK-034 → TASK-011 → TASK-033 → TASK-032 → TASK-035. Test each on
`visa-tracker-test.localhost`. Close TASK-016, TASK-017 and TASK-022 to
TASK-027 together, because they deploy together.

### Phase 2: deploy and configure (owner)

1. Back up the production site.
2. Check that the three FEAT-001 Custom Fields exist before migrate (risk 25).
3. Install `passport_extractor`. Confirm PaddleOCR models are on the worker
   host, and at least one `long` queue worker is running.
4. Deploy `fileflo`, `visaguy_crm`, `passport_extractor`, `the_visaguy`, then
   `visa_tracker`. Backend before frontend (TASK-017, TASK-025).
5. Read the printed counts of the ADR-015 link patch (risk 41).
6. Migrate syncs the role permissions (TASK-034). No role assignment is
   needed for operations; assign `Visa Tracker Manager` to the people who
   change settings.
7. **Visa Tracker Settings**:
   - `enabled`, `enable_passport_extraction`,
     `auto_create_tracking_application`, `auto_link_verified_passport`: on.
   - `passport_field_ids`: the `field_id` values used on new templates.
   - `require_manual_verification`: **off** (D2).
   - `extraction_queue`: `long`. `inspection_queue`: `short`.
   - `default_lead_status`, `process_file_created_status`,
     `enable_process_file_created_transition` (D9).
   - `enable_public_tracking`: on. `frontend_base_url`: the tracker's
     HTTPS origin. `support_link`, `generic_failure_message`.
   - Session, lockout and history values as on the test site.
8. Site config: `allow_cors` includes the tracker origin (risk 20).
9. Status records: public titles and messages per D6.
10. Scheduler: the hourly reconciliation sweep is registered.

### Phase 3: internal pilot (2–3 days)

- Operations save 20 real open files: primaries with dependants, a file
  with a PDF passport, one with front and back images, one with a passport
  not yet Completed.
- For each: the coverage report reason is correct; after the extraction,
  the link appears; the status matches the workflow state.
- Staff open the public tracker with the client's passport and DOB for
  five files, on a phone and on a desktop. Check the name, status and
  timeline, and a case list for a client with two cases.
- Try a wrong DOB five times; confirm the lockout message is generic.
- Exit: no wrong-person data, no permission errors, every stuck file has a
  reason an operations user can act on.

### Phase 4: soft launch (1–2 weeks)

Daily, from the coverage report and the Visa Tracker Audit Log:

- open files saved since launch, and how many are tracked;
- counts per reason; extractions in `Needs Review` (no tracking is created for them);
- extractions `Failed` and the error codes;
- Error Log entries for visa tracking;
- public lookups per day: successful and failed;
- long-queue backlog and worker memory.

Send the link by hand to the clients chosen in D7. Ask them one question:
"Was the status right and clear?"

### Phase 5: marketing gate

Market the tracker only when all of these are true:

- No case showed another person's data.
- At least 90% of open files saved since launch are tracked, or each
  untracked one has a reason operations accept.
- The number of `Needs Review` and `Failed` extractions is known, and
  each has an owner (risk 46).
- TASK-012 is deployed (D8), and D5 and D10 are decided.
- The link is in client messages (D7 follow-up).

### Rollback

- Turn off `enable_public_tracking`: the public API returns the generic
  failure; nothing else changes.
- Turn off `enabled`: no new extraction or application is created. Process
  File saves are not affected; TASK-031's hook returns at once.
- Data created during the soft launch stays. It is not client-visible
  while public tracking is off.
