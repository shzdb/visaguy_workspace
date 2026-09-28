# 01e2 — TASK-032 corrective: PF Process File field_order (executor log)

## Summary

- F1: I read the Frappe v15 source on the bench (read-only). The rule is
  confirmed: a `field_order` Property Setter decides the order of the
  fields it lists, and `insert_after` places only the fields that are not
  in the list. But the premise needs one correction. None of the shipped
  PF Process File `field_order` lists contains any of the seven Visa
  Tracking fields. So today, `insert_after` still places them, and the new
  section comes directly after `custom_form_submitted` and before
  `custom_section_break_mw0ux`. The chain resolves correctly. This matches
  what my first log (01e) said.
- F2: I added the after_migrate hook anyway. It is a guard. It keeps the
  order correct if the list later contains these fields (for example after
  a Customize Form save), or if an upstream list changes.
- F3: 9 new pure tests.
- F4: The on-site checks are listed below.
- Pure tier on the bench at `ffcacb3`: `Ran 356 tests`,
  `FAILED (errors=2, skipped=20)`. This is 347 + 9. The only errors are
  the 2 known `TestProcessFileHandler` "AttributeError: site" cases.

## Commits

| sha | message |
|---|---|
| `f800d3f` | feat(TASK-032): desk layout and navigation for visa tracking (earlier) |
| `ffcacb3` | feat(TASK-032): keep visa tracking fields in PF Process File field_order after migrate |

I pushed `sl/task-032` to `bench`. The bench worktree is
`/home/shahzad/sl-worktrees/task-032-the_visaguy`, detached at `ffcacb3`.

## Files changed (this corrective)

- `the_visaguy/hooks.py`: a new `after_migrate` list with one entry,
  `the_visaguy.visa_tracking.desk_layout.apply_pf_process_file_field_order`.
  No `after_migrate` existed before. I did not change the `fixtures` list.
- `the_visaguy/visa_tracking/desk_layout.py` (new).
- `the_visaguy/visa_tracking/tests/test_desk_layout_field_order.py` (new).

I did not change any fixture JSON, and I did not touch any file of
visaguy_hrms or visaguy_crm.

## F1 — source evidence (Frappe on bench: `v15.8.1-4505-g01ea89c4e6`, commit `01ea89c4e6`)

### `frappe/model/meta.py`

- `Meta.process` (line 138) calls these in order: `add_custom_fields`
  (145), `apply_property_setters` (146, where the `field_order` Property
  Setter becomes `meta.field_order`), `init_field_caches` (147) and
  `sort_fields` (148).
- `Meta.sort_fields` (line 467). The docstring gives the priority as:
  `field_order` property setter > computed `insert_after` for standard
  fields > `insert_after` for custom fields.
  - Line 475: `if field_order := getattr(self, "field_order", [])`.
  - Line 476: drops names that are not in `self._fields`.
  - Line 479: if every field is listed, the list is used as is (return).
  - Line 505: `existing_fields = set(field_order)`.
  - Line 509: fields in `existing_fields` are skipped. Listed fields keep
    their list position, and their `insert_after` is ignored.
  - Line 519/520: an unlisted custom field goes into
    `insert_after_map[insert_after]`.
  - Line 527: `_update_field_order_based_on_insert_after(field_order, insert_after_map)`.
  - Line 531: `_update_fields_based_on_order` sets `idx` and `self.fields`.
- `_update_field_order_based_on_insert_after` (line 895):
  - Line 904: it skips anchors that are not in the list yet, and retries
    until nothing changes, so chains resolve.
  - Lines 907–910: it inserts mapped fields *directly after* the anchor's
    index, in front of whatever the list had after the anchor.
  - Line 917: fields whose anchor never resolves go to the end.

Consequence for PF Process File: `custom_visa_tracking_section` (insert
after `custom_form_submitted`, not listed) goes directly after
`custom_form_submitted` and in front of `custom_section_break_mw0ux`
(listed). The other six fields chain after the section. Without any
`field_order`, both the new section and `custom_section_break_mw0ux` map to
`custom_form_submitted`, and their relative order depends on field
iteration order (Custom Field idx). This is the ambiguity. It only exists
on sites without a `field_order`.

### `frappe/migrate.py` (order of fixture sync and after_migrate)

- `SiteMigration.post_schema_updates` (line 129) runs, in this order:
  - `sync_jobs()` (142);
  - `sync_fixtures()` (143);
  - `sync_dashboards()` (144);
  - `sync_customizations()` (145);
  - `sync_languages()` (146);
  - then the `after_migrate` hooks for each installed app (lines 153–157:
    `for fn in frappe.get_hooks("after_migrate", app_name=app): frappe.get_attr(fn)()`).
