# ADR-014: A Process File Belongs to the Tracking Application That Shares Its File Collection

## Status

Accepted (2026-09-03, recorded 2026-09-13)

The owner approved the rule on 2026-09-03 and implemented it directly on the
bench (`the_visaguy` `b99dea7`, hardened by `d59614f`). The approval is
recorded in the source itself, in the docstring of
`lifecycle_service._file_collection_candidates_for_process_file`. This ADR
records that decision after the fact.

Replaces the resolution order in TASK-006's
`_resolve_tracking_application_for_process_file`, which tried the Lead's
`custom_visa_tracking_application` Link first.

## Context

The public status endpoint (`api/status.py`) builds the `dependants` array
only when `Visa Tracking Application.process_file` is set. On 2026-09-03 no
application had that field set, and no `PF Process File` had
`custom_visa_tracking_application` set, so every primary showed an empty
`dependants` list.

The cause: `lifecycle_service.link_process_file_to_tracking()` existed but
nothing called it. It was implemented in TASK-006 and never wired to a hook,
job, or API. The investigation brief is
`ongoing/process-file-tracking-link/PROMPT.md`.

Wiring it was not enough, because the existing resolver could pick the
wrong application:

1. **The Lead route is wrong for multi-applicant leads.** A Lead has one
   `custom_visa_tracking_application` Link, but one Lead can have several
   applicants, and each verified passport creates its own application. The
   dev-site lead in the brief had two applications and its Link named the
   one the client did not verify into.
2. **The process-stage file collection alone does not match.** A tracking
   application is created while the case is still a Lead, so it carries the
   **lead-stage** file collection. `visaguy_crm` gives the Process File a new
   **process-stage** collection in `file_collection` and keeps the lead-stage
   one in `custom_lead_file_collection`. Matching on `file_collection` only
   misses the application.

Linking a Process File to the wrong application shows one client another
client's dependants — the same class of defect as risk 28.

## Decision

**A `PF Process File` belongs to the unique active `Visa Tracking
Application` whose `file_collection` equals the Process File's
`custom_lead_file_collection` or its `file_collection`.**

- Active means `application_closed = 0`.
- **Zero matches:** do not link.
- **One match:** link both directions — `PF Process File.custom_visa_tracking_application`
  and `Visa Tracking Application.process_file`.
- **More than one match:** do not link, and call `_flag_review` so a person
  decides. Never guess.
- **The Lead's `custom_visa_tracking_application` is never used** for this
  decision.
- An existing `custom_visa_tracking_application` value on the Process File
  wins and is not re-resolved.

The link is attempted from both sides, so the order of creation does not
matter:

| Trigger | Where |
|---|---|
| Process File created | `PF Process File` `after_insert` → `process_file_handlers.after_insert` |
| A file-collection field changes on an unlinked Process File | `PF Process File` `on_update` → `_maybe_link_on_fc_change` (watches `file_collection`, `custom_lead_file_collection`) |
| Tracking application created or reused | `lifecycle_service.create_tracking_application` → `_maybe_link_process_file_for_application`, which looks up Process Files on either collection field and flags more than one |

The Process File side is written with
`frappe.db.set_value(..., update_modified=False)` and mirrored onto the
caller's in-memory document (`d59614f`). A document save here moved
`modified` forward while `visaguy_crm.create_pf_process_file` still held the
old object, and its second save failed with `TimestampMismatchError`. That
broke Lead-to-Process-File conversion.

All handler paths catch exceptions into `frappe.log_error`, so a linking
fault cannot fail a staff save.

## Consequences

### Positive

- One Lead with several applicants links each Process File to the right
  applicant's application.
- A primary's status response now carries its dependants.
- Ambiguity is reported for review instead of producing a wrong link.
- The ADR-010 derived-status path (`custom_visa_tracking_application`
  guards) can now act on real rows.

### Negative

- **Existing rows are not linked.** The triggers fire only on new events.
  On 2026-09-13, 4 of 3,875 Process Files on `visaguy` were linked. No
  backfill exists (risk 37).
- **A wrong link is permanent.** Once `custom_visa_tracking_application` is
  set it short-circuits the resolver. Correction is manual.
- **A collection mismatch fails silently.** If neither collection field on
  the Process File equals the application's collection, the case stays
  unlinked and the tracker shows no dependants, with no log entry.
- The flag-for-review path writes an Error Log entry; nobody is notified.

## Alternatives considered

- **Keep the Lead Link as the first route.** Rejected: one Link cannot
  express one Lead with many applicants, and it was already wrong on real
  data.
- **Match on the process-stage `file_collection` only.** Rejected: the
  application carries the lead-stage collection, so this misses the normal
  case.
- **Match on applicant name.** Rejected: names are not unique and are
  written differently across records.
- **Pick the oldest match when several applications match.** Rejected:
  a guess that shows another person's data when wrong.

## Revisit when

`visaguy_crm` stops copying the lead-stage collection into
`custom_lead_file_collection`, a Process File can serve more than one
applicant, a backfill of existing rows is planned, or the review flag fires
often enough to need a real queue.
