---
id: TASK-024
feature: FEAT-001
title: One tracking application per Lead applicant row
status: in-progress
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
4. **Reuse rule:** reuse an application only when the identity hash **and**
   the applicant row match. Same hash, different row → new application.
5. **Write the row link** with `db.set_value(update_modified=False)`.
6. **Stop writing the old Links:** `Lead/CRM Lead.custom_visa_tracking_application`
   and `Customer.custom_visa_tracking_application`.
7. **Destination:** mandatory Link to `Destination`, filled from
   `Lead/CRM Lead.custom_destination` at creation.
8. **Remove `visa_type`** from the DocType, the status API, the response
   allowlist and the tests.
9. **Do not delete** the old Lead/Customer fields in this task (risk 25).

## Implementation (2026-09-14)

`the_visaguy` `896930f` (together with TASK-025 and TASK-027; the three
share constants, fixtures and tests). Pushed 2026-09-14 (`8cf4c64..896930f`).

- `lifecycle_service`: `resolve_applicant_row`, `_reusable_application`,
  `_write_applicant_row_link`, `_link_lead_extraction`;
  `create_tracking_application` rewritten to the rules above. A row that
  links an application for a **different** identity gets a new application
  and a "Visa tracking: applicant passport changed" review flag. A Lead with
  no destination, or with no resolvable row, creates nothing and is flagged.
  `link_verified_extraction_to_lead/_customer` write the extraction Link
  only. `find_active_tracking_application_for_extraction` and
  `_find_active_applications_for_identity` are removed.
- `lead_handlers.sync_customer_tracking_links`: copies the extraction Link
  and sets `customer` on every application whose `lead` is the Customer's
  Lead. No Customer-level tracking Link.
- `visa_tracking_application.json`: `destination` → Link `Destination`,
  `reqd`; `visa_type` removed. Controller `_validate_lead_reference`.
- `fixtures/custom_fields.json`: new `Applicant Information-visa_tracking_application`.
- `patches/link_tracking_applications_to_applicant_rows.py` (post-model-sync):
  creates the custom field if the fixture has not synced yet, fills an empty
  destination from the Lead, and links each application from its row when
  the row resolves and is unlinked. Prints counts; guesses nothing.
- `response_service` / `api/status.py`: `visa_type` removed.

## Validation

| Check | Result |
|---|---|
| Pure tier (`unittest discover`) | 317 run, 20 skipped, 2 errors — the known `TestProcessFileHandler` site-context errors |
| `bench --site visa-tracker-test.localhost migrate` | exit 0; the patch ran (0 applications on the test site) |
| On-site (`run-tests --app the_visaguy --skip-test-records`) | **418 run, OK** |

New or rewritten tests: applicant row picked by collection; reuse only for
the linked row and same identity; same passport on another row gets its own
application; row linked to another identity; ambiguous rows; Lead without
rows; Lead without destination; Customer on every application of the Lead;
exactly one lead reference; destination mandatory and `visa_type` gone; the
backfill patch fills and links, and is idempotent. On-site: the same
passport on two Leads yields two applications, each linked from its own row.

Test fixtures now build Leads with one applicant row
(`fixtures.make_lead_with_applicant`) and give directly inserted
applications a Lead and destination (`fixtures.tracking_application_references`).

## What remains

1. Push `the_visaguy` `feat/visa-tracker`.
2. Deploy. Read the patch's printed counts on `visaguy` (11 applications
   there); an application whose row does not resolve stays unlinked (risk 41).
3. Later: an explicit patch that deletes `Lead/CRM Lead/Customer.custom_visa_tracking_application`
   (risk 39). Never through a fixture sweep.
