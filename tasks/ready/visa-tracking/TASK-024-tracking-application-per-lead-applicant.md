---
id: TASK-024
feature: FEAT-001
title: One tracking application per Lead applicant row
status: ready
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-015
created: 2026-09-14
updated: 2026-09-14
---

# TASK-024: One tracking application per Lead applicant row

## Objective

Create one Visa Tracking Application per applicant per case, so one passport
can have several applications (ADR-015).

## Required behaviour

1. **Applicant row link.** Custom Field fixture
   `Applicant Information.visa_tracking_application` (Link →
   `Visa Tracking Application`, read-only, `no_copy`).
2. **Trace back to the Lead.** `create_tracking_application` starts from the
   Lead given by `_resolve_source_lead`. Exactly one of `lead` / `crm_lead`
   is set on the application; validate this in the controller.
3. **Find the applicant row inside that Lead** (ADR-015 §4): the row whose
   `file_collection` equals the source collection; else the only row if the
   Lead has one; else `_flag_review` and return `None`.
4. **Reuse rule:** reuse an active application only when the identity hash
   **and** the applicant row match. Same hash, different row → new
   application. Flag review only for several active applications on one
   row.
5. **Write the row link** with `db.set_value(update_modified=False)` on the
   child row (same reason as `d59614f`).
6. **Stop writing the old Links:** `Lead/CRM Lead.custom_visa_tracking_application`
   (`_ensure_lead_links`, `link_verified_extraction_to_lead`) and
   `Customer.custom_visa_tracking_application`
   (`link_verified_extraction_to_customer`, `lead_handlers`).
   `custom_passport_extraction` behaviour is unchanged.
7. **Destination:** `Visa Tracking Application.destination` becomes a
   mandatory Link to `Destination`, filled from
   `Lead/CRM Lead.custom_destination` at creation.
8. **Remove `visa_type`:** the DocType field
   (`visa_tracking_application.json`), `api/status.py` `_APPLICATION_FIELDS`,
   `response_service.STATUS_RESPONSE_KEYS` and the payload builder, and the
   tests that reference it (`test_response_service.py`, `test_public_api.py`,
   `test_visa_tracking_application.py`). Update ADR-005's payload table and
   `docs/security-and-privacy.md`.
9. **Do not delete** the old Lead/Customer fields in this task. Record a
   follow-up patch; never remove them through a fixture sweep (risk 25).

## Constraints

- No change to ADR-014 Process File ownership.
- No data backfill without an owner decision.
- Deploy order: removing `visa_type` from the payload is safe before the SPA
  change, because `StatusSummary` renders visa type only when present.
  TASK-026 removes it from the SPA's types and contract.

## Validation

- Same passport on two applicant rows (two Leads, and two rows in one Lead)
  → two applications, each row linked to its own, each with its Lead Link.
- Redelivery on the same row → one application.
- Lead with several rows and no matching collection → review flag, no
  application.
- Primary in Lead A, dependant in Lead B → each application resolves its
  own role through its Process File.
- No `lead`/`crm_lead`, or no destination → cannot save.
- The second Lead no longer points at the first case's application.
- Status payload has no `visa_type` key.
- On-site suite green on `visa-tracker-test.localhost`.
