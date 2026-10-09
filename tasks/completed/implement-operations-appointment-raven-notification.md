---
id: TASK-implement-operations-appointment-raven-notification
feature: FEAT-operations-appointment-raven-notification
title: Implement Operations Appointment Date Raven Notification
status: completed
repository: visaguy_raven
owners: []
depends_on: []
expected_files:
  - visaguy_raven/functions/send_operation_appointment_notification.py
  - visaguy_raven/hooks.py
created: 2026-10-08
updated: 2026-10-09
---

# Implement Operations Appointment Date Raven Notification

## Objective

Create a scheduled daily Raven notification in `visaguy_raven` that fires
2 days before a PF Process File's `custom_operations_appointment_date`,
notifying the designated user and all Operations Team Lead users in the
matching department — but only when the linked Destination has the notification
flag enabled.

## Context

PF Process Files track an `custom_operations_appointment_date` (Date field,
defined as a custom field by `visaguy_crm`). Operations staff needed proactive
2-day advance reminders so they can prepare without manual tracking.

The `Destination` DocType (in `visaguy_crm`) holds a per-destination toggle
`enable_notification_operations_appointment_date` that controls whether files
linked to that destination should trigger notifications. This allows the feature
to be enabled selectively per country/destination.

## Inputs

- `PF Process File.custom_operations_appointment_date` — trigger date.
- `PF Process File.custom_designated_to` — primary recipient (User link).
- `PF Process File.custom_department` — used to match Operations Team Lead users.
- `PF Process File.custom_destination` — used to gate the notification via
  `Destination.enable_notification_operations_appointment_date`.
- `Destination.enable_notification_operations_appointment_date` — Check field;
  notification only fires when this is 1.
- `Operations Team Lead` role — users with this role and a matching Employee
  department receive the notification.
- `send_crm_notify` helper in `visaguy_raven` — existing CRM bot DM sender.

## Required behaviour

1. Daily scheduler calls `notify_operation_appointment()`.
2. Fetch all Destination names with `enable_notification_operations_appointment_date = 1`.
   If none, stop (no-op).
3. Query PF Process Files where `custom_operations_appointment_date = today + 2`
   AND `custom_destination IN [enabled destinations]`.
   If none, stop.
4. For each matching PF Process File, enqueue a background job that:
   a. Adds `custom_designated_to` to the recipient set (if not null).
   b. Adds all active `Operations Team Lead` users whose Employee `department`
      matches `custom_department`.
   c. Sends a Raven DM via CRM bot to each unique recipient.
5. Skip the `Administrator` account from all recipient lists.
6. Skip users who are not valid Raven users (handled internally by `send_crm_notify`
   → `validate_raven_user`).

## Constraints

- Must use existing `send_crm_notify` (CRM bot) — no new bot.
- Must follow `frappe.enqueue(..., enqueue_after_commit=True)` pattern used
  throughout `visaguy_raven`.
- Must not introduce per-file N+1 destination lookups — enabled destinations
  must be fetched once and applied as an `IN` filter.
- No duplicate-send guard required.
- Must be registered in `scheduler_events.daily` in `visaguy_raven/hooks.py`.

## Expected changes

- **[NEW]** `visaguy_raven/functions/send_operation_appointment_notification.py`
- **[MODIFY]** `visaguy_raven/hooks.py` — add one entry to `scheduler_events.daily`

## Validation

- Syntax check passed: `ast.parse()` on the new module — all 5 top-level
  functions parsed correctly.
- Logic checks (6/6 passed):
  - `get_enabled_destinations()` called before PF query.
  - Early return when no enabled destinations.
  - `get_pf_files_due_in_days` receives `enabled_destinations` argument.
  - PF query filters by `custom_destination IN [...]`.
  - Early return inside `get_pf_files_due_in_days` when list is empty.
  - Destination query uses `enable_notification_operations_appointment_date = 1`.
- Manual testing instructions: create a PF Process File with appointment date
  `today + 2` and an enabled destination, then run:
  ```bash
  bench execute visaguy_raven.functions.send_operation_appointment_notification.notify_operation_appointment
  ```
  Verify Raven DM received by designated user and matching team leads.

## Definition of done

- [x] New scheduler function created and registered.
- [x] Destination gate implemented — notifications suppressed when flag is off.
- [x] Recipient resolution covers both `custom_designated_to` and
      `Operations Team Lead` users in matching department.
- [x] Syntax and logic verified.
- [x] Committed to `visaguy_raven` on branch `ops-appo-date-noti`
      (commit `aa8eb9d`).
- [x] Feature and task documents recorded in workspace.
