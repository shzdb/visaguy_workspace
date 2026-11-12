---
id: TASK-sync-department-mailboxes
feature: FEAT-department-mailbox-sync
title: Sync department mailboxes to operations users
status: completed
repository: visaguy_helpdesk
owners: []
depends_on: []
expected_files:
  - visaguy_helpdesk/server_scripts/department_mailbox_sync.py
  - visaguy_helpdesk/server_scripts/test_department_mailbox_sync.py
  - visaguy_helpdesk/visaguy_helpdesk/doctype/tvg_hd_settings/tvg_hd_settings.py
  - visaguy_helpdesk/patches/sync_department_mailboxes.py
  - visaguy_helpdesk/patches.txt
  - visaguy_crm/server_scripts/employee/department_mailbox_hooks.py
  - visaguy_crm/server_scripts/employee/test_department_mailbox_hooks.py
  - visaguy_crm/hooks.py
created: 2026-11-05
updated: 2026-11-09
---

# Sync department mailboxes to operations users

## Objective

Keep User Emails aligned with TVG HD Settings for Operations Associate and Operations Team Lead users. Run the sync in a background job.

## Context

The New Email From list comes from User Email rows with outgoing mail enabled. TVG HD Settings already maps an Email Account to an HD Team. The Department field on `Email and HD Team` maps that mailbox to an Employee department.

The Employee and User hooks live in `visaguy_crm`. The sync and the settings hook live in `visaguy_helpdesk`.

## Inputs

- `Email and HD Team.email_account` and `department` on TVG HD Settings.
- Employee `user_id`, `department`, and `status`.
- User roles, `enabled`, and `user_emails`.

## Required behaviour

1. A user keeps a settings mailbox only while the user is enabled, has an operations role, and an Active Employee department matches the settings row.
2. Add a missing mailbox. Copy `email_id`, `enable_outgoing`, and `awaiting_password` from the Email Account. Set `used_oauth` when the account auth method is OAuth.
3. Remove a User Email row only when its account is on TVG HD Settings, or was on the settings document before this save, and the user no longer matches it.
4. Queue the job with `enqueue_after_commit=True` on queue `short`. The save does not wait.
5. Employee `on_update` queues the previous user and the current user when `user_id`, `department`, or `status` changes.
6. Employee `on_trash` queues that user.
7. User `on_update` queues that user when an operations role, `enabled`, or the User Email account set changes. A save from the sync itself does not queue again.
8. TVG HD Settings `on_update` queues a full sync when an email account and department pair changes. An HD Team-only edit does nothing.
9. The patch calls `reconcile_all()` during migrate.

## Constraints

- Do not change HD Ticket sender routing.
- Do not commit. Do not run migrate as part of this task.
- Skip the CRM hooks when `visaguy_helpdesk` is not installed.
- Leave the existing Department field on `Email and HD Team` unchanged.

## Expected changes

- **[NEW]** `visaguy_helpdesk/server_scripts/department_mailbox_sync.py`
- **[NEW]** `visaguy_helpdesk/server_scripts/test_department_mailbox_sync.py`
- **[MODIFY]** `visaguy_helpdesk/visaguy_helpdesk/doctype/tvg_hd_settings/tvg_hd_settings.py`
- **[NEW]** `visaguy_helpdesk/patches/sync_department_mailboxes.py`
- **[MODIFY]** `visaguy_helpdesk/patches.txt`
- **[NEW]** `visaguy_crm/server_scripts/employee/department_mailbox_hooks.py`
- **[NEW]** `visaguy_crm/server_scripts/employee/test_department_mailbox_hooks.py`
- **[MODIFY]** `visaguy_crm/hooks.py`

Paths are under `/home/fasil/fasil-bench2/apps/` on the remote bench.

## Validation

Commands on site `visaguy`:

```bash
CI=1 bench --site visaguy run-tests --skip-before-tests \
  --module visaguy_helpdesk.server_scripts.test_department_mailbox_sync
```

Result: 11 tests passed.

```bash
CI=1 bench --site visaguy run-tests --skip-before-tests \
  --module visaguy_crm.server_scripts.employee.test_department_mailbox_hooks
```

Result: 10 tests passed.

`CI=1` was required because the site has no `allow_tests` config. `--skip-before-tests` was required because the India Compliance `before_tests` hook fails on a mandatory Company field. After the runs, TVG HD Settings still had its 2 rows.

Status: **source-wired**. Live form saves on the running workers were not checked.

## Definition of done

- [x] Sync module, settings hook, CRM hooks, and tests are on the remote bench.
- [x] Helpdesk tests passed (11).
- [x] CRM hook tests passed (10).
- [x] Workspace feature and task documents updated.
- [ ] Code committed. Not requested.
- [ ] `bench migrate` run. The patch is registered and has not executed.
