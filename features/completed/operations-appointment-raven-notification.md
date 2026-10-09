---
id: FEAT-operations-appointment-raven-notification
title: Operations Appointment Date Raven Notification
status: completed
priority: medium
repositories: [visaguy_raven]
owners: []
depends_on: []
created: 2026-10-08
updated: 2026-10-09
---

# Operations Appointment Date Raven Notification

## Summary

A scheduled daily Raven notification that fires **2 days before** a PF Process
File's `custom_operations_appointment_date`. The notification is gated by a
per-destination toggle (`enable_notification_operations_appointment_date` on the
Destination master) and is delivered via the CRM bot as Raven direct messages.

## User value

Operations staff are proactively reminded about upcoming appointment dates for
active process files 2 days in advance, giving them sufficient time to prepare.
The designated agent (Designated To field) and all Operations Team Lead users in
the same department receive the alert automatically without manual tracking.

## Scope

### Included

- Daily scheduler function in `visaguy_raven` that queries PF Process Files due
  in 2 days and dispatches Raven DMs.
- Recipient resolution:
  1. The user in `custom_designated_to` on the PF Process File (if set).
  2. All active `Operations Team Lead` role users whose Employee department
     matches the PF Process File's `custom_department`.
- Destination-level gate: notification only fires when the linked Destination
  record has `enable_notification_operations_appointment_date = 1`.
- Uses the existing CRM bot (`send_crm_notify`) — no new bot or Raven channel
  created.

### Excluded

- Same-day or day-before reminder variants (only 2-day advance notification).
- Duplicate-send guards (scheduler runs once daily by Frappe design).
- Notification for PF Process Files with no `custom_destination` set.
- Users with no linked Employee record or whose Employee is not Active.

## Requirements

- Query Destination records for `enable_notification_operations_appointment_date = 1`
  before touching the PF Process File table (early exit if none enabled).
- Filter PF Process Files by `custom_operations_appointment_date = today + 2`
  AND `custom_destination IN [enabled destinations]`.
- For each matching file, enqueue a background job per Frappe's async pattern.
- Skip `custom_designated_to` if null/empty.
- Skip Operations Team Lead users with no active Employee in the matching
  department.
- Exclude the `Administrator` system account from all recipient lists.

## Proposed design

See Completion Notes for the implemented architecture.

## Tasks

- [x] TASK-implement-operations-appointment-raven-notification

## Acceptance criteria

- [x] Raven DM sent to `custom_designated_to` user when appointment is 2 days out
      and destination has notification enabled.
- [x] Raven DM sent to all matching `Operations Team Lead` users in the same
      department when appointment is 2 days out and destination enabled.
- [x] No notification sent when destination has `enable_notification_operations_appointment_date = 0`.
- [x] No notification sent when destination flag is enabled but no PF Process
      Files match the date.
- [x] Function exits immediately (no DB load on PF table) when no destinations
      have the flag enabled.

## Dependencies

- `visaguy_raven` app — existing CRM bot and `send_crm_notify` helper.
- `Destination` DocType (in `visaguy_crm`) — `enable_notification_operations_appointment_date` field.
- Custom fields on `PF Process File` (in `visaguy_crm` custom/):
  `custom_operations_appointment_date`, `custom_designated_to`, `custom_department`,
  `custom_destination`.
- `Operations Team Lead` role (in `visaguy_crm` fixtures).
- Employee DocType — `user_id` and `department` fields for role-to-department mapping.

## Risks

- If a Destination record is renamed, existing PF Process Files with
  `custom_destination` storing the old name will not match and will be silently
  excluded. (Acceptable — consistent with existing `custom_destination` Data field
  design elsewhere in the codebase.)

## Open questions

None — all resolved during implementation planning.

## Completion notes

### Implementation

Single new file added to `visaguy_raven`, one line added to `hooks.py`.

**`visaguy_raven/functions/send_operation_appointment_notification.py`**

| Function | Role |
|---|---|
| `notify_operation_appointment()` | Daily scheduler entry-point registered in `hooks.py`. Calls `get_enabled_destinations()` first; exits immediately if none are enabled. Passes the enabled list into `get_pf_files_due_in_days()` and enqueues one background job per matching file. |
| `_notify_operation_appointment(...)` | Queued background worker. Builds the recipient set, constructs the message text, and calls `send_crm_notify()` for each user. |
| `get_enabled_destinations()` | Queries `Destination WHERE enable_notification_operations_appointment_date = 1`; returns list of destination names (which are also the values stored in `PF Process File.custom_destination` due to `autoname = field:destination`). |
| `get_pf_files_due_in_days(days, enabled_destinations)` | Queries PF Process Files matching both the target date (`today + 2`) and `custom_destination IN [enabled_destinations]`. Returns `[]` immediately if the list is empty. |
| `get_operations_team_leads(department)` | Looks up users with `Operations Team Lead` role via `Has Role`, then cross-references with active Employee records in the given department. |

**Notification text:**
> 📅 Operations Appointment in 2 Days: {applicant_name}'s operations appointment
> is scheduled in 2 days ({date}). Please take the necessary action.

**`visaguy_raven/hooks.py`** — one-line addition to `scheduler_events.daily`:
```python
"visaguy_raven.functions.send_operation_appointment_notification.notify_operation_appointment"
```

### Query strategy

Destination flag is checked first (lightweight single-table query) to avoid
loading the PF Process File table when no destinations are configured. The PF
Process File query uses a compound filter (`date + destination IN list`) rather
than per-file N+1 lookups.

### Commit

- **Repository:** `visaguy_raven`
- **Branch:** `ops-appo-date-noti`
- **Commit:** `aa8eb9d` — _feat: notify designated user and ops team leads 2 days before operations appointment date_
