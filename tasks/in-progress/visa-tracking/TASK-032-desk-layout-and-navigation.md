---
id: TASK-032
feature: FEAT-001
title: Desk layout and navigation for visa tracking
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-015
  - ADR-016
expected_files:
  - the_visaguy/fixtures/custom_fields.json
  - the_visaguy/fixtures/property_setters.json
  - the_visaguy/the_visa_guy/doctype/visa_tracking_application/visa_tracking_application.json
  - the_visaguy/the_visa_guy/doctype/visa_tracking_application/visa_tracking_application.js
  - the_visaguy/the_visa_guy/doctype/visa_tracking_application/visa_tracking_application_list.js
  - the_visaguy/fixtures/workspace.json
created: 2026-09-28
updated: 2026-09-28
---

# TASK-032: Desk layout and navigation for visa tracking

## Objective

Make tracking easy to find and read for operations and support staff. No
behaviour change.

## Context (site `visaguy`, 2026-09-28)

- `PF Process File.custom_visa_tracking_application` (read-only) and
  `custom_client_status` exist. They sit at positions 21–22 in an unlabelled
  section (`custom_section_break_xzg1p`) between `file_collection` and
  `custom_lead_file_collection`, mixed with reference and date fields.
- `Visa Tracking Application` shows the "References" section first, then
  "Public State", then "Secure Lookup". It has no title field, no list-view
  columns, no standard filters, no search fields and no form script. The
  list shows only `VTA-YYYY-#####`. The status timeline (`Visa Tracking
  Status Log`) is not visible from the form.
- `Lead`, `CRM Lead` and `Customer` still show
  `custom_visa_tracking_application`, which ADR-015 no longer writes
  (risk 39). The value there can be stale.
- `Applicant Information.visa_tracking_application` is not in the grid
  view.
- There is no workspace for visa tracking.

## Required behaviour

### 1. Process File

- A new labelled, collapsible section **Visa Tracking**, placed after the
  section that holds `file_collection`. Move into it:
  `custom_visa_tracking_application`, `custom_client_status`, and two new
  read-only fetched fields: `custom_tracking_updated_on` (from
  `status_updated_on`) and `custom_tracking_enabled` (from
  `tracking_enabled`).
- When the link is empty, show a short grey note in the section: "No
  tracking yet. It is created after the passport is marked Completed and
  verified." TASK-031 adds the button.

### 2. Visa Tracking Application form

Section order:

1. **Applicant**: `applicant_display_name` (title field), `destination`,
   `tracking_enabled`, `application_closed`.
2. **Current status**: `current_status`, `current_public_message`,
   `status_updated_on`.
3. **Timeline**: an HTML field that the form script fills with the status
   log. Show the date, the status, whether the client sees it, and who
   changed it.
4. **References** (collapsed): the existing reference links.
5. **Secure lookup** (collapsed): the two hash fields.

Also:

- `title_field = applicant_display_name`, `show_title_field_in_link = 1`,
  so the Process File link shows the name, not the ID.
- List view: applicant, destination, current status, tracking enabled,
  status updated on. Standard filters: current status, destination,
  tracking enabled, application closed. Search fields:
  `applicant_display_name`, `process_file`, `lead`.
- A **Connections** entry for `Visa Tracking Status Log`.
- A form button **Open Process File** when `process_file` is set.

### 3. Lead, CRM Lead, Customer

Hide the Lead-, CRM Lead- and Customer-level
`custom_visa_tracking_application` with a Property Setter (`hidden = 1`).
Do not delete the fields. Deletion is a separate patch (risk 39, risk 25).

### 4. Applicant Information

Set `in_list_view = 1` on `visa_tracking_application`, so each applicant's
link shows in the Lead grid.

### 5. Workspace "Visa Tracking"

Shortcuts, with counts where Frappe supports them:

- Passport Extractions in `Needs Review`.
- Passport Extractions in `Failed`.
- Visa Tracking Applications.
- The coverage report (TASK-035).
- Visa Tracker Settings.

## Constraints

- Custom Fields only through `fixtures/custom_fields.json`, by name. No
  bare-string fixture entry (risk 25).
- No change to field names that the API or the SPA reads.
- `processflo` is not changed. Everything is a Custom Field or a Property
  Setter from `the_visaguy`.

## Validation

- `bench migrate` on `visa-tracker-test.localhost`. Check the field order
  with `frappe.get_meta`.
- Desk check as an Operations Associate on a linked and on an unlinked
  Process File. This needs TASK-034 for the link to open.
- The Application list shows names and filters work.

## Definition of done

Validation passes, and screenshots of the Process File section and the
Application form are attached to the completion note.

## Implementation (2026-09-28)

Branch `feat/visa-tracker` in `the_visaguy` on the bench (installed checkout), commits `07e7c73`, `d46364c`, merged `7c737b1`. Not pushed, not deployed.
Built by Cursor executors, reviewed and merged by the orchestrator; records in
`ongoing/visa-tracking-soft-launch/`.

Evidence: Static fixture tests; on the test site the PF field order is custom_form_submitted → Visa Tracking section (link, Client Status, note, column, updated on, enabled) → Application Form; Application title/sections/list/filters/links, workspace, hidden Lead-level fields and applicant grid column verified with frappe.get_meta. The PF `field_order` Property Setter (from visaguy_crm) does not list the tracking fields; an idempotent after_migrate hook guards the order. Full suites on `visa-tracker-test.localhost` after all merges: `the_visaguy` 638 OK, `passport_extractor` 98 OK (`--skip-test-records`).

## What remains

1. Owner migrates and tests `visaguy` (never run by Claude; see memory rule).
2. Browser check of the desk UI.
3. Push and deploy (owner).
