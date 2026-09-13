---
id: TASK-024
feature: FEAT-001
title: One tracking application per Lead applicant row
status: blocked
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-015
created: 2026-09-14
updated: 2026-09-14
---

# TASK-024: One tracking application per Lead applicant row

## Blockers

- **ADR-015 O1:** no visa type field exists on `Lead` / `CRM Lead`. Name the
  source, or confirm `visa_type` stays empty for now.
- **ADR-015 O2:** confirm that creation finds the applicant row through
  `Applicant Information.file_collection` = the extraction's source
  collection.

## Objective

Create one Visa Tracking Application per applicant per case, so one passport
can have several applications (ADR-015).

## Required behaviour

1. Custom Field fixture `Applicant Information.visa_tracking_application`
   (Link → `Visa Tracking Application`, read-only, no copy).
2. `create_tracking_application` resolves the applicant row (per O2) and:
   - reuses an application only when hash **and** applicant row match;
   - otherwise creates a new one;
   - flags review only for several active applications on one row.
3. Write the application name to the applicant row with
   `db.set_value(update_modified=False)` (same reason as `d59614f`).
4. Stop writing `Lead/CRM Lead.custom_visa_tracking_application`
   (`_ensure_lead_links`, `link_verified_extraction_to_lead`) and
   `Customer.custom_visa_tracking_application` (`link_verified_extraction_to_customer`,
   `lead_handlers`). Keep `custom_passport_extraction` behaviour unchanged.
5. `destination` ← `Lead/CRM Lead.custom_destination`; make
   `Visa Tracking Application.destination` mandatory. `visa_type` per O1.
6. Do **not** delete the old Lead/Customer fields in this task. Record a
   follow-up patch; never remove them through a fixture sweep (risk 25).

## Constraints

- No change to ADR-014 Process File ownership.
- No data backfill without an owner decision.

## Validation

- Same passport on two applicant rows (two Leads, and two rows in one Lead)
  → two applications, each row linked to its own.
- Redelivery on the same row → one application.
- Primary in Lead A, dependant in Lead B → each application resolves its
  own role through its Process File.
- Missing `custom_destination` cannot create an application.
- The second Lead no longer points at the first case's application.
- On-site suite green on `visa-tracker-test.localhost`.
