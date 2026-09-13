---
id: TASK-025
feature: FEAT-001
title: Public API and session for several applications per identity
status: blocked
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-015
  - TASK-024
created: 2026-09-14
updated: 2026-09-14
---

# TASK-025: Public API and session for several applications per identity

## Blockers

- TASK-024 (applications must exist per applicant row first).

## Objective

Let a verified client see every case they are in (ADR-015 §7).

## Required behaviour

1. `verify_identity` step 5: load all `tracking_enabled = 1` applications
   matching the hash candidates, order by `status_updated_on desc`, cap 20.
   Closed and completed cases are included like any other (ADR-015 §5).
   No match → unchanged failure path and counters.
2. `session_service.create_session` stores
   `{application_ref: application_name}` with refs from `secrets.token_urlsafe`.
   `resolve_session` returns the map. Old single-application sessions keep
   resolving until they expire.
3. New guest POST `list_applications(session_token)` →
   `[{application_ref, destination, visa_type, role, title, last_updated}]`.
   `role` is `Primary` / the dependant type from the case's Process File,
   or the applicant row `type` before one exists.
4. `get_tracking_status(session_token, application_ref=None)`:
   - ref given → that case; unknown ref → constant generic failure;
   - no ref and one application → today's response, byte-for-byte shape;
   - no ref and several → the most recently updated (documented) so an old
     SPA still renders something sensible.
5. Audit logs name the selected application.
6. Update `response_service` allowlists and ADR-005's payload table.

## Validation

- 1, 2 and 21 applications for one identity; cap enforced.
- A ref from another session fails generically; refs never equal names.
- Single-case response unchanged against `wireContract.ts`.
- Live HTTP smoke of all four endpoints on the test site.
