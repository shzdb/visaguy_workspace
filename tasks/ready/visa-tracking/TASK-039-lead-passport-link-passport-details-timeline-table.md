---
id: TASK-039
feature: FEAT-001
title: Drop the Lead passport link, show passport number and DOB on the application, timeline as a child table
status: ready
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-032
  - TASK-034
created: 2026-10-05
updated: 2026-10-05
---

# TASK-039: Drop the Lead passport link, show passport number and DOB on the application, timeline as a child table

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

## Part C — timeline as a Frappe child table

Owner: replace the HTML timeline with a normal child table.

`Visa Tracking Status Log` is a standalone, immutable DocType read by the
public API, so it cannot become the child table. Instead:

1. New child DocType **Visa Tracking Timeline** (`istable`, module The Visa
   Guy): `effective_on` (Datetime), `status` (Link Visa Tracking Status),
   `previous_status` (Link), `public_message` (Small Text),
   `visible_to_client` (Check), `changed_by` (Link User), `source_doctype`
   (Link DocType), `source_document` (Dynamic Link), `status_log` (Link
   Visa Tracking Status Log). All read-only, list-view columns: effective
   on, status, visible to client, changed by.
2. Visa Tracking Application: replace `timeline_html` with a Table field
   `timeline` (options Visa Tracking Timeline, read_only) in the Timeline
   section; remove the HTML render code from the form script.
3. `status_service.append_status_log` inserts the matching child row
   directly (child `insert` with parent, parenttype, parentfield; no parent
   save, no `modified` change), in the same transaction as the log.
4. Patch: backfill rows for existing applications from their Status Logs,
   ordered by `effective_on`.
5. Status Log stays the canonical record; the public timeline API still
   reads Status Log.

## Validation

- Pure tests for each part.
- Test site: migrate; the two Lead fields are gone and the Lead form still
  renders the tracking link in place; creating an application through the
  smoke chain sets the Customer link, the passport number and DOB, and adds
  timeline rows; an Operations Associate can read the two fields, a
  `Lead Role` user cannot see them; the backfill patches fill existing
  applications; on-site suite passes.

## Definition of done

Validation passes and the commit SHA is recorded here.
