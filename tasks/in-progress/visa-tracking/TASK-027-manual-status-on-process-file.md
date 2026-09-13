---
id: TASK-027
feature: FEAT-001
title: Operations set the tracking status from the Process File
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-010
created: 2026-09-14
updated: 2026-09-14
---

# TASK-027: Operations set the tracking status from the Process File

## Objective

Let operations change a case's tracking status on its `PF Process File`
(ADR-010 "Amendment (2026-09-14)").

## Roles (owner, 2026-09-14)

`Operations Team Lead` and `Operations Associate` (`System Manager` keeps
access).

## Required behaviour

1. `custom_client_status`: editable, `fetch_from:
   custom_visa_tracking_application.current_status`, `fetch_if_empty: 1`;
   keep `depends_on`.
2. Only the two roles may change it.
3. Active statuses only in the picker.
4. Reject an inactive or unknown status before save.
5. Log a manual change with `visible_to_client=False` and the user. No reason.
6. Allowed on dependant Process Files.
7. The next genuine workflow change still recomputes it.

## Implementation (2026-09-14)

`the_visaguy` `896930f` (with TASK-024, TASK-025). Local, not pushed.

- `fixtures/custom_fields.json`: `read_only: 0`, `fetch_from`,
  `fetch_if_empty: 1`, new description. The existing `link_filters`
  (active, allowed on Process File) already limit the picker, so no
  `set_query` was needed.
- `process_file_handlers.validate` (registered on `PF Process File`
  `validate` in `hooks.py`): when the field changed on an existing Process
  File — needs a linked application; a value equal to the application's
  current status is accepted from anyone (that is the `fetch_from` fill);
  otherwise the user must hold `PROCESS_FILE_STATUS_EDIT_ROLES`
  (`PermissionError`) and the status must be active and allowed on Process
  Files. Skipped during the recursion-guarded sync write.
- `fixtures/client_scripts.json`: the field is enabled only for a linked
  Process File **and** a user with one of the roles.
- `lifecycle_service.sync_process_file_client_status`: `changed_by =
  frappe.session.user`, `visible_to_client=False`.

### Deviation from the planned approach

The plan put the field on `permlevel: 1` with filtered Custom DocPerm rows.
Not done. Both known sites already carry Custom DocPerm rows for
`PF Process File`, so extra rows would be additive there, but on a site
without them the first Custom DocPerm row replaces the DocType's standard
permissions. The server-side `validate` check enforces the same rule on
every site, gives the user a clear message, and needs no permission
fixtures. The client script keeps the field read-only for everyone else.

## Validation

Pure tier 317 (2 known errors) and on-site **418 OK** — see TASK-024.
New pure tests (`test_process_file_status_validate.py`): each allowed role;
other roles refused; inactive, not-allowed and unknown statuses refused;
the fetched value accepted from any role; no linked application refused;
unchanged, cleared and new documents not checked; guarded sync not
checked. On-site: field metadata (`read_only` 0, `fetch_from`,
`fetch_if_empty`); a manual change appends exactly one log row with
`visible_to_client = 0` and `changed_by`; it is absent from the public
timeline; the next workflow change recomputes it.

## What remains

1. Push `the_visaguy`, deploy (fixtures sync the field and client script).
2. Check the field exists on the target site before migrate (risk 25).
3. A desk check by an Operations Associate on a real Process File.
