---
id: TASK-fix-visaguy-helpdesk-hd-ticket-class-override
feature: FEAT-visaguy-helpdesk-hd-ticket-class-override
title: Fix visaguy_helpdesk HD Ticket override after Helpdesk upgrade
status: completed
repository: visaguy_helpdesk
owners: ["fasil"]
depends_on: []
expected_files:
  - visaguy_helpdesk/server_scripts/hd_ticket_class_override.py
  - docs/architecture/customizations.md
created: 2026-10-29
updated: 2026-10-29
---

# Fix visaguy_helpdesk HD Ticket override after Helpdesk upgrade

## Objective

Stop copying the entire old `HD Ticket` controller. Inherit the current helpdesk `HDTicket` class and override only team-based outgoing email resolution so Helpdesk opens after the upgrade.

## Context

Opening Helpdesk calls `helpdesk.api.doc.get_quick_filters`, which loads the HD Ticket controller. `visaguy_helpdesk` overrides that class with a full copy of an older `HDTicket`. The copy still imports `log_ticket_activity`, which the upgraded helpdesk app removed, causing:

`ImportError: cannot import name 'log_ticket_activity' from 'helpdesk.helpdesk.doctype.hd_ticket_activity.hd_ticket_activity'`

The only VisaGuy class-level behaviour in that copy is routing `reply_via_agent` through TVG HD Settings (Email Account mapped to HD Team). Current helpdesk already has `_resolve_sender_email()` as the hook for that.

## Inputs

- `visaguy_helpdesk/server_scripts/hd_ticket_class_override.py`
- `helpdesk/helpdesk/doctype/hd_ticket/hd_ticket.py` (`HDTicket._resolve_sender_email`)
- `TVG HD Settings.email_account_and_hd_team`

## Required behaviour

- `CustomHDTicket` subclasses `HDTicket`.
- `_resolve_sender_email` uses the TVG HD Settings mapping when no explicit From account is passed.
- Explicit From account and unmapped teams call `super()._resolve_sender_email(...)`.
- Existing doc_events, permission query, ToDo assignment rules, and the reply-template monkey-patch remain unchanged.

## Constraints

- Do not copy the full helpdesk controller.
- Do not modify the `helpdesk` fork for this fix.
- Leave git changes unstaged for review.

## Expected changes

- Replace `hd_ticket_class_override.py` with a short subclass.
- Update `docs/architecture/customizations.md` to record that HD Ticket is a subclass override of `_resolve_sender_email`.

## Validation

Performed on remote bench `/home/fasil/fasil-bench2`, site `visaguy`:

- **runtime-verified**: `frappe.get_controller("HD Ticket")` returns `CustomHDTicket`; MRO is `CustomHDTicket` → `HDTicket` → `Document`.
- **runtime-verified**: `helpdesk.api.doc.get_quick_filters("HD Ticket")` returns 4 filters with no ImportError.
- **runtime-verified**: `HD Settings.send_acknowledgement_email` is `0`.
- **runtime-verified**: `https://visaguy-fsl.code.tridz.in/login` and `/helpdesk` return HTTP 200 after bench restart.
- **configured-unverified**: TVG HD Settings had 0 `email_account_and_hd_team` rows, so team-mapped sender routing was not exercised against live mappings. Unmapped `_resolve_sender_email(None, None)` fell through to upstream `sender_email()`.
- Authenticated Helpdesk agent UI (reply as agent) was not exercised; browser hits the login wall.

Change left unstaged on remote `visaguy_helpdesk` branch `class-override-fix` (`M visaguy_helpdesk/server_scripts/hd_ticket_class_override.py`).

## Definition of done

- Copied controller removed; subclass override in place.
- Workspace feature/task and customizations doc updated.
- Import and Helpdesk-open checks recorded.
