# Task: the public tracker never shows dependants, because no PF Process File is linked to a Visa Tracking Application

> **Status (2026-09-13):** implemented by the owner on the bench —
> `the_visaguy` `b99dea7` and `d59614f`. Ownership rule: ADR-014. Record:
> TASK-022. This brief is kept as the investigation record. Passport number
> and date of birth below are redacted.

You are picking this up cold. Everything you need is below. **Re-verify the
findings before acting on them** — they were gathered on 2026-09-03 and the
site is a development site under active change.

## Environment

- Bench host: `ssh -p 2257 shahzad@erpcode.tridz.in`, bench at `/home/shahzad/bench`.
- Site: `visaguy`. **This is a development site**, not production, despite
  older workspace docs describing it as "production-like". Its data is
  feature test data.
- App: `/home/shahzad/bench/apps/the_visaguy`, branch `feat/visa-tracker`.
- Run read-only queries like this (from `/home/shahzad/bench/sites`):
  `../env/bin/python <script>` with `frappe.init(site="visaguy"); frappe.connect()`.
- Workspace (this repo) is the control plane: features in `features/`,
  tasks in `tasks/<lifecycle>/visa-tracking/`, decisions in `decisions/`,
  risks in `docs/risks-and-open-questions.md`, session notes in `ongoing/`.

## Symptom

`POST /api/method/the_visaguy.visa_tracking.api.status.get_tracking_status`
with a valid `session_token` returns `"dependants": []` for an applicant who
demonstrably has a dependant.

Reproduced against lead `CRM-LEAD-2026-00109`, whose tracking application
(reached via passport `<redacted>`, DOB `<redacted>`) is `VTA-2026-00774`.

## What is NOT wrong

The dependant data itself is correct and both ends of the relationship agree:

- `Schengen-Primary-00127-Shahzad-0804` has one `custom_dependent_details`
  row: `{applicant_name: 'Navnigha', type: 'Spouse'}`.
- `Schengen-Spouse-00472-Navnigha-0806` has
  `custom_primary_process_file = 'Schengen-Primary-00127-Shahzad-0804'`.

`lifecycle_service.get_process_file_family()` reads these correctly. Do not
"fix" it.

## Root cause

`api/status.py` (~line 126) does:

```python
process_file_name = app.get("process_file")
if process_file_name:
    ... resolve family, populate dependants ...
```

`Visa Tracking Application.process_file` is `NULL`, so the branch never runs.

That field is written in exactly one place:
`lifecycle_service.link_process_file_to_tracking()` (~line 336). **That
function is never called.** Confirm with:

```
cd /home/shahzad/bench/apps/the_visaguy
grep -rn "link_process_file_to_tracking" --include="*.py" --include="*.json" --include="*.txt" .
```

At the time of writing the only hit is its own `def`. It was implemented and
never wired to a hook, job, or API.

`PF Process File.on_update` →
`visa_tracking/handlers/process_file_handlers.py:on_update` handles only
client-status sync, and its manual-sync half begins with
`if not doc.get("custom_visa_tracking_application"): return` — a field
nothing populates.

State consistent with that (re-verify):

- 0 of 3,871 `PF Process File` rows have `custom_visa_tracking_application` set.
- All `Visa Tracking Application` rows have `process_file` NULL.
- `the_visaguy/hooks.py` (~line 229) already says in a comment that "no PF
  Process File is linked to a tracking application yet", which is why the
  TASK-016 drift sweep is deliberately not scheduled.

## The hard part: which application owns a process file?

**Do not wire the linker before resolving this.** Attaching a process file to
the wrong tracking application would show one client another client's
dependants — the same class of defect as risk 28 in
`docs/risks-and-open-questions.md`, on a live CRM path.

`_resolve_tracking_application_for_process_file()` has two routes. For this
lead **both are currently wrong**:

