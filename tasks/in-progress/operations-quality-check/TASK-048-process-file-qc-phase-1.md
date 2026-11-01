---
id: TASK-048
feature: FEAT-006
title: Process file quality check, Phase 1 (Check QC button with a huf agent)
status: in-progress
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-017
expected_files:
  - the_visaguy/quality_check/huf_adapter.py
  - the_visaguy/quality_check/context.py
  - the_visaguy/quality_check/prompt.py
  - the_visaguy/quality_check/runner.py
  - the_visaguy/quality_check/api.py
  - the_visaguy/quality_check/doctype/visaguy_ai_settings/
  - the_visaguy/quality_check/tests/
  - the_visaguy/quality_check/custom/
  - the_visaguy/patches/v1_0/grant_huf_user_role.py
  - the_visaguy/public/js/pf_process_file_qc.js
  - the_visaguy/hooks.py
  - the_visaguy/modules.txt
created: 2026-10-23
updated: 2026-10-23
---

# TASK-048: Process file quality check, Phase 1

## Objective

Owner (2026-10-23): implement FEAT-006 Phase 1 on a new branch, without
committing. A **Check QC** button on PF Process File runs a huf agent in the
background on the file's data and documents, and saves the report on the
process file. Design: FEAT-006 "Phase 1 — simple QC run"; decision: ADR-017
(accepted).

## Context

- FEAT-006 decisions D1–D19 (button, no workflow change, all available
  documents including sidebar and the lead file collection, prompt template
  per destination, scope choice on a primary, Visaguy AI Settings, huf pinned
  to `v1.0.0-beta.4`).
- huf facts found while building (recorded in ADR-017): `run_agent_sync`
  queues unless `now=1`; it sends only images to the model; Persist
  Conversation reuses one conversation for every call.

## Required behaviour

As FEAT-006 Phase 1 requirements 1–10. Summary:

- **Check QC** / **Recheck QC** shows for Operations Associate, Operations
  Team Lead and System Manager when huf is installed, the site is migrated,
  Visaguy AI Settings has a QC agent, and the file's destination has a QC
  prompt template.
- On a primary with dependants, a dialog offers "This file only" or
  "Primary and all N dependants". A dependant runs alone.
- The click sets **Processing** on every included file and enqueues one job
  (`long` queue). A second click while Processing is refused; after the
  configured minutes (default 30) a stuck check can be started again.
- The job collects the documents, reads non-image documents with huf OCR,
  calls the agent with the destination's template and a JSON schema, and
  writes the result on every included file. A failure sets **Failed** with a
  short message and keeps the previous report.
- The Quality Check tab shows status, result, issue count, who and when,
  scope, check count, the report, and the list of documents checked and
  skipped. Open forms refresh in real time.

## Constraints

- No workflow change; no process file save (QC writes use
  `frappe.db.set_value`: no hooks, but `modified` changes).
- huf imported only inside functions (`huf_adapter`); unsupported huf version
  stops the check with a clear error.
- No application data, keys or secrets in the workspace.
- Do not commit (owner instruction). Test only on
  `visa-tracker-test.localhost`.

## Expected changes

New module **Quality Check** in `the_visaguy`:

| File | Purpose |
|---|---|
| `quality_check/huf_adapter.py` | Version check (`SUPPORTED_HUF_VERSIONS`), agent validation (exists, enabled, Persist Conversation off), prompt template resolution (latest active in `prompt_group`), `extract_document` OCR, `run_agent_sync(now=1)`, Agent Run reference link |
| `quality_check/context.py` | Group expansion (primary + `custom_dependent_details`), form data from both collections, document sources (form uploads of both collections, application form, RPA Documents, action `custom_attach`, sidebar `File`s), content-hash de-duplication, disk check, count and size limits, keys D1…Dn |
| `quality_check/prompt.py` | Shared rules, the message (applicants, form data, document list, document text cut at 30,000 characters), `RESPONSE_FORMAT` JSON schema, answer parsing |
| `quality_check/runner.py` | Availability, `get_state`, `start_check`, background `run_check`, saving success and failure, realtime event `process_file_qc_update` |
| `quality_check/api.py` | Whitelisted `get_state`, `start_check` (POST) |
| `quality_check/doctype/visaguy_ai_settings/` | Single DocType: QC agent, include sidebar (default on), max documents (60), max total MB (100), restart after minutes (30); System Manager only |
| `quality_check/custom/pf_process_file.json`, `destination.json` | 20 PF Process File fields (tab "Quality Check" after `custom_timer_events`) and 2 Destination fields (tab "AI" after `custom_invoice_items`, `custom_qc_prompt_template` Link Agent Prompt), in Export Customizations format |
| `public/js/pf_process_file_qc.js` | Button, scope dialog, tab rendering (report Markdown is HTML-escaped first), realtime refresh and alert |
| `hooks.py`, `modules.txt` | `doctype_js` list for PF Process File; module registered |

