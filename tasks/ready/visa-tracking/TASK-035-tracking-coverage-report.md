---
id: TASK-035
feature: FEAT-001
title: Tracking coverage report for the soft launch
status: ready
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-016
  - TASK-031
  - TASK-036
expected_files:
  - the_visaguy/the_visa_guy/report/visa_tracking_coverage/
created: 2026-09-28
updated: 2026-09-28
---

# TASK-035: Tracking coverage report for the soft launch

## Objective

Show, per open Process File, whether the client can track it and, if not,
why. Operations use it to fix files. The owner uses it to decide on the
marketing launch.

## Required behaviour

A Script Report **Visa Tracking Coverage**, with filters: workflow state,
department, modified from, modified to, "only without tracking".

One row per Process File:

- Process File, applicant name, workflow state, destination, primary or
  dependant, modified.
- Tracking application (link) and current status.
- **Reason**, the same outcome codes that TASK-031's `ensure_tracking`
  returns: `already_linked`, `no_passport_row`, `passport_not_completed`,
  `passport_no_file`, `extraction_pending`, `needs_review`,
  `extraction_failed`, `applicant_row_unresolved`, `no_destination`,
  `not_saved_since_launch`.

The report computes the reason read-only. It never enqueues or writes.

A summary row at the top: open files, tracked, and a count per reason.

## Constraints

- Read-only. No passport number, DOB or MRZ in any column.
- Find passport rows by `field_id` in `passport_field_ids` only
  (TASK-036). Reuse TASK-031's outcome codes.
- It must run in under 30 seconds for 15,000 open files. Use set-based
  queries, not a document load per file.

## Validation

- On `visa-tracker-test.localhost`, one fixture file per reason shows that
  reason.
- On `visaguy`, the totals match the 2026-09-25 counts in ADR-016 before
  any tracking exists.

## Definition of done

Validation passes, and the report is on the "Visa Tracking" workspace
(TASK-032).
