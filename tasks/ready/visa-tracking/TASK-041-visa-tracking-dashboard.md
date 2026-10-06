---
id: TASK-041
feature: FEAT-001
title: Visa Tracking workspace dashboard — reports, number cards and charts
status: ready
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-032
  - TASK-035
created: 2026-10-06
updated: 2026-10-06
---

# TASK-041: Visa Tracking workspace dashboard — reports, number cards and charts

## Objective

Owner request (2026-10-06): in the existing "Visa Tracking" workspace
(`the_visaguy` fixture), add reports and charts for:

1. passports extracted today;
2. tracking applications created;
3. failed extractions and their reasons;
4. how many applications were newly created from leads versus created for
   existing files.

Permissions stay as they are: no DocType permission changes.

## Definitions

- **Extracted today**: Passport Extractions whose `processing_completed_on`
  is today (any outcome); split by status.
- **Failed**: status `Failed`; reason = `error_code` (blank → "Unknown").
  `error_message` is permlevel 1 and must not appear in any report or chart.
- **Origin of an application** (owner-approved definition, 2026-10-06):
  - **New from Lead**: no Process File, or the application's `creation` is
    on or before its Process File's `creation`;
  - **Existing file**: its Process File was created before the application
    (the ADR-016 path: save trigger or Generate Visa Tracking).

## Required behaviour

### Script Reports (module The Visa Guy, is_standard Yes)

1. **Passport Extraction Daily Summary** (ref Passport Extraction). Filters:
   from date, to date (default last 30 days). One row per day: total,
   Extracted, Verified, Needs Review, Failed, Queued/Processing. Chart: stacked
   bar per day by status. Report summary: today's totals.
2. **Failed Passport Extractions** (ref Passport Extraction). Filters: from /
   to date, error code. Columns: extraction (link), requested on, completed on,
   error code, source document (link), Process File(s) using that collection
   (link, first one), retried (yes if a newer extraction exists for the same
   source row). No passport values, no `error_message`. Chart: bar by error
   code. Summary: total failed, per top reasons.
3. **Visa Tracking Applications Created** (ref Visa Tracking Application).
   Filters: from / to date, origin, destination. Columns: application (link),
   created on, applicant display name, destination, origin, Process File
   (link), current status. Chart: stacked bar per day, New from Lead vs
   Existing file. Summary: total, new from lead, existing file. No passport
   number or DOB.

Set each report's roles to exactly the roles that can read its ref DocType
today (read the current DocPerm / Custom DocPerm rows; do not add or remove
DocType permissions).

### Number Cards (fixtures, by name)

- "Extracted Today" — Passport Extraction, `processing_completed_on` = today
  (dynamic filter), status in Extracted / Verified / Needs Review.
- "Needs Review" — Passport Extraction, status = Needs Review (open).
- "Failed Today" — Passport Extraction, status = Failed, completed today.
- "Applications Created Today" — Visa Tracking Application, creation today.
- "Applications Linked to Process Files" — Visa Tracking Application with a
  Process File (total).

Use `dynamic_filters_json` for "today".

### Dashboard Charts (fixtures, by name)

- "Passport Extractions (Daily)" — Report chart from report 1.
- "Failed Extractions by Reason" — Group By `error_code`, filter status
  Failed, last 30 days, bar.
- "Applications Created: New vs Existing" — Report chart from report 3.
- "Applications by Current Status" — Group By `current_status`, donut.

### Workspace layout ("Visa Tracking")

Keep the existing header and shortcuts. Layout, top to bottom:

1. Header "Today" → the five number cards in one row.
2. Header "Passport extraction" → "Passport Extractions (Daily)" (full width),
   then "Failed Extractions by Reason" (half) next to a card of links to
   reports 1 and 2.
3. Header "Tracking applications" → "Applications Created: New vs Existing"
   (half) and "Applications by Current Status" (half), then a links card
   with report 3 and the coverage report.
4. Existing shortcuts row stays at the top under the title.

Add the Number Card and Dashboard Chart records to `hooks.py` fixtures by
name filter (never a bare-string fixture entry; risk 25), and the reports as
standard report folders.

## Constraints

- No change to any DocType permission, Custom DocPerm or role.
- No passport number, DOB, MRZ, `error_message` or file name in any column,
  card or chart.
- Reports use set-based queries (no document load per row).

## Validation

- Pure tests for the origin classification, report columns (no forbidden
  fields), filters and summaries.
- Test site: migrate; the workspace renders the records (Number Card and
  Dashboard Chart docs exist and are linked in `content`); each report runs
  with seeded rolled-back data and gives correct counts per day, per reason
  and per origin; the chart data matches the report rows.
