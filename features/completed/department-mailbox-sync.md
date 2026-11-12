---
id: FEAT-department-mailbox-sync
title: Department mailbox sync
status: completed
priority: medium
repositories: [visaguy_helpdesk, visaguy_crm]
owners: []
depends_on: []
created: 2026-11-05
updated: 2026-11-09
---

# Department mailbox sync

## Summary

Operations users receive the mailbox for their department on User Emails. The mailbox comes from TVG HD Settings. The New Email From list reads those User Email rows.

## User value

Operations Associate and Operations Team Lead users can send client email from the department mailbox. Staff no longer add that mailbox by hand on each User.

## Scope

### Included

- Match `Email and HD Team.department` to an Active Employee `department`.
- Add the mapped Email Account to User Emails when it is missing.
- Remove that Email Account when the user no longer qualifies.
- Queue the sync after the save commits.
- Backfill existing users with a patch. The patch is registered. Migrate has not run.

### Excluded

- Ticket `agent_group` and reply sender selection. Those still use Email Account and HD Team.
- Mailboxes that are not on TVG HD Settings.
- A wait on the desk save for the sync to finish.

## Requirements

Keep a mailbox on the user only when all of these are true:

- The user is enabled and is not Administrator.
- The user has Operations Associate or Operations Team Lead.
- An Active Employee uses that `user_id`.
- A TVG HD Settings row maps that Employee department to the Email Account.

Remove only Email Accounts that appear on TVG HD Settings. Leave every other User Email row in place.

## Proposed design

`visaguy_helpdesk` owns the sync. `visaguy_crm` only detects Employee and User changes and queues the sync. TVG HD Settings `on_update` queues a full sync when an email account or department pair changes.

The Employee hook is in `visaguy_crm` by request. The project rule places Employee hooks in `visaguy_hrms`. This feature is the exception.

## Tasks

- [x] TASK-sync-department-mailboxes

## Acceptance criteria

- [x] An eligible user gains the department mailbox.
- [x] The same mailbox is not added twice.
- [x] A user without an operations role, a disabled user, an inactive Employee, or a different department does not keep a managed mailbox.
- [x] A change of Employee user, department, or status updates the previous user and the current user.
- [x] Removal of an operations role, or disabling the user, removes the managed mailbox.
- [x] A TVG HD Settings row add, delete, or department or email change updates the affected users.
- [x] An HD Team-only edit does not queue a sync.
- [x] A User Email for an account outside TVG HD Settings stays in place.
- [ ] Existing users are updated on the site. The patch has not run.

## Dependencies

- `Email and HD Team.department` links to Department. The field is already on the bench.
- Employee `user_id`, `department`, and `status`.
- User Emails on User. Frappe uses those rows for the New Email From list.

## Risks

- `bench migrate` runs `reconcile_all` on the live site. It adds and removes managed mailboxes for current users.
- The desk shows the new From list after a refresh. The sync clears the user cache after a real change.
- A managed mailbox added by hand to a user who does not qualify is removed on the next sync.

## Open questions

None.

## Completion notes

Code is on the remote bench and is not committed. Tests passed on site `visaguy`. See TASK-sync-department-mailboxes.

Status is **source-wired**. The tests called the modules directly. A live Employee save, User role change, and TVG HD Settings save on the running workers are not runtime-verified. The backfill patch has not run.