PF Process File fields: `custom_qc_tab`, `custom_qc_html`,
`custom_qc_details_section`, `custom_qc_status`, `custom_qc_result`,
`custom_qc_issue_count`, `custom_qc_scope`, `custom_qc_run_from`,
`custom_qc_column_break`, `custom_qc_checked_on`, `custom_qc_checked_by`,
`custom_qc_check_count`, `custom_qc_started_on`, `custom_qc_column_break_2`,
`custom_qc_prompt_template`, `custom_qc_prompt_version`,
`custom_qc_agent_run`, `custom_qc_error`, `custom_qc_output` (hidden),
`custom_qc_files` (hidden). All read-only and no-copy.

Deviations from the FEAT-006 plan:

- Non-image documents are read in VisaGuy with huf's `extract_document`,
  because `run_agent_sync` sends only images (ADR-017).
- Added fields `custom_qc_run_from` (file the group check started from) and
  `custom_qc_prompt_version` (template name and version used), and the
  setting `qc_stuck_after_minutes`.
- `get_state` returns "not set up (migrate needed)" when the settings DocType
  is missing, because the dev bench checkout is shared with the unmigrated
  `visaguy` site.

## Implementation (2026-10-23)

- Branch `feat/process-file-qc` in the installed checkout
  `/home/shahzad/bench/apps/the_visaguy`, created from `upstream/main`
  `02fee42`, upstream unset. **Not committed** (owner instruction).
- huf `v1.0.0-beta.4` installed on `visa-tracker-test.localhost` (owner
  approved). It was not on that site before; `helpdesk` is not installed
  there, so there was nothing to uninstall first.

## Validation

- Pure tests: `quality_check/tests` — 35 tests (group and scope, sources,
  form rows, de-duplication, missing files, limits, prompt content, answer
  parsing, availability and roles, start and lock, success, agent failure,
  invalid answer, unexpected error, unreadable document). Run with
  `cd ~/bench/sites && ../env/bin/python -m unittest
  the_visaguy.quality_check.tests.test_context
  the_visaguy.quality_check.tests.test_prompt
  the_visaguy.quality_check.tests.test_runner` — OK.
- Full app suite on the test site:
  `bench --site visa-tracker-test.localhost run-tests --app the_visaguy
  --skip-test-records` — **839 tests OK**. (A first run failed 4
  `test_desk_layout_fixtures` checks because the QC fields were in
  `custom_fields.json`; moved to their own fixture file.)
- Test site migrate: Visaguy AI Settings (module Quality Check), 20 PF fields
  and 2 Destination fields present.
