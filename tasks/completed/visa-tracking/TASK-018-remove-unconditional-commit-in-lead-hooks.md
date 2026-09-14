---
id: TASK-018
feature: FEAT-001
title: Investigate and remove unconditional frappe.db.commit() in visaguy_crm Lead hooks
status: completed
repository: visaguy_crm
owners: []
depends_on: []
expected_files:
  - visaguy_crm/visaguy_crm/server_scripts/lead/lead_hooks.py
created: 2026-09-02
updated: 2026-09-14
---

# TASK-018: Investigate and remove unconditional `frappe.db.commit()` in `visaguy_crm` Lead hooks

## Objective

Investigate why `visaguy_crm`'s Lead hooks call `frappe.db.commit()`
mid-transaction on every Lead save, and remove or condition that commit so a
Lead save no longer forces a partial-transaction commit point. See risk 26 in
`docs/risks-and-open-questions.md` for the full evidence.

## Context

Discovered during TASK-016's test-environment correction
(`ongoing/visa-tracking-implementation/13-session-2026-09-02-task-016.md`)
and consistent with the leaked-state test-isolation failures recorded in
`ongoing/visa-tracking-implementation/12-session-2026-09-01-task-011-012.md`
§2b. An unconditional `frappe.db.commit()` inside a Lead save hook has two
distinct consequences:

- **Production atomicity.** A later failure in the same request (the same
  Lead save, or a caller that wraps the Lead save inside a larger
  transaction) can no longer be rolled back past the commit point. Whatever
  was written before the commit is now permanent regardless of what happens
  afterward.
- **Test isolation.** `FrappeTestCase` normally rolls back at the class
  level only; a mid-test `frappe.db.commit()` defeats that, so a row a test
  creates and deletes can be permanently committed and leak into the next
  test run — the same failure mode already observed and worked around once
  in this feature's test suite.

`lead_hooks.py` is on a live CRM path (Lead creation/update is core, high-
volume workflow), so this needs care: understand *why* the commit was added
before removing it — it may be masking a real need (e.g. a downstream
`enqueue_after_commit` job that assumes committed data, or an earlier bug
this commit was a workaround for) rather than being pure oversight.

## Inputs

- `visaguy_crm/visaguy_crm/server_scripts/lead/lead_hooks.py` — locate every
  `frappe.db.commit()` call and its surrounding hook (which Lead event it
  fires on, what runs before and after it in the same request).
- Git blame / history on the file, if available, for why the commit was
  introduced.
- `visaguy_crm/visaguy_crm/hooks.py` for how `lead_hooks.py` is wired into
  Lead's document events.

## Required behaviour

- Identify every unconditional `frappe.db.commit()` in the Lead hook chain
  and what it currently protects (if anything).
- Determine whether the commit is load-bearing (something downstream
  genuinely requires committed state before it can proceed — e.g. a
  synchronous external call issued in the same hook) or removable oversight.
- If removable: remove it, and confirm Lead-save behaviour is unchanged for
  the cases that matter (existing Lead hook tests, plus this feature's own
  fixtures in `the_visaguy/the_visaguy/visa_tracking/tests/fixtures.py`,
  which build Leads through this exact path).
- If load-bearing: replace the blanket commit with the narrowest possible
  scope (e.g. commit only the specific write that must be durable before the
  next step, or move the durability-requiring step to run after the
  transaction's natural commit instead of forcing an early one).

## Constraints

- This is a live CRM path — do not change Lead-save behaviour visible to
  users (auto-assignment, notifications, field defaults) as a side effect of
  this fix. Scope the change to the commit call itself and whatever
  minimally must move with it.
- Do not touch `the_visaguy` or any other repository as part of this task.
- Do not weaken or remove the test-isolation workaround already in place in
  `the_visaguy`'s visa-tracking fixtures; this task fixes the root cause but
  should not assume every caller has been updated to rely on the fix before
  it ships.

## Validation

- `visaguy_crm`'s own test suite, full run, before/after counts.
- A targeted test (or a reasoned explanation if none is practical) proving a
  Lead save inside a larger transaction no longer commits prematurely — e.g.
  simulate a downstream failure after the Lead save and confirm the Lead
  write rolls back with it, where it previously would not have.
- Re-run `the_visaguy`'s visa-tracking suite (which now installs
  `visaguy_crm`) to confirm no regression from this change.

## Definition of done

- Root cause of the unconditional commit understood and recorded here.
- Commit either removed or narrowed to the minimum load-bearing scope, with
  reasoning recorded.
- Validation evidence recorded in this task file.
- Risk 26 in `docs/risks-and-open-questions.md` updated to reflect the fix
  once deployed (do not close it on implementation alone — deployment
  evidence is required, consistent with this workspace's standing rule).

## Completion evidence (2026-09-14)

**Scope as found.** The two Lead customer-sync hooks in `lead_hooks.py` were
already fixed (`51f608e`). Risk 26 named three more sites; all eight commits
on them were in these places:

| Module | Where | Runs inside | Git history |
|---|---|---|---|
| `form_disable_via_pf_action.py` | `disable_form_with_action` (4), `disable_additional_documents` (2) | PF Process File `validate` | initial import `7af96a9` (2025-09-04), `f719140d` (2026-01-27); no reason given |
| `file_collection_from_lead.py` | end of `generate_file_collection_lead`; workaround block in `create_ff_file_collection` after `db_set` | whitelisted action **and** Lead `before_save` via `reset_and_regenerate_on_destination_change` | `7af96a9`, `1c17d478` (2026-03-31) |
| `allocated_to_process_file.py` | `create_process_file`, after creating process files and in the form-disable loop | whitelisted POST action | `7af96a9` |

**Load-bearing?** No. Nothing on these paths enqueues a job that reads the
new rows (`update_applicant_details` enqueues deletion of the *previous*
collections only), emails use `frappe.sendmail(now=True)` inside the request,
`publish_realtime` already uses `after_commit=True`, and the whitelisted
actions are called with `frappe.call` (POST), which Frappe commits in
`sync_database` on success. The commits only split one logical change into
committed halves. `update_customer_name_from_button` keeps its commit: a
standalone button action, never called from a hook.

**Fix.** `visaguy_crm` `df74c46` removes all eight.

**Validation.**
- New `visaguy_crm/test_no_mid_request_commits.py` (4 tests): both PF validate
  hooks save the collections and never commit; an AST scan of the four
  save-path modules allows a commit only in
  `update_customer_name_from_button`. Against the old code: 4/4 fail. With the
  fix: 4/4 OK, plus `test_allocated_to_process_file` 6/6.
- `visaguy_crm.server_scripts.lead.test_lead_hooks` on-site: 3/3 OK.
- `the_visaguy` on-site suite (installs `visaguy_crm`): 425 run, OK, twice.
- The `the_visaguy` fixture workarounds for leaked state are left in place.

**Outstanding.** Deploy. Risk 26 closes on deployment evidence.
