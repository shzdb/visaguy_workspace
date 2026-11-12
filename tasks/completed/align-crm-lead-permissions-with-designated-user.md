---
id: TASK-align-crm-lead-permissions-with-designated-user
feature: FEAT-crm-lead-consultant-assignment-restriction
title: Align CRM Lead Permissions and Assignments with Designated User
status: completed
repository: visaguy_frappe_crm
owners:
  - fasil
depends_on: []
expected_files:
  - visaguy_frappe_crm/functions/lead_restrictions.py
  - visaguy_frappe_crm/functions/update_designated_to.py
  - visaguy_frappe_crm/hooks.py
  - visaguy_frappe_crm/overrides/__init__.py
  - visaguy_frappe_crm/overrides/crm_lead.py
created: 2026-10-13
updated: 2026-10-13
---

# Align CRM Lead Permissions and Assignments with Designated User

## Objective

Restrict write and submit access on `CRM Lead` for users with the `Consultant Role` so that only the actively designated consultant (via open `ToDo` assignment) can edit the lead, mirroring standard ERPNext `Lead` behavior. Prevent automatic `ToDo` assignment and `DocShare` generation for `lead_owner`, enforce single-assignee state on reassignment, and provide bulk cleanup for stale assignments.

## Context

In Frappe CRM (`crm`), the base `CRMLead` class automatically assigns a `ToDo` to `lead_owner` and shares the document via `DocShare` on creation and whenever `lead_owner` changes. Under VisaGuy policy (`TVG User Restriction.consultant_unassigned_lead_restriction`), consultants should only be able to view and modify leads assigned to them. Because of the base app's automatic assignment and sharing, lead creators and former assignees retained edit permissions even after leads were reassigned to other consultants.

## Inputs

- DocTypes: `CRM Lead`, `ToDo`, `TVG User Restriction`
- Roles: `Consultant Role`, `Lead Manager`, `Team Head`
- Apps: `visaguy_frappe_crm`, `visaguy_crm`, `crm`

## Required behaviour

1. **DocType Override**:
   - `CRM Lead` controller overridden by `CustomCRMLead` in `visaguy_frappe_crm/overrides/crm_lead.py`.
   - Prevent automatic `DocShare` creation for `lead_owner` (`share_with_agent` is a no-op).
   - In `validate()`, do not auto-create assignments or shares when `lead_owner` changes.
   - In `after_insert()`, auto-assign only if explicitly designated (`custom_designated_to`) or if creator has `Consultant Role`.

2. **Permission Check**:
   - `has_crm_lead_permission` hooked to `has_permission` for `CRM Lead`.
   - Restrict only `write` and `submit` permissions for users with `Consultant Role` when `consultant_unassigned_lead_restriction` is active.
   - Check whether an open `ToDo` exists for the user or their senior in `Junior Senior` group.
   - Return `True` for `read` operations so consultants with links can view.

3. **Single Assignment Enforcement**:
   - `update_designated_to` hooked on `ToDo` `before_save` and `on_trash`.
   - When a new open `ToDo` is saved, cancel all existing open ToDos on that `CRM Lead`.
   - Set `CRM Lead.custom_designated_to` to the new assignee.
   - When an open `ToDo` is cancelled, closed, or trashed, update `custom_designated_to` to any remaining open ToDo or clear it (`None`).
   - If an open `ToDo` is saved with empty `allocated_to`, automatically cancel it.

4. **Stale Assignment Cleanup**:
   - Move historical cleanup logic into Desk Server Script `Cancel unwanted  todo` (`Scheduler Event`, `Daily`) to cancel lingering open ToDos where `allocated_to = lead_owner` and `allocated_to != custom_designated_to`.

5. **Vanilla Frontend**:
   - Leave frontend Vue source unmodified to preserve clean upstream upgrade path.

## Constraints

- All custom code must stay in `visaguy_frappe_crm` (no edits to `apps/crm/` upstream repository).
- Keep changes unstaged until requested by user (currently staged on branch `lead-owner-fix` per previous session).
- Maintain documentation integrity in this workspace.

## Expected changes

- `visaguy_frappe_crm/overrides/__init__.py`: Module initializer.
- `visaguy_frappe_crm/overrides/crm_lead.py`: `CustomCRMLead` class definition.
- `visaguy_frappe_crm/functions/lead_restrictions.py`: Implement `has_crm_lead_permission` and update `lead_restrictions`.
- `visaguy_frappe_crm/functions/update_designated_to.py`: Enforce single-assignee cancellation and sync `custom_designated_to`.
- `visaguy_frappe_crm/hooks.py`: Register `override_doctype_class`, `has_permission`, and `ToDo` `doc_events` (`before_save`, `on_trash`).

## Validation

- Verified `frappe.get_doc("CRM Lead", ...)` resolves to `CustomCRMLead`.
- Verified `has_crm_lead_permission`:
  - Assigned consultant (`azeemabdullatvg@gmail.com` on `CRM-LEAD-2026-23849`): `has_permission("write")` $\rightarrow$ `True`.
  - Unassigned consultant (`harshini.tvg@gmail.com`): `has_permission("write")` $\rightarrow$ `False`.
  - Read access: `has_permission("read")` $\rightarrow$ `True`.
- Verified `ToDo` count on lead: exactly 1 open `ToDo` preserved.
- Verified Server Script `Cancel unwanted  todo` exists and is enabled in the database.
- Verified `frontend/` working tree clean, bundle rebuilt with `yarn build`, and `bench --site visaguy clear-cache` executed.

## Definition of done

- Backend overrides, permission hooks, and assignment synchronization fully implemented in `visaguy_frappe_crm`.
- Stale assignment cleanup script available in Desk Server Scripts.
- All acceptance criteria verified via bench console on site `visaguy`.
- Committed in `visaguy_frappe_crm` (`commit 57dfe64`), merged to `main` via PR #28 (`merge 61a4268`).
- ADR-005 and feature document recorded in workspace.