**Route 1 — via the lead.** `PF.custom_reference_type='Lead'`,
`custom_reference_name='CRM-LEAD-2026-00109'`, then read
`Lead.custom_visa_tracking_application`. That field holds `VTA-2026-00801`,
but the application the client actually verifies into is `VTA-2026-00774`.
Lead `00109` has **two** tracking applications because two passports were
extracted (`PEX-2026-00014` → `VTA-2026-00774`, `PEX-2026-00015` →
`VTA-2026-00801`). A single Link field cannot express one-lead-many-
applicants, and it currently names the wrong one.

**Route 2 — via file collection.** Looks like the right key, because a file
collection is per-applicant while the lead is not. But the values disagree:

| Record | file_collection |
|---|---|
| `Schengen-Primary-00127-Shahzad-0804` | `Shahzad-TVGUC-0180600805` |
| `VTA-2026-00774` | `Shahzad-TVGUC-0180600765` |
| Lead `00109` `Applicant Information` row 1 | `Shahzad-TVGUC-0180600765` |

So the process file and the lead's own applicant row disagree about which
collection belongs to Shahzad. **Explain this discrepancy before trusting
route 2.** Plausible causes to check: the process file was recreated, the
collection was regenerated per upload, or the applicant row is stale. Find
out from the data and the creation code paths — do not assume.

## What to do

1. **Re-verify** every claim above against the live site. Report anything
   that no longer holds.
2. **Explain the file-collection discrepancy.** This is the gating question.
   Trace where `file_collection` is written on `PF Process File`, on
   `Visa Tracking Application`, and on the lead's `Applicant Information`
   child rows, and determine which is authoritative.
3. **Propose the ownership rule** — given a `PF Process File`, which
   `Visa Tracking Application` owns it, when a lead has several? State it
   plainly, with the failure modes it accepts. **Stop here and get the owner's
   decision before writing code that links records.**
4. Once the rule is agreed: wire the linking path (hook, job, or explicit
   action — justify the choice), make `_resolve_tracking_application_for_process_file`
   implement the agreed rule, and ensure an ambiguous match flags for review
   rather than guessing (`_flag_review` already exists for this).
5. Add tests. `the_visaguy/visa_tracking/tests/` runs with
   `cd /home/shahzad/bench/sites && ../env/bin/python -m unittest discover -s
   /home/shahzad/bench/apps/the_visaguy/the_visaguy/visa_tracking/tests -p "test_*.py"
   -t /home/shahzad/bench/apps/the_visaguy`. Cover: one lead with two
   applications; ambiguous match flags instead of linking; a dependant's own
   lookup; a primary's `dependants` array.
6. Backfill existing rows only after the rule is agreed, and report the count
   and the intended mapping **before** writing anything.

## Constraints

- **Do not push to any remote and do not deploy.** Committing locally is fine;
  pushing and deploying are the owner's.
- **Do not add a `Co-Authored-By` trailer** or any Claude/Anthropic attribution
  to commits.
- `the_visaguy` may carry uncommitted work from a concurrent session. **Stage
  only the files you changed** — never `git add -A` or `git commit -a`.
- Do not put real passport numbers, MRZ strings, dates of birth, or client
  names into the repository. The identifiers in this prompt are dev-site test
  data and are already recorded in the workspace; do not add more.
- Do not change `get_process_file_family()` — it is correct.
- Do not re-scope into the derived client-status work (ADR-010 / TASK-016) or
  the dependant display override in `status.py`; both are working as designed.

## Known pre-existing test failures

Full `visa_tracking` discovery reports 268 tests with 2 errors, both in
`TestProcessFileHandler` (`test_calls_sync_on_status_change`,
`test_sync_failure_is_logged_not_raised`). They fail in
`_maybe_enqueue_client_status_recompute` → `is_job_enqueued` for want of
`frappe.local.site` when run without a site. They pre-date this work —
verified by re-running against pristine sources. Do not count them as
regressions, and do not fix them as part of this task.

## When done

Follow the workspace conventions: add a task file under
`tasks/` with objective, context, changes, validation and completion evidence
(commit hashes); add an ADR if the ownership rule is an architectural
decision; add or update a risk in `docs/risks-and-open-questions.md` — risks
close on **deployment** evidence, not implementation; and write a session
record under `ongoing/`.