- On-site flow, `visa-tracker-test.localhost`, inside a transaction rolled
  back afterwards (created files removed from disk). Real: huf version check,
  agent validation, prompt template resolution, document collection, saving.
  Stubbed: `extract_text` and `run_agent` only. Results:
  - group check on a primary with one dependant marked both Processing; a
    second start was refused;
  - 6 documents sent (form uploads of both collections, application form,
    RPA hotel, sidebar text, dependant's sidebar image); the sidebar copy of
    the application form was dropped as a duplicate; a lead upload missing on
    disk was listed as skipped;
  - 3 images sent as files, 3 documents read as text;
  - both files got Completed / Issues Found / check count 1 / scope Group /
    run from the primary / template and version / Agent Run link;
  - a failing recheck on the dependant set only it to Failed with the error
    and kept its previous report;
  - a file whose destination has no template reports it and shows no button.
- `node --check` on the desk script: OK.

## Change (2026-10-23): report styling

Owner asked for subtle colours in the report. The model still returns
Markdown; `pf_process_file_qc.js` escapes it, renders it, then colours it:

- issue lines starting with **[Error]** (light red), **[Warning]** (light
  amber) and **[Clarify]** (light blue), as the Schengen prompt template
  writes them;
- items under "Missing documents" (light blue) and "Checked without issues"
  (light green);
- a banner with the result, the summary line and chips counting errors,
  warnings and items to clarify (green for Passed, grey for Could Not
  Check).

Rejected: asking the model for HTML. Model output can carry text from the
documents, so rendering it as HTML would allow markup injection into the
desk. Checked with `node --check` and in a local preview page with sample
reports (a `<script>` tag in the report stays plain text). Not yet seen in the
desk.

## Change (2026-10-23): first real run reviewed, report restructured

First real run on `visaguy`, case A (`Schengen-Primary-00127-ALEXEY
ANTIPOV-234244`, Agent Run `46u83a8rig`, gpt-5.4-mini, 37,381 input tokens,
USD 0.024 for the run, OCR calls billed separately): 9 "issues", most of them
noise. Evidence from the stored prompt:

- 5 images went to the model as images; 7 PDFs were read by huf's vision OCR
  (2.6k–5.8k characters each, with a chatty first line).
- The application form text (16k characters) held only the printed
  questions: its 35 filled answers are PDF **form fields**, which OCR does not
  read. Most findings were "form values not visible", raised as errors.
- Findings that concluded "no problem", self-corrections in the text, a Group
  section for one applicant, and labels without file names.

Changes on the branch:

- `pdf_fields.py`: filled PDF form-field values are added to each PDF's text
  (case A application form: 35 values).
- Structured answer: `findings` (severity, applicant, topic, documents,
  expected, found, fix), `missing_documents`, `checks_passed`,
  `unreadable_documents`, `summary`, `result`. Stored as JSON (format 2) in
  `custom_qc_output` with a document key → label map; issue count = number of
  findings. The tab draws cards per applicant, errors first, passed checks
  folded. Older Markdown reports still render.
- Strict shared rules: real problems only, no reasoning, "cannot read" is never
  an error, Group only for several applicants, short fields.
- The shared rules are a setting: **Visaguy AI Settings → Shared QC Rules**
  (`qc_shared_rules`, Code). Empty uses the built-in text, which the form
  shows on first open. The JSON format stays in code (the tab depends on it).
- Labels: applicant "Name (Type)"; documents "Label (file name)".

Validation: 44 QC tests (including `test_pdf_fields.py`) and the app suite on
the test site, **846 tests OK**; test site migrated; card layout checked in a
local preview. Not yet re-run with the model.

## Change (2026-10-23): QC writes update "last updated"

Owner: a QC status change must update the document's last-updated time, or
people miss checked files in lists. QC writes no longer pass
`update_modified=False`: start, success and failure set `modified` and
`modified_by` (the user who ran the check). Still no save hooks and no Version
row (checked on the test site). Because `modified` changes, the tab reloads an
open form only when it has no unsaved edits (otherwise it shows a message),
and **Check QC** asks the user to save first. Trade-off: someone editing the
same file in another tab while a check finishes has to reload before saving.
Tests assert no `update_modified` override; app suite OK.

## Change (2026-10-23): second real run reviewed, rules tightened

Recheck of case A (Agent Run `qmavnq1eun`, gpt-5.4-mini, 20,047 input tokens,
one call, USD 0.020; job 18:36:13 → 18:37:17). Structured output worked and
the form-field values were read (the model quotes the form's hotel address).
5 images reached the model in both runs (about 5,500 tokens per call).
Remaining noise: format-only differences reported (03/07/1975 vs 03.07.1975),
unlike values compared (visa sticker vs passport number, appointment date vs
travel dates), applicable-only rules ignored (parental NOC for an adult),
a passport listed as missing although D4 is the passport, and an unchecked
item under checks passed. Built-in shared rules extended for each pattern.
Worth a manual look: form passport number …5780 vs passport …6780.

Operational notes from this run:

- The first recheck waited in the `long` queue behind 62 short-queue jobs on
  the bench's single worker (stale visa-tracking recompute jobs from test-site
  suite runs). An extra `bench worker --queue long` was started on the dev
  bench (not in the Procfile).
- The job then failed: `visaguy` had not been migrated for the new
  `qc_shared_rules` field. Fixed with `config.get(...)` and a test.

## Change (2026-10-23): report layout

Owner chose a Frappe-like table layout with light colour:

- Header: result pill, coloured-dot counts (errors, warnings, to clarify), a
  **Copy** button (plain text for WhatsApp / email), and one meta line
  (checked when and by whom, scope, document count, model, check number).
- One table per applicant (errors first; "Whole group" first), columns
  Severity, Issue (with the fix below), Expected, Found, Documents. Rows have a
  light red, amber or blue background; fixed column widths line the tables up.
- Document keys open the actual file in a new tab; applicant headers link to
  their process file.
- "Documents sent to the check (N)" lists every document by key and name,
  linked to its file and grouped by applicant, with skipped files below.
  Reports saved before format 3 have no links: a recheck adds them.
  (Case B's group report of 19:03 was saved one minute before format 3
  reached the bench, so it shows the old text list.)
- Upload labels drop the group name when the file name already starts with
  it, and cut group names over 40 characters (`context.short`).
- Missing documents and (folded) checks passed side by side at the bottom.
- Report JSON format 3 adds each document's file URL, the applicant →
  process file map and the model name (`runner.report_json`, `run_model`).

Checked in a local preview with Bootstrap 4.6 and in `node --check`; QC unit
tests OK. Not yet seen in the desk.

## Change (2026-11-02): pre-live review, commit and PRs

- **Blocker found:** all real runs had been as Administrator. huf needs Agent
  Run create permission and agent access for the session user, so an
  operations user failed with "You do not have access to run this agent"
  (reproduced on the test site). Owner chose roles over a service user: patch
  gives Huf User to all enabled desk users, and the agent's Allowed Roles are
  `Operations Associate` and `Operations Team Lead` (ADR-017). Access is also
  checked at the click, so no OCR is spent on a refused user.
- `tests/test_operations_users.py` runs a full check as both roles with real
  roles, agent access and permissions; OCR and the model call are stubbed.
  A user without Huf User, or outside operations, is stopped at the click.
- Custom fields moved from `fixtures/` to `quality_check/custom/` (owner).
  Sync proven on the test site: a removed field returned after migrate.
- App suite on the test site: **854 tests OK** (`--app`; `--module` fails in
  an HRMS setup step that needs a fiscal year the test site lacks).
- Commits `866d603`, `a9eedb1`, branch `feat/process-file-qc`, pushed.
  PRs: https://github.com/tvgglobal/the_visaguy/pull/51 (`main`, mergeable),
  https://github.com/tvgglobal/the_visaguy/pull/52 (`develop`, **conflicts**:
  `fixtures/custom_html_block.json`, `hooks.py`, `modules.txt`; it also carries
  `02fee42`, the `dash-updt` merge on `main` that `develop` lacks). Owner
  resolves.

