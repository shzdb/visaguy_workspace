---
id: TASK-039
feature: FEAT-001
title: Drop the Lead passport link, show passport number and DOB on the application, open the status log from the timeline
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-032
  - TASK-034
created: 2026-10-05
updated: 2026-10-05
---

# TASK-039: Drop the Lead passport link, show passport number and DOB on the application, open the status log from the timeline

Owner requests of 2026-10-05. Three independent parts.

## Part A — remove the passport extraction link from Lead

Owner: "remove passport extraction from the lead, we would not need that".

Today (`the_visaguy` `b372f73`):

- Custom Fields `Lead-custom_passport_extraction` and
  `CRM Lead-custom_passport_extraction` (fixtures/custom_fields.json); the
  Lead and CRM Lead `custom_visa_tracking_application` fields use
  `insert_after: custom_passport_extraction`.
- Written by `lifecycle_service.link_verified_extraction_to_lead` and
  `_link_lead_extraction` (gated by `Visa Tracker Settings.auto_link_verified_passport`).
- Read by `lead_handlers.on_customer_save`, which copies it to
  `Customer.custom_passport_extraction` (kept for future FileFlo autofill).

Required:

1. Stop writing and reading the Lead / CRM Lead field. Remove
   `link_verified_extraction_to_lead` and `_link_lead_extraction` and their
   callers.
2. Keep `Customer.custom_passport_extraction`: set it directly from the
   verified extraction when the tracking application is created or reused,
   using the Lead's customer (existing `link_verified_extraction_to_customer`).
   `lead_handlers.on_customer_save` no longer reads the Lead field.
3. Re-anchor the Lead / CRM Lead `custom_visa_tracking_application`
   Custom Fields (`insert_after: status`, the old anchor of the removed field).
4. Delete the two Custom Fields with an explicit patch
   (`frappe.delete_doc("Custom Field", name, ignore_missing=True)`), and
   remove them from fixtures/custom_fields.json in the same commit. Never a
   fixture sweep (risk 25). The DB column is dropped by Frappe with the
   field; that loses only a redundant link (the extraction keeps its source).
5. `auto_link_verified_passport` keeps gating the Customer link only; update
   its description.

## Part B — passport number and DOB on Visa Tracking Application

Owner: staff should see them on the application without opening Passport
Extraction.

Security note: passport number + DOB are the public tracker credentials
(ADR-005). Every desk role can read the application (TASK-034, D3). So the
two fields are **permlevel 1**, readable only by roles that can already read
Passport Extraction: Operations Associate, Operations Team Lead, Visa Tracker
Manager, System Manager. No new exposure.

Required:

1. Fields in the Applicant section: `passport_number` (Data) and
   `date_of_birth` (Date), both `read_only`, `permlevel 1`,
   `fetch_from` `passport_extraction.passport_number_normalized` and
   `passport_extraction.date_of_birth`. Not in list view, filters or search.
2. `create_tracking_application` sets them explicitly on insert and on reuse
   when `passport_extraction` changes.
3. Custom DocPerm rows (fixtures/custom_docperm.json) for Visa Tracking
   Application at permlevel 1: read for the four roles above (keep the union
   rule from TASK-034).
4. Patch: backfill both fields for existing applications from their linked
   extraction (db update, no save).
5. Public API and SPA unchanged; no new key in any response.

## Part C — open the status log from each timeline row

Owner (2026-10-05, replacing the earlier child-table request): keep the
existing HTML timeline on Visa Tracking Application and add, on each row, a
link that opens that row's `Visa Tracking Status Log` record.

1. The form script already loads the logs with `frappe.db.get_list`; also
   fetch `name` and render an "Open" link per row to
   `/app/visa-tracking-status-log/<name>` (use `frappe.utils.get_form_link`
   or the route helper; escape every value).
2. No new DocType, no new field, no change to `status_service`.

## Validation

- Pure tests for each part.
- Test site: migrate; the two Lead fields are gone and the Lead form still
  renders the tracking link in place; creating an application through the
  smoke chain sets the Customer link, the passport number and DOB; each
  timeline row links to its Status Log; an Operations Associate can read the two fields, a
  `Lead Role` user cannot see them; the backfill patch fills existing
  applications; on-site suite passes.

## Definition of done

Validation passes and the commit SHA is recorded here.

## Implementation (2026-10-05)

Built by two Sonnet sub-agents (Parts A + B server; Part B fields + C), reviewed
and merged by the orchestrator into `feat/visa-tracker` on the bench:
`the_visaguy` `e6632e6` + orchestrator fix `458f551`, `6718c89`; merges `5381de1`,
`a9a74a1` (HEAD). Pushed 2026-10-05 (`the_visaguy` `feat/visa-tracker` `80a5c3a`, `passport_extractor` `316154e`); not deployed.

Orchestrator fix `458f551`: the Customer was found through `Customer.lead_name`,
which ERPNext sets only for Leads, so CRM Leads never got the Customer passport
link. It now reads `custom_customer_id` (Lead and CRM Lead), then `customer`,
then `Customer.lead_name`.

Evidence on `visa-tracker-test.localhost`:
- Migrate ran both patches. The two Custom Fields are gone. The Lead DB column
  remains (Frappe does not drop a column when a Custom Field is deleted).
- Pure tier 630 (2 known errors); on-site suite 731 OK.
- CRM Lead end to end with a real passport (rolled back): CRM Lead with a Primary
  applicant row and Customer; `extraction_queued` → OCR Extracted 99.3% in 60 s →
  auto-verified → application with `crm_lead` set, linked to the Process File and
  the applicant row, `IN_PROGRESS`, passport number and DOB set, Customer passport
  link set, 2 status logs, `already_linked` afterwards.
- Field permissions with single-role users: Lead Role and Consultant Role read the
  application but not permlevel 1; Operations Associate and Team Lead read both.

Test-site setup for the CRM Lead run: installed `frappe_conversions_api` (it
provides `Lead External IDs`; no provider, account or event records exist, so
nothing is sent) and `visaguy_frappe_crm` (its bench checkout has an uncommitted
`fixtures/property_setter.json` change, left untouched), then migrated.

## What remains

Owner test on `visaguy`, browser check of the Open links, deploy (pushed 2026-10-05).
