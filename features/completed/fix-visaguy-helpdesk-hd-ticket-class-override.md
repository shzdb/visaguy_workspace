---
id: FEAT-visaguy-helpdesk-hd-ticket-class-override
title: Replace copied HD Ticket class with a subclass override
status: completed
priority: high
repositories: [visaguy_helpdesk]
owners: ["fasil"]
depends_on: []
created: 2026-10-29
updated: 2026-10-29
---

# Replace copied HD Ticket class with a subclass override

## Summary

`visaguy_helpdesk` overrode `HD Ticket` by copying the entire old helpdesk controller. After the Helpdesk upgrade, that copy imported `log_ticket_activity`, which no longer exists, so opening Helpdesk failed. The copy was replaced with a subclass of the current `HDTicket` that keeps only VisaGuy sender-email routing.

## User value

Agents can open Helpdesk after the upgrade. Team-mapped outgoing email still works: replies on a ticket with an `agent_group` send from the Email Account mapped in TVG HD Settings.

## Scope

### Included

- Rewrite `CustomHDTicket` to inherit `helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.HDTicket`.
- Override only `_resolve_sender_email` to apply TVG HD Settings team-to-email mapping, then call `super()`.
- Keep existing hooks, permissions, TVG HD Settings, roles, workspaces, and the reply-template monkey-patch.

### Excluded

- Rewriting the `get_default_email_content` monkey-patch.
- Cleaning duplicate `custom/hd_ticket.json` perms.
- Changes inside the `helpdesk` fork.

## Requirements

1. Loading the HD Ticket controller must not raise `ImportError`.
2. Opening `/helpdesk` must not fail on `helpdesk.api.doc.get_quick_filters`.
3. If a ticket has `agent_group` mapped in TVG HD Settings and the agent does not pick an explicit From account, the mapped Email Account is used.
4. If the agent UI passes an explicit From account, or no team mapping exists, upstream sender resolution is used.

## Proposed design

Subclass `HDTicket` and override `_resolve_sender_email`, which current `reply_via_agent` already calls. Do not copy the rest of the controller.

## Tasks

- TASK-fix-visaguy-helpdesk-hd-ticket-class-override

## Acceptance criteria

- `frappe.get_controller("HD Ticket")` returns `CustomHDTicket` and imports successfully.
- Helpdesk UI opens without the previous ImportError.
- Team-mapped reply sender still works; explicit From / unmapped team falls back to helpdesk.

## Dependencies

- Installed `helpdesk` app exposing `HDTicket._resolve_sender_email`.

## Risks

- Acknowledgement emails follow HD Settings again (the old copy had `send_acknowledgement_email` commented out). Confirm production HD Settings rather than re-copying `after_insert`.

## Open questions

None.

## Completion notes

Implemented on the remote bench `visaguy_helpdesk` app. `CustomHDTicket` now subclasses `HDTicket` and overrides `_resolve_sender_email` only. `HD Settings.send_acknowledgement_email` is `0` on site `visaguy`, so inheriting `after_insert` does not send acknowledgement emails. TVG HD Settings had 0 email-to-team rows at validation time, so mapped-sender routing was not runtime-verified; unmapped fallback to upstream `sender_email()` was exercised.
