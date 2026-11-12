---
id: FEAT-crm-lead-consultant-assignment-restriction
title: CRM Lead Consultant Assignment and Permission Alignment
status: completed
priority: high
repositories:
  - visaguy_frappe_crm
owners:
  - fasil
depends_on: []
created: 2026-10-13
updated: 2026-10-13
---

# CRM Lead Consultant Assignment and Permission Alignment

## Summary

Aligns Frappe CRM (`CRM Lead`) permissions and assignments with VisaGuy's single-consultant assignment policy. Ensures that users with the `Consultant Role` can only edit and manage leads actively assigned to them via an open `ToDo` (or assigned to their team senior in the Junior Senior team hierarchy), mirroring the behavior of standard ERPNext `Lead`. Prevents automatic ToDo assignments and `DocShare` records from granting permanent edit permissions to lead creators or former assignees.

## User value

- Protects lead integrity by preventing unassigned or previous consultants from modifying lead details once handed over.
- Ensures consultants see only the leads they are actively responsible for in CRM list views.
- Eliminates conflicting multi-assignee states on a single lead record.

## Scope

### Included

- Override of `CRMLead` class via `visaguy_frappe_crm` (`CustomCRMLead`).
- Suppression of automatic `DocShare` generation for `lead_owner`.
- Controlled auto-assignment on `after_insert` only when explicitly designated or created by a user with `Consultant Role`.
- Enforcement of `write` and `submit` restriction for unassigned consultants via `has_crm_lead_permission`.
- Single-assignment enforcement in `update_designated_to`: automatically cancels existing open ToDos when a new consultant is assigned.
- Desk Server Script (`Cancel unwanted  todo`) for cleaning up historical stale creator ToDos.
- Verified runtime behavior for assigned vs unassigned consultants.

### Excluded

- Frontend modifications to `apps/crm/frontend` or `apps/visaguy_frappe_crm/frontend` (kept standard/vanilla).
- Blocking `read` access (consultants with a direct link can view leads in read-only mode).
- Modifying standard `crm` fork repository code.

## Requirements

1. Users with `Consultant Role` must not be able to write or submit a `CRM Lead` unless an open `ToDo` is assigned to them (or their senior in Junior Senior group).
2. Changing `lead_owner` must not automatically re-assign or share the lead via `DocShare`.
3. Creating a new assignment must cancel existing open assignments on that lead, ensuring only one consultant is actively assigned.
4. `CRM Lead.custom_designated_to` must stay synchronized with the active open `ToDo`.
5. Existing historical open ToDos allocated to creators who are not designated consultants must be cleanable via a background/scheduler script.

## Proposed design

- **DocType Class Override**: `CustomCRMLead` extends `CRMLead` in `visaguy_frappe_crm/overrides/crm_lead.py`, registered in `hooks.py`.
- **Permission Hooks**: `has_permission` wired to `has_crm_lead_permission` in `visaguy_frappe_crm/functions/lead_restrictions.py`.
- **ToDo Lifecycle Hooks**: `doc_events` on `ToDo` for `before_save` and `on_trash` wired to `update_designated_to`.
- **Scheduler Cleanup**: Desk Server Script `Cancel unwanted  todo` queries and cancels stale open ToDos where `allocated_to = lead_owner` and `allocated_to != custom_designated_to`.

## Tasks

- `tasks/completed/align-crm-lead-permissions-with-designated-user.md`

## Acceptance criteria

- [x] Unassigned consultants cannot save changes to a `CRM Lead` (server returns permission error).
- [x] Assigned consultants can view and edit their assigned `CRM Lead`.
- [x] Read access is permitted for consultants with direct link.
- [x] Reassigning a `CRM Lead` cancels the previous consultant's open ToDo.
- [x] `custom_designated_to` matches the active assignee or is cleared when deallocated.
- [x] No `DocShare` records are automatically created on lead creation or owner change.
- [x] Frontend working tree remains unmodified.

## Dependencies

- `visaguy_frappe_crm`
- `visaguy_crm` (for `TVG User Restriction` and global helper functions `has_role`, `get_team_members`, `get_team_head`)
- `crm` (maintained fork)

## Risks

- Upstream updates to `CRMLead.validate()` or `after_insert()` must be reviewed when upgrading the `crm` app fork.
- Without custom frontend toast wrapping, unassigned consultant edit attempts reject via standard Frappe HTTP 403 responses.

## Open questions

None. All product decisions and implementation details accepted and verified.

## Completion notes

- Implemented in `visaguy_frappe_crm` on branch `lead-owner-fix`.
- Committed in `visaguy_frappe_crm` (`commit 57dfe64`), merged to `main` via PR #28 (`merge 61a4268`).
- Verified on local bench site `visaguy`.
- Committed files:
  - `visaguy_frappe_crm/functions/lead_restrictions.py`
  - `visaguy_frappe_crm/functions/update_designated_to.py`
  - `visaguy_frappe_crm/hooks.py`
  - `visaguy_frappe_crm/overrides/__init__.py`
  - `visaguy_frappe_crm/overrides/crm_lead.py`
- Frontend bundle re-built with `yarn build` to ensure compiled assets match clean source.
