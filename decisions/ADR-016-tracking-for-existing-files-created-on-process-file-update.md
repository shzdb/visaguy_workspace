# ADR-016: Tracking for Existing Files Is Created on Process File Update, Not by Backfill

## Status

Accepted (2026-09-28). Not implemented. Implementation: TASK-031.

Amends the FEAT-001 go-live approach. ADR-012 (extraction starts on a
Completed passport row), ADR-014 (Process File ownership by file collection)
and ADR-015 (one application per Lead applicant row) are unchanged.

## Context

When the feature goes live, no Process File created before it has a
`Visa Tracking Application`. A bulk backfill was considered: a `bench
execute` command that processes every file from an appointment date onward.

Read-only counts on site `visaguy` (2026-09-25):

- 14,036 open Process Files (Unassigned, Assigned, Inprogress, Hold). None
  has a tracking application.
- 45% of open files have no appointment date. A date cutoff would miss them.
- Open files saved in the last 180 days: 7,558. Of these, 6,083 have a
  Completed passport row with a file.
- No legacy primary passport row has a `field_id`. The rows are identified
  only by file name (`Passport`, `Passport Copy`, `Passport - N`, …).
- Every such passport row is in the Lead-stage collection
  (`custom_lead_file_collection`), not in the Process File's `file_collection`.

Legacy passport rows are already `Completed`, so the ADR-012 trigger never
fires for them again.

Owner facts (2026-09-28):

- A file collection belongs to one person. Several passport rows in one
  collection are pages of the same passport (for example front and back),
  never two people.
- Staff mark a passport row `Completed` only after they check that the
  upload is a valid passport.

## Decision

Owner decision of 2026-09-28:

1. **No bulk backfill.** No application data is created in advance.
2. **Create on Process File update.** When a `PF Process File` is saved and
   it has no tracking application, the system makes sure one exists, for the
   primary file and for each linked dependant file.
3. **Manual action.** The same logic is available as an action on the
   Process File form, for when the job fails or a person needs to retry.
4. **Legacy passport rows are found by file name** when they have no
   `field_id`. New files use `field_id` as now.
5. **Soft launch.** Run in production for one to two weeks without
   marketing. Then decide on the marketing launch
   (`features/ongoing/visa-tracking/07-soft-launch-plan.md`).

## Consequences

### Positive

- OCR load is spread across normal work. There is no single run of about
  6,000 extractions.
- Only files that staff are working on get tracking. Inactive files are
  not processed.
- One code path serves the save trigger, the manual action and any later
  one-time sweep.

### Negative

- A file nobody saves has no tracking. A client with such a file gets the
  generic "not found" response.
- Coverage depends on operations activity. It must be measured during the
  soft launch.
- The file-name match is a heuristic. A passport uploaded under another
  name is not found.
- The save hook runs on every Process File save. It must return at once
  when a link exists, and it must not write repeated Error Log entries for
  files that cannot resolve.

## Alternatives considered

- **Backfill from an appointment date onward.** Rejected: 45% of open files
  have no appointment date, and a date cutoff also leaves out open files
  with an old date.
- **Backfill all open files saved in the last 180 days.** Not chosen: about
  6,000 OCR jobs in one run, and the review queue fills before the feature
  is proven.
- **Wait for `field_id` on legacy rows.** Rejected: no legacy row has one,
  and adding them to old collections is a separate data change.

## Amendment (2026-09-28): field ID patch instead of file-name matching

Owner decision, later the same day. Decision 4 ("legacy passport rows are
found by file name") is replaced:

- A one-time patch (TASK-036) sets `field_id` and `field_id_link` to the
  existing `FF Field ID` `passport` on every primary passport row: 223
  template rows and 37,490 rows in 29,176 existing collections on
  `visaguy`.
- The name rule is used once, in the patch, and its counts are reviewed in
  a dry run. Live code (TASK-031, TASK-035, the ADR-012 trigger) uses only
  `field_id`.
- The patch writes without document saves, so it queues no OCR. Decision 1
  (no bulk backfill) still holds.
- `passport_field_ids` is set to `passport`.

This also removes the "file-name match is a heuristic" consequence above
from the running system. A passport under an unmatched name is found by
the patch's dry-run counts, not later by the coverage report.

## Revisit when

Coverage after the soft launch is too low for marketing, or untouched open
files must be tracked. Then run the same function once over the remaining
open files.