Known limitation, not fixed: a primary's dependant list can hold unrelated
primaries (risk 28), so a group check can send another family's data to the
provider and overwrite their QC fields. Unexpected job errors go to the Error
Log with Frappe's traceback variables, which can include applicant data.

## What remains

0. **Run a real check as an operations user** (not yet done; only as
   Administrator). Configure Allowed Roles on the agent first. Recheck case A on `visaguy` with the new branch code and compare with the first report (owner). Remove the "Report format" section from the huf Schengen template: the format is now set in code.
1. **Real model run (owner):** set an AI provider key and the QC agent in
   huf (Persist Conversation off, OCR model set, allowed roles include the
   operations roles), create the Schengen prompt template, link it on the
   Schengen destinations, select the agent in Visaguy AI Settings, then run
   Check QC on real past files with their documents on disk.
2. **Browser check:** button, scope dialog, tab layout, realtime refresh and
   alert, on the test site or `visaguy` after migrate.
3. **Owner review and merge** of PRs 51 and 52; resolve the `develop` conflicts.
4. ~~Owner decision on ADR-017.~~ Accepted 2026-11-02.
5. Before live: pin huf (`git checkout v1.0.0-beta.4`, `bench exclude-app
   huf`) and resolve the Python package drift (FEAT-006 risks; it also stops
   Frappe's S3 backup jobs loading on the dev bench).
6. `visaguy` needs a migrate to show the tab; until then the button stays
   hidden there.

## Definition of done

- Committed and merged; 35 QC tests and the app suite pass.
- A real check on a pilot Schengen group produces a report on every file,
  verified by the owner.
- ADR-017 accepted.