- So the hook runs after all fixture and customization re-imports, on
  every migrate. `SiteMigration.run` (174) wraps the phases. The phase
  methods are decorated with `@atomic` (for example, line 110), so the hook
  does not need its own commit.
- `frappe/utils/fixtures.py`:
  - `sync_fixtures` (line 12) calls `import_fixtures(app)` for each
    installed app, in `apps.txt` order.
  - `import_fixtures` (line 28) imports the files sorted by name (line 33).
- `frappe/modules/utils.py`:
  - `sync_customizations` (line 103) imports `<module>/custom/*.json`
    that have `sync_on_migrate`.
  - For Property Setters (lines 175–182), it runs `doc.insert()`, and
    Property Setter replaces any existing record with the same property.

### Where the live value comes from (a correction to the orchestrator's fact)

There are three shipped copies of `PF Process File-main-field_order`:

| Source | Names | Modified |
|---|---|---|
| `visaguy_hrms/visaguy_hrms/fixtures/property_setter.json` | 37 | 2026-02-12 |
| `visaguy_crm/visaguy_crm/fixtures/property_setter.json` | 12 | 2024-09-20 |
| `visaguy_crm/visaguy_crm/visaguy_crm/custom/pf_process_file.json` (`sync_on_migrate: 1`) | **45** | 2026-08-14 |

`sync_customizations` runs after `sync_fixtures`, so the site ends up with
the **45-name visaguy_crm customization**. This matches the orchestrator's
"45 names starting workflow_state, applicant_name, process_". The value
does not come from visaguy_hrms. In the 45-name list,
`custom_section_break_mw0ux` directly follows `custom_form_submitted`. In
the hrms 37-name list, `custom_section_break_izply` follows it instead.
None of the three lists contains any of the seven tracking fields.

## F2 — design notes

- `apply_pf_process_file_field_order()`:
  - It runs `frappe.db.get_value("Property Setter", {"doc_type": "PF Process File", "property": "field_order"}, ["name", "value"], as_dict=True)`.
  - If there is no record, it returns.
  - It parses the value. If the value is not a JSON list, or the anchor
    `custom_form_submitted` is missing, it logs
    `frappe.logger().warning(...)` and returns. The warning has no
    document data.
  - It calls `place_tracking_fields(list)`. This removes the seven fields
    wherever they are, and re-inserts them in the contract order directly
    after `custom_form_submitted`.
  - If the result equals the current list, it returns (idempotent, no
    write, no cache clear).
  - Otherwise it runs `frappe.db.set_value("Property Setter", name, "value", json.dumps(new_order), update_modified=False)`
    and then `frappe.clear_cache(doctype="PF Process File")`.
- **Deviation (small):** `update_modified=False`. The brief says "no other
  field changes", so the hook does not bump `modified` either.
- The seven names are always inserted, even when a Custom Field does not
  exist on the site yet. This is harmless, because `sort_fields` line 476
  drops unknown names.
- The `insert_after` values in `custom_fields.json` are unchanged, as the
  fallback for sites without a `field_order`.
- I checked the helper against the real 45-name visaguy_crm list with the
  bench python, read-only and with no site. The result has 52 names:
  `... custom_form_saved, custom_form_submitted, custom_visa_tracking_section, custom_visa_tracking_application, custom_client_status, custom_tracking_empty_note, custom_tracking_column_break, custom_tracking_updated_on, custom_tracking_enabled, custom_section_break_mw0ux, custom_generate_application_form ...`.
  A second pass gives the same list.
- Side effect: after the first migrate, the site's `field_order` Property
  Setter lists the seven fields. If someone later runs "Export
  Customizations" for PF Process File from visaguy_crm, that export will
  include them. That is correct content, but it is a cross-app change.
  Every migrate first re-imports the visaguy_crm list and then the hook
  runs again, so the order stays stable.
- Hook order across apps: `the_visaguy` comes after `visaguy_hrms` and
  `visaguy_crm` in `apps.txt`. Neither of them has an `after_migrate` that
  writes this Property Setter. Only fixture and customization sync write
  it, and both run before any hook.

## Tests added and pure-tier result

File: `the_visaguy/visa_tracking/tests/test_desk_layout_field_order.py`.
It patches frappe and uses synthetic lists.

- `TestPlaceTrackingFields`:
  - `test_moves_tracking_fields_after_anchor`
  - `test_does_not_change_the_input_list`
  - `test_returns_none_without_anchor`
