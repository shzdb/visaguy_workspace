---
id: TASK-implement-sales-team-membership-from-invoice-company
feature: FEAT-sales-team-membership-from-invoice-company
title: Implement Sales Team Membership from Invoice Company
status: completed
repository: visaguy_hrms
owners: []
depends_on: []
expected_files:
  - visaguy_hrms/custom_scripts/employee_hooks.py
  - visaguy_hrms/hooks.py
created: 2026-11-05
updated: 2026-11-05
---

# Implement Sales Team Membership from Invoice Company

## Objective

Fill Sales Team Employee Group child tables from the Employee record when
Invoice Company and Zoho Sales Person ID are set, and remove the employee
when Invoice Company is cleared or the employee is no longer Active.

## Context

Sales Team members were added by hand. Team Head is `custom_team_head` on
Employee Group (a User). Members live on `employee_list` (Employee Group
Table). Group type is `custom_group_type`: Sales Team or Junior Senior.

## Inputs

- Employee `custom_invoice_company`, `custom_zoho_sales_person_id`, `status`,
  `user_id`, `employee_name`.
- Employee Group `custom_team_head`, `custom_group_type`, `employee_list`.
- Team head Invoice Company: Employee.`custom_invoice_company` where
  `user_id` equals `custom_team_head`.

## Required behaviour

1. Employee `on_update` runs when Invoice Company, Zoho Sales Person ID, or
   status changed.
2. Enqueue `sync_sales_team_groups` with `enqueue_after_commit=True` on the
   short queue. The save does not update groups itself.
3. Enqueue when status is not Active.
4. Enqueue when Invoice Company was cleared.
5. Enqueue when status is Active and both Invoice Company and Zoho Sales
   Person ID are set.
6. Do not enqueue when only Zoho Sales Person ID is cleared and Invoice
   Company is still set.
7. Worker, if status is not Active: remove the employee from every Sales
   Team group except the one they head. Do not add.
8. Worker, if Active and Zoho Sales Person ID is empty while Invoice Company
   is set: make no membership change.
9. Worker, if Active and Invoice Company is empty: remove from Sales Team
   groups except the one they head.
10. Worker, if Active and both fields are set: add to every Sales Team whose
    team head has the same Invoice Company; remove from the other Sales
    Teams; do not add them to the group they head.
11. Do not read or write Junior Senior groups.
12. Child rows set `employee`, `employee_name`, and `user_id`.

## Constraints

- Implement only on the SSH bench `fasil-bench2`
  (`ssh -p 2203 fasil@code.tridz.in`), site `visaguy`.
- Do not edit a local bench, including `/home/fasil/Tridz/bench_v15`.
- Place the hook in `visaguy_hrms`.
- Leave git changes unstaged. Do not commit or push unless asked.
- Keep the existing Employee `validate` handler for pending leave applications.

## Expected changes

- **[MODIFY]** `visaguy_hrms/custom_scripts/employee_hooks.py` — queue and
  apply Sales Team membership sync.
- **[MODIFY]** `visaguy_hrms/hooks.py` — Employee `on_update`.

## Validation

- `py_compile` passed on `employee_hooks.py` on `fasil-bench2`.
- Hook wiring: Employee `on_update` is
  `visaguy_hrms.custom_scripts.employee_hooks.sync_sales_team_membership`.
  `validate` is still `check_pending_leave_applications`.
- Rolled-back site script on `visaguy` checked:
  - add to every matching Sales Team
  - move when Invoice Company changes
  - skip the group the employee heads
  - clear Invoice Company removes Sales Team rows
  - clear only Zoho Sales Person ID leaves rows
  - Inactive and Left remove Sales Team rows and do not add
  - Active again with both fields set adds them back
  - Junior Senior rows stay
  - status change to Inactive enqueues the worker
- Script rolled back. No `@stsync.test` users remained.
- Requester confirmed ("all good"). Live Desk save after process restart
  was not separately runtime-verified.

## Definition of done

- [x] Sync queued from Employee `on_update` after commit.
- [x] Active employees with both fields are added to every matching Sales Team.
- [x] Empty Invoice Company removes them from Sales Team groups.
- [x] Non-Active status removes them and does not add.
- [x] Own-group and Junior Senior exclusions hold.
- [x] Syntax and hook wiring checked on `fasil-bench2`.
- [x] Feature and task documents recorded in the workspace.
- [x] Requester confirmed behaviour.
