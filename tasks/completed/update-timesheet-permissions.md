---
id: TASK-005
feature: FEAT-000
title: Update timesheet permission query for accounts users
status: completed
repository: visaguy_hrms
owners: []
depends_on: []
expected_files:
  - overrides/timesheet_permission_query.py
created: 2026-10-09
updated: 2026-10-09
---

# Update timesheet permission query for accounts users

## Objective
Restrict Accounts and Finance users from viewing all submitted timesheets unless they are also an OT Approver.

## Context
Previously, anyone with an "Accounts User - TVG" or "Finance Manager - TVG" role could view all submitted timesheets. The new requirement restricts this so that only users possessing BOTH an Accounts/Finance role AND the "OT Approver" role can view all submitted timesheets.

## Inputs
None

## Required behaviour
- Users with only an Accounts/Finance role should only view their own timesheets.
- Users with both an Accounts/Finance role and the "OT Approver" role should be able to view all submitted timesheets.

## Constraints
None

## Expected changes
- Remove the `is_accounts` standalone condition block in `timesheet_permission_query.py`.

## Validation
- Log in as an Accounts user without OT Approver and verify they can only see their own timesheets.
- Log in as an Accounts user with OT Approver and verify they can see all submitted timesheets.

## Definition of done
- The `timesheet_permission_query.py` file is updated.
- Syntax is valid.