- `TestApplyFieldOrder`:
  - `test_writes_expected_order_and_clears_cache` (checks the exact
    `set_value` call, `update_modified=False` and `clear_cache(doctype=...)`)
  - `test_second_run_is_idempotent` (one write, one cache clear over two
    runs)
  - `test_no_op_without_property_setter`
  - `test_no_op_and_warning_without_anchor`
  - `test_no_op_and_warning_for_invalid_value`
- `TestAfterMigrateHookRegistration`:
  - `test_hook_is_registered`

The synthetic input puts `custom_client_status` and
`custom_tracking_enabled` at wrong positions, to prove that they are
removed and re-inserted.

Gates:

- `py_compile` passes on `desk_layout.py`, the test file and `hooks.py`.
- Pure tier (bench worktree `task-032-the_visaguy` at `ffcacb3`, under the
  flock and timeout wrapper):

```
Ran 356 tests in 1.086s
FAILED (errors=2, skipped=20)
ERROR: test_calls_sync_on_status_change (test_lifecycle_service.TestProcessFileHandler)
ERROR: test_sync_failure_is_logged_not_raised (test_lifecycle_service.TestProcessFileHandler)
```

These are the baseline errors. There are no new errors or failures.

## On-site checks still to run (integration phase, `visa-tracker-test.localhost`)

These map to TASK-032 Validation 1 (meta after migrate) and replace
checks 1–2 in 01e.

1. Before migrate, record the current value:
   `frappe.db.get_value("Property Setter", {"doc_type": "PF Process File", "property": "field_order"}, ["name", "value", "modified"])`.
2. Run `bench --site visa-tracker-test.localhost migrate`. The output shows
   "Executing `after_migrate` hooks..." and no traceback from
   `the_visaguy.visa_tracking.desk_layout`.
3. After migrate:
   - Run `v = json.loads(frappe.db.get_value("Property Setter", "PF Process File-main-field_order", "value"))`.
   - Check that `v[v.index("custom_form_submitted"):][:9]` equals
     `["custom_form_submitted", "custom_visa_tracking_section", "custom_visa_tracking_application", "custom_client_status", "custom_tracking_empty_note", "custom_tracking_column_break", "custom_tracking_updated_on", "custom_tracking_enabled", "custom_section_break_mw0ux"]`.
   - Check that each of the seven names appears exactly once.
   - Check that `modified` is unchanged from step 1. This proves
     `update_modified=False`. The visaguy_crm re-insert may itself change
     `modified`, so compare with a second migrate if needed.
4. Run `frappe.clear_cache(doctype="PF Process File"); f = [d.fieldname for d in frappe.get_meta("PF Process File").fields]`.
   The same 9-name slice must appear, in that order, starting at
   `f.index("custom_form_submitted")`.
5. Run migrate a second time. The Property Setter value must be the same
   string as after step 3. The meta order must be the same as in step 4.
6. In Customize Form for PF Process File, drag `custom_client_status`
   elsewhere, save, and run migrate. The order returns to the step 4 slice.
   Revert the Customize Form change afterwards, or skip this step if
   Customize Form use on the test site is not allowed.
7. Desk check (Validation 2): open a PF Process File. The "Visa Tracking"
   section sits directly under the "Form Submitted" field, and before the
   Application Form section (`custom_section_break_mw0ux`).
8. The fallback cannot be checked on this site (it has a `field_order`).
   Note it as not verified on-site. The pure test
   `test_section_follows_form_submitted_and_precedes_application_form` in
   `test_desk_layout_fixtures.py` covers the `field_order` case only.

## Needs from another task

- None for this corrective. The 01e items (TASK-031 fetched-field refresh,
  TASK-034 read permissions, TASK-035 workspace shortcut) still apply.
- Merge note: `hooks.py` now has a new top-level `after_migrate` block
  under the Installation comments. TASK-031 edits `doc_events` in
  `hooks.py`, and the two blocks are far apart. If another task also adds
  `after_migrate`, merge the two lists.

## Open questions

1. Should the visaguy_crm `custom/pf_process_file.json` owner add the seven
   fields to their shipped `field_order`? Then the hook becomes a no-op. It
   would stay as a guard.
2. On sites without any `field_order` (none known today), the relative
   order of the new section and `custom_section_break_mw0ux` is still
   decided by Custom Field idx. Is that acceptable, or should the hook also
   create a `field_order` in that case? I did not do this, because the
   brief says "do nothing if absent".
