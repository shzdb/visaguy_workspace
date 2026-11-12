---
id: FEAT-sales-team-membership-from-invoice-company
title: Sales Team Membership from Invoice Company
status: completed
priority: medium
repositories: [visaguy_hrms]
owners: []
depends_on: []
created: 2026-11-05
updated: 2026-11-05
---

# Sales Team Membership from Invoice Company

## Summary

When an Employee is saved, keep Sales Team Employee Group membership aligned
with that employee's Invoice Company. The save only decides whether work is
needed. Group updates run in the background.

## User value

HR no longer types Sales Team members by hand. An Active sales person is
placed on every Sales Team whose team head bills through the same Invoice
Company, and is taken off those groups when the company is cleared or the
employee is no longer Active.

## Scope

### Included

- Employee `on_update` in `visaguy_hrms`.
- Queue `sync_sales_team_groups` on the short queue with
  `enqueue_after_commit=True`.
- Sales Team groups only (`custom_group_type == "Sales Team"`).
- Add when status is Active, Invoice Company and Zoho Sales Person ID are
  both set, and the group team head's Employee has the same Invoice Company.
- Add to every matching Sales Team.
- Remove from Sales Team groups that no longer match.
- Remove from Sales Team groups when Invoice Company is cleared.
- Remove from Sales Team groups when status is no longer Active
  (Inactive, Suspended, or Left).
- Do not add an employee to the Sales Team group they head.

### Excluded

- Junior Senior Employee Groups.
- Membership changes when Invoice Company stays set and only Zoho Sales
  Person ID is cleared.
- Adding an employee who is not Active.
- A new DocType or a change to Employee Group custom fields.

## Requirements

- Run the check when `custom_invoice_company`, `custom_zoho_sales_person_id`,
  or `status` changes.
- Do not make the Employee save wait on Employee Group writes.
- Leave the group an employee heads unchanged.
- Leave Junior Senior child rows unchanged.

## Proposed design

See Completion Notes for the implemented behaviour.

## Tasks

- [x] TASK-implement-sales-team-membership-from-invoice-company

## Acceptance criteria

- [x] Active employee with both fields set is added to every Sales Team whose
      team head has the same Invoice Company.
- [x] Changing Invoice Company moves the employee off the old groups and onto
      the new ones.
- [x] Clearing Invoice Company removes the employee from Sales Team groups.
- [x] Clearing only Zoho Sales Person ID leaves membership unchanged.
- [x] A non-Active employee is not added. Becoming non-Active removes them
      from Sales Team groups.
- [x] An employee is not added to the Sales Team they head.
- [x] Junior Senior groups are not changed.
- [x] The Employee save enqueues the sync after commit.

## Dependencies

- Employee `custom_invoice_company` and `custom_zoho_sales_person_id`
  (`visaguy_crm` customizations).
- Employee Group `custom_team_head` (User) and `custom_group_type`
  (`Sales Team` / `Junior Senior`).
- Team head Invoice Company is read from the Employee whose `user_id` is
  `custom_team_head`.

## Risks

- The queued job runs only while a worker is up. Until the SSH bench web and
  worker processes load this code, saves still follow the previous behaviour.
- A team head with no Employee, or no Invoice Company, does not match, so
  members are removed from that Sales Team when a sync runs.
- Changes are uncommitted on `fasil-bench2`.

## Open questions

None — confirmed by the requester ("all good").

## Completion notes

Implemented on the SSH bench `fasil-bench2` (`ssh -p 2203 fasil@code.tridz.in`),
site `visaguy`, app `visaguy_hrms`. Not written to the local bench. Git changes
left unstaged. Not committed.

**`visaguy_hrms/custom_scripts/employee_hooks.py`**

| Function | Role |
|---|---|
| `sync_sales_team_membership(doc, method)` | Employee `on_update`. Returns unless Invoice Company, Zoho Sales Person ID, or status changed. Enqueues when the employee is not Active, when Invoice Company was cleared, or when both Invoice Company and Zoho Sales Person ID are set. |
| `sync_sales_team_groups(employee)` | Background worker. Reloads the Employee. Non-Active status removes them from Sales Team groups and does not add. Active with an empty Zoho Sales Person ID and a set Invoice Company returns without changes. Otherwise adds to matching Sales Teams and removes from the rest. |
| `_add_sales_team_member` | Appends `employee`, `employee_name`, and `user_id`. Returns immediately when status is not Active or the row already exists. |
| `_remove_sales_team_member` | Removes that employee from one group's child table. |

Group saves use `ignore_permissions=True`. The group the employee heads is
skipped, so a team head is neither added there nor removed from it.

**`visaguy_hrms/hooks.py`** — Employee `on_update` points at
`sync_sales_team_membership`. The existing `validate` handler for pending
leave applications is unchanged.

**Evidence**

- **source-wired** on `fasil-bench2`: `py_compile` passed; hook string is
  registered.
- Rolled-back site script on site `visaguy` checked add, move, several
  matching groups, own-group skip, empty Invoice Company removal, Zoho-only
  clear leaving membership, Inactive and Left removal, and Junior Senior
  left untouched. Transaction rolled back; no test users left behind.
- Requester confirmed behaviour. A live Desk save after bench restart was
  not separately runtime-verified.
