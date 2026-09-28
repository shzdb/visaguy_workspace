# 01d2 — TASK-034 corrective: System Manager access to Visa Tracker Settings

- Repository: `the_visaguy`
- Branch: `sl/task-034` (local worktree `wt/task-034/the_visaguy`, pushed to the bench repo)
- Previous head: `924480e` (see `01d-task-034.md`)
- Head: `1d070d0`
- Bench worktree: `/home/shahzad/sl-worktrees/task-034-the_visaguy`
- Verdict: done

## Summary

- G1: `the_visaguy/fixtures/custom_docperm.json` has one new row,
  `System Manager-Visa Tracker Settings`. The file now has 65 rows (it had 64).
  The flags are the same as the standard `System Manager` row in
  `visa_tracker_settings.json`: `read`, `write`, `create`, `delete`, `email`,
  `export`, `print`, `report` and `share` are 1. All other flags are 0.
  Permlevel is 0.
- Before this change, the fixture had only the `Visa Tracker Manager` and
  `Visa Tracker Operator` rows for Settings. These rows replace the standard
  permissions, so a non-Administrator `System Manager` could not open Settings.
  Now the fixture has the full union of the standard Settings rows. The
  Manager and Operator rows were already identical to the standard rows, and
  the new test checks this.
- No other role gets access to Settings.
- G2: two new static tests check the Settings union and the Settings role set.
- The orchestrator decisions on the other open questions are applied with no
  change: `Visa Tracker Operator` keeps `write` on `Visa Tracking Application`,
  and `Desk User` stays in the read-role list.

## Commits

| SHA | Message |
|---|---|
| `924480e` | `feat(TASK-034): grant tracking read, operations create and extraction review permissions` (earlier run) |
| `1d070d0` | `fix(TASK-034): keep System Manager access to Visa Tracker Settings` |

## Files changed

- `the_visaguy/fixtures/custom_docperm.json`: 26 insertions, 0 deletions. The
  new row is appended at the end. No existing row is changed.
- `the_visaguy/visa_tracking/tests/test_custom_docperm_fixture.py`: 2 new tests.

## Design notes and deviations

- Record format: the same as the other rows in the file (all 15 flags written
  out, the same key order, `docstatus 0`, `parentfield "permissions"`,
  `parenttype "DocType"`). The name follows the `<Role>-<Parent>` scheme.
  `modified` is `2026-09-28 12:00:00.000000`, the same as the other TASK-034 rows.
- Serialization: the script first confirmed that `json.dumps(indent=1)`
  reproduces the file byte for byte, then appended the row and wrote the file
  with the same settings. The 1-space indent and the missing trailing newline
  are kept.
- `import` is 0 because the standard Settings row does not set it. This is a
  copy of the standard row, not a new grant.
- No deviations from the orchestrator decision.

## Tests added

In `TestCustomDocPermFixture`:

- `test_settings_keep_standard_permissions`: every standard row of
  `visa_tracker_settings.json` has a fixture row with identical flags. The test
  also checks that the standard rows contain `System Manager`, so that the test
  fails if the DocType JSON loses that row.
- `test_settings_roles_are_limited_to_tracker_roles`: the Settings roles in the
  fixture are exactly `System Manager`, `Visa Tracker Manager` and
  `Visa Tracker Operator`.

The existing `test_read_roles_cannot_open_settings` is unchanged and still passes.

### Gates

- JSON is valid (65 rows).
- No duplicate `(parent, role, permlevel)` keys, and no duplicate names.

### Pure-tier result (bench worktree, `1d070d0`, under the flock wrapper)

```
Ran 343 tests in 0.839s
FAILED (errors=2, skipped=20)
```

- Previous run (`924480e`): Ran 341, FAILED (errors=2, skipped=20). The new count is 341 + 2 new tests.
- Baseline (`12ded1a`): Ran 324, FAILED (errors=2, skipped=20).
- The only errors are the 2 known cases in
  `test_lifecycle_service.TestProcessFileHandler`
  (`test_calls_sync_on_status_change`, `test_sync_failure_is_logged_not_raised`,
  `AttributeError: site`). There are no new errors or failures, and the skipped
  count is unchanged.
- The fixture test module alone on the bench: `Ran 19 tests`, `OK`.

## On-site checks still to run

All the checks in `01d-task-034.md` still apply. Use SHA `1d070d0` in step 7
of that list. Add these Settings checks. Run them on
`visa-tracker-test.localhost` after migrate in the integration phase:

1. Confirm that the row `System Manager-Visa Tracker Settings` exists in
   `Custom DocPerm` and has the flags above.
2. Log in as a test user who has `System Manager` and is not `Administrator`.
   Open `/app/visa-tracker-settings`, change a field and save. Both must work.
   `frappe.has_permission("Visa Tracker Settings", "write")` must return True.
3. A `Visa Tracker Manager` user can still read and write Settings. A
   `Visa Tracker Operator` user can still read Settings and cannot write it.
4. A user who has only a read role (for example `Lead Role`, which also
   gets `Desk User` automatically) gets a permission error on
   `/app/visa-tracker-settings`.
5. Before migrate, list the Custom DocPerm rows for `Visa Tracker Settings` on
   both sites. A row with a hash name from Role Permission Manager stays after
   migrate. If such a row gives Settings access to a role other than the three
   tracker roles, decide what to do with it.

## Needs from another task

No new needs. The notes for TASK-031, TASK-032 and TASK-033 in
`01d-task-034.md` still apply.

## Open questions

The orchestrator closed open questions 1, 2 and 3 of `01d-task-034.md`.
Question 4 is still open: should the read roles also get `report` or `print`
on the tracking DocTypes? Only `read` is granted.
