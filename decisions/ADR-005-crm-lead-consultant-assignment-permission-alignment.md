# ADR-005: CRM Lead Consultant Assignment and Permission Alignment

**Date:** 2026-10-13  
**Status:** Accepted  

## Context

In Frappe CRM (`crm`), the standard `CRMLead` controller automatically creates a `ToDo` assignment for the `lead_owner` in `after_insert()` and whenever `lead_owner` changes in `validate()`. It also automatically generates a `DocShare` record for `lead_owner` (`share_with_agent`).

Under VisaGuy's business rules (configured in `TVG User Restriction` via `consultant_unassigned_lead_restriction`), users with the **Consultant Role** must only be allowed to edit and manage leads that are actively assigned to them via an open `ToDo` (or assigned to their senior in the Junior Senior team hierarchy).

In the legacy `visaguy_crm` app on ERPNext `Lead`, this restriction was strictly enforced. However, in Frappe CRM (`CRM Lead`), any consultant who created a lead or was set as `lead_owner` retained continuous access because Frappe CRM created a `ToDo` and a `DocShare` for the owner. Furthermore, when a lead was subsequently assigned to another consultant, the previous consultant's `ToDo` remained open, creating multiple simultaneous assignments and bypassing the single-consultant ownership model.

## Decision

We align `CRM Lead` assignment and permission behaviour with standard `Lead` logic entirely within `visaguy_frappe_crm`:

1. **DocType Class Override (`CustomCRMLead`)**:
   - Register `override_doctype_class` in `visaguy_frappe_crm/hooks.py` pointing `CRM Lead` to `visaguy_frappe_crm.overrides.crm_lead.CustomCRMLead`.
   - Override `validate()` to remove automatic assignment creation and DocShare generation when `lead_owner` changes.
   - Override `after_insert()` so that auto-assignment happens **only** if `custom_designated_to` is already provided, or if the creator has `Consultant Role` (matching standard `Lead` creation rules).
   - Override `share_with_agent()` as a no-op to suppress automatic `DocShare` creation for `lead_owner`.

2. **Permission Hook (`has_crm_lead_permission`)**:
   - Register `has_permission` in `visaguy_frappe_crm/hooks.py` for `CRM Lead` pointing to `visaguy_frappe_crm.functions.lead_restrictions.has_crm_lead_permission`.
   - Restrict only `write` and `submit` operations when `consultant_unassigned_lead_restriction` is active. Unassigned consultants cannot modify or submit the lead.
   - Read operations (`ptype="read"`) remain permitted so that consultants with a direct link can view details without edit capabilities.

3. **Single-Assignment ToDo Synchronization (`update_designated_to`)**:
   - Hook `ToDo` on `before_save` and `on_trash` in `visaguy_frappe_crm/hooks.py`.
   - When an open `ToDo` is created or updated with a valid `allocated_to`, automatically cancel any other existing open `ToDo` records referencing the same `CRM Lead`, ensuring exactly one active assignee.
   - Keep `CRM Lead.custom_designated_to` synchronized with the active `allocated_to` user.
   - When a `ToDo` is cancelled, closed, or trashed, re-evaluate remaining open ToDos and update or clear `custom_designated_to`.

4. **Stale Creator Assignment Cleanup**:
   - A Desk **Server Script** (`Cancel unwanted  todo`) of type `Scheduler Event` (`Daily`) cleans up legacy open `ToDo` records where `allocated_to = lead_owner` and `allocated_to != custom_designated_to`.

5. **Vanilla Frontend**:
   - Do not customize the upstream Frappe CRM frontend (`apps/crm/frontend` or `visaguy_frappe_crm/frontend`). Leave the frontend clean and unedited to preserve upgrade compatibility.

## Consequences

### Positive

- Enforces VisaGuy's single-consultant assignment policy across Frappe CRM.
- Prevents consultants from modifying leads that have been reassigned to other team members.
- Suppresses unnecessary `DocShare` records that previously granted permanent backdoor access.
- Eliminates duplicate open ToDos on a single `CRM Lead`.
- Implementation is self-contained in `visaguy_frappe_crm` without modifying upstream `crm` repository code.

### Negative

- Lead creators who are consultants lose write access once the lead is assigned to a different consultant (this is the desired business requirement).
- When an unassigned consultant attempts an inline edit, the server rejects the request with HTTP 403 / permission error.

## Alternatives considered

- **Modifying frontend error toasts in `visaguy_frappe_crm/frontend`**: Explored and prototyped, but discarded to keep the Vue frontend bundle clean and avoid maintenance burden during upstream Frappe CRM frontend updates.
- **Modifying the `crm` fork directly**: Rejected because all VisaGuy-specific business logic and permission overrides must reside in `visaguy_frappe_crm`.

## Revisit when

- Frappe CRM upstream introduces native role-based field-level or assignment-based permission guards.
- Additional roles beyond `Consultant Role` require assignment-scoped write restrictions.
