---
id: TASK-025
feature: FEAT-001
title: Public API and session for several applications per identity
status: in-progress
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

## Objective

Let a verified client see every case they are in (ADR-015 §10).

## Required behaviour

1. `verify_identity`: load all `tracking_enabled = 1` applications for the
   hash candidates, newest status first, cap 20. Closed cases included.
2. The session stores `{application_ref: application_name}` with random
   references. Old single-application sessions keep resolving.
3. New guest POST `list_applications(session_token)` →
   `[{application_ref, destination, role, title, last_updated}]`.
4. `get_tracking_status(session_token, application_ref=None)`: reference →
   that case; unknown reference → constant generic failure; no reference →
   the session's default case.
5. Audit logs name the selected application.

## Implementation (2026-09-14)

`the_visaguy` `896930f` (with TASK-024, TASK-027). Local, not pushed.

- `session_service`: `create_session` takes one name or a list and stores
  `{"applications": [[ref, name], ...], "created_at"}`; references are
  `secrets.token_urlsafe(16)`. `resolve_application(session, ref=None)`
  returns the default (first) case or the matching reference, compared with
  `secrets.compare_digest`. A pre-ADR-015 payload (`tracking_application`)
  resolves as one case with an empty reference that no client reference
  matches. Malformed application lists drop the session.
- `api/verification.py`: `frappe.get_all(... pluck="name", order_by="status_updated_on desc, creation desc", limit=MAX_APPLICATIONS_PER_IDENTITY)`;
  no `application_closed` filter. Rate limiting and failure counting unchanged.
- `api/status.py`: rewritten around `_parse_request`, `_resolve_session`,
  `_resolve_display` (the dependant display override, unchanged in
  behaviour) and `_applicant_role` (the applicant row `type`).
  `get_tracking_status` accepts `application_ref`; a blank or non-string
  reference is `invalid_request`, an unknown one `session_invalid`.
  Closed applications are served. New `list_applications`; leaves out
  disabled applications and fails generic when none is left.
- `response_service`: `APPLICATION_ENTRY_KEYS`,
  `applications_success_response`, `build_application_entry`.

## Validation

Pure tier 317 (2 known errors) and on-site **418 OK** — see TASK-024.
Tests added: every application goes into the session; lookup query
filters, order and cap; default case, named case, unknown and malformed
references; closed application served; list entries allowlisted, ordered,
no internal names; disabled cases left out; list audited without the token;
session order and distinct references; legacy session payload; malformed
application lists. On-site: one passport on two Leads, verify → list shows
both → each reference opens its own case → a foreign reference fails.

## What remains

1. Push `the_visaguy`; deploy before the frontend (TASK-026).
2. Live HTTP smoke of `verify_identity` → `list_applications` →
   `get_tracking_status` on a deployed site.
3. Update `docs/security-and-privacy.md` / ADR-005 endpoint and payload
   tables (done in the workspace on 2026-09-14; see those files).
