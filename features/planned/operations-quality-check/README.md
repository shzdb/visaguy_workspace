---
id: FEAT-006
title: AI quality check for process files (huf)
status: planned
priority: medium
repositories:
  - the_visaguy
  - visaguy_crm
  - processflo
  - fileflo
  - huf
owners: []
depends_on: []
created: 2026-10-19
updated: 2026-10-19
---

# AI quality check for process files (huf)

> Numbering: FEAT-002 to FEAT-004 are taken on the unmerged branch
> `chore/workspace-audit-remediation`, and FEAT-005 is the UK refusal checker.
> This feature is FEAT-006.
>
> "QC" in this document means the operations quality check that the team
> calls "QZ".

## Planning status (resume here)

Last updated 2026-10-19. Status: **planned**, design agreed in principle, no
task files created, no code written.

**Settled:** decisions D1–D12 below (button, not workflow; all available
documents; sidebar included; code in `the_visaguy` module Quality Check;
Schengen pilot in all three departments; one huf agent with a prompt
template per department; per-department QC action set in settings; Team
Leads see R6).

**Pending the owner:**

- How operations attach prepared documents (D4, open question 2): action
  row `custom_attach` (confirm one file per action is enough) or more RPA
  Documents options.
- Workspace placement of QC cards, charts and report links (D11, open
  question 3).
- Whether to add a "Quality Check" action to the Schengen process templates
  (open question 1).
- huf agent, provider, model and the Schengen prompt template (D9, D8a).
  These are configured by the owner in huf.

**Next steps when resuming:**

1. Write the ADR (task 1): huf on the same site as a lazy dependency of
   `the_visaguy`, the Quality Check module boundary, data sent to the AI
   provider, one agent with department prompt templates.
2. After the ADR is accepted, create task files TASK-046 onward from the
   Tasks list under `tasks/ready/` (check the highest TASK number first; it
   was TASK-045 on 2026-10-19).
3. Fold in the owner's answers to the pending items above.

**Evidence sources used:** bench source on `erpcode` (`processflo`,
`fileflo`, `visaguy_crm`, `the_visaguy`), huf commit `69d65d8`, and
read-only counts on the `visaguy` development site. Re-check counts before
relying on them after a new database restore.

## Summary

Before operations deliver a visa file, a person checks that the form data,
the applicant's uploads, and the documents that operations prepared all
agree. Today they download everything and paste it into an external AI chat.

This feature adds a **Check QC** button to the process file. The button
starts a huf agent in the background. The agent gets the form data and
**every document available at that moment** for the primary applicant and all
dependants, and it returns a report. The report and the QC history (checked
or not, when, by whom, the result, and whether the file was rechecked after
fixes) show in a **Quality Check** tab on the process file. Operations users
do not open the huf UI.

QC is optional. The button is on every process file for operations users,
but it does not change the workflow state and does not block any transition.
Departments that are not ready simply do not click it. The only difference
between departments is the prompt, which the owner sets on the huf agent.

## Current state (verified 2026-10-19)

Evidence comes from source on the erpcode bench and from read-only counts on
the `visaguy` development site (a database copy of live; latest process file
2026-10-05). Counts are production estimates, labelled **data-observed**.

### How the team does QC today (owner report)

1. Download the file collection data of the process file as CSV.
2. Download every applicant upload and every prepared document.
3. Upload all of them to Claude or ChatGPT with a prompt such as: cross check
   the data against the documents, use the latest issued Schengen visa in the
   application form, make sure hotel vouchers, flight reservations and the
   itinerary agree, make sure dates and personal data on the cover letter and
   application form agree, and flag errors or points that need more clarity
   for each person.
4. Read the answer and fix the file by hand.

There is no record of the check in VisaGuy.

### Where the data and documents live

| Item | Location | Label |
|---|---|---|
| One process file per applicant | `PF Process File` (`processflo`). `custom_type` = Primary or dependant. The primary lists dependant files in `custom_dependent_details`; a dependant points back by `custom_primary_process_file` | source-wired |
| Applicant form data | `FF File Collection.information` (`field_name`, `value`, `group_name`, `field_id_link`), linked by `PF Process File.file_collection`. A lead-level collection is linked by `custom_lead_file_collection`. In 2026 almost every process file has both, and they are always different collections, so QC must read both | source-wired, data-observed |
| Applicant uploads | `FF File Collection.file_collection_file` rows → `FF Document.attach` | source-wired |
| RPA application form | Button **Generate Application Form** → `visaguy_crm.server_scripts.rpa.generate_application_form`. Posts the `information` table and mapped files to the RPA or PDF Filler URL in `TVG CRM Settings`; saves the PDF in `custom_application_form` (1,724 files in 2026) | source-wired, data-observed |
| RPA Documents | `PF Process File.custom_rpa_documents` (`document_name` Select = Flight Tickets / Hotel Bookings, `attachment`). Rows on 1,092 process files in 2026 | source-wired, data-observed |
| Action rows | `PF Process File Action` (`status` Pending / Completed, `custom_attach`). 19,557 of 196,821 rows are Completed. Templates already have a **Quality Check** action (5,109 rows, plus variants) | data-observed |
| Sidebar attachments | `File` attached to the process file with no field. 16,007 in 2025 (most cover letters, itineraries, hotels, flights), 1,930 in 2026 (mostly the RPA form, which `save_file` also attaches here) | data-observed |
| Workflow | `Process File Workflow` (fixture in `visaguy_crm`). **Not changed by this feature** | source-wired |

In 2026, 5,921 files reached Documents Delivered or Completed, but almost no
cover letters or itineraries are stored in VisaGuy: 1 of each in the sidebar,
none in `FF Document`. They are probably kept outside VisaGuy (an action named
"Drive Upload" exists). A QC run can only check what is in VisaGuy, so the
report must say which documents it saw.

### Can operations add a document of any type to a process file? (sidebar excluded)

**Not cleanly.** Three routes exist:

| Route | Any type? | Limits | Use in 2026 |
|---|---|---|---|
| RPA Documents table on the process file | No. `document_name` is a Select with only Flight Tickets and Hotel Bookings | The section is hidden unless the destination has RPA enabled for the zone (`toggle_rpa_section` in `pf_process_file_doctype.js`) | 2,169 attachments |
| `custom_attach` on an action row | Yes, any file | One file per action row; the file is named by the action, not by the document | 4 attachments in total, ever |
| FileFlo form "Additional Documents" on the file collection | Yes | **Client-facing form. Not usable for documents that operations prepare** (owner, 2026-10-19). Staff files would mix with applicant files | 3,042 by staff and 16,954 by applicants on process file collections |

In the desk, the file collection grid is read-only (property setters on
`FF File Collection File`), so staff cannot add a typed document there.

How operations attach prepared documents is the **owner's decision** (see
Decisions). The two candidates are the action row `custom_attach` (to confirm
with the team whether one attachment per action is enough) and more options
in the RPA Documents table. The QC context builder reads both, plus the
sidebar, so QC does not depend on that choice.

### Departments, roles and workspaces (data-observed)

| Item | Values |
|---|---|
| Operations departments (`PF Process File.custom_department`) | `Operations - <region> - <company abbr>`: regions Schengen, Asia, UK, US, Canada; companies T (TVG), TQ (TVG Qatar), TS (TVG Saudi) |
| Schengen volume in 2026 | `Operations - Schengen - T` 8,601, `- TQ` 1,270, `- TS` 216 process files (about 66% of all 2026 files) |
| Roles | Operations Associate (69 enabled users), Operations Team Lead (25), Management Role (2). A duplicate role "Operation Team Lead" also exists |
| Workspaces (`visaguy_crm`) | Operation Associate (Operations Associate), Operation Manager (Operations Team Lead), Management (Management Role) |
| Department scope rule | Existing Insights queries scope a user to `Employee.department` plus the `Additional Operation Department` rows on the Employee (29 rows in use) |

### huf (commit `69d65d8`, 2026-10-10)

huf is **not installed** on the bench. Its source shows:

| Capability | Evidence | Use here |
|---|---|---|
| Agent with provider, model, instructions, OCR, temperature, reasoning settings | `Agent` DocType | Holds the QC prompt and model. Admins change them in huf without a deploy |
| Python entry point with files and structured output | `huf.ai.agent_integration.run_agent_sync(agent_name, prompt, files=…, response_format=…)` | `the_visaguy` calls this from a background job |
| Run log with reference document, status, response, tokens, cost | `Agent Run` | Audit and cost per QC run |
| Images go to the model as images; PDFs and other files go through text or vision OCR first | `providers/litellm.py` `_file_dict_to_data_image_url`; `ocr_engine.extract_document` | Scanned passports and visas need the OCR model set on the agent |
| No-code Doc Event automation with file fields | `Automation Trigger.file_attachments` (DocField or Child Table Field on the firing document only) | Not enough: QC files sit behind links (`FF Document`), in other DocTypes, and on dependant files |
| Compatibility | `frappe >= 15`, `requires-python >= 3.10` | Matches the bench (Frappe 15.113, Python 3.10.12) |

So a small adapter in `the_visaguy` collects the context and calls huf. huf
supplies the agent setup, provider keys, OCR, run log and cost.

## Decisions made (owner, 2026-10-19)

| # | Decision |
|---|---|
| D1 | QC is an optional **Check QC** button, not a workflow state. It never blocks a transition. |
| D2 | Documents vary by file and client. A run takes every document available at check time; nothing is mandatory. |
| D3 | The FileFlo "Additional Documents" upload is client-facing and is not used for operations documents. |
| D4 | How operations attach prepared documents (action row `custom_attach` or more RPA Documents options) is left to the owner. It is not part of this feature's tasks. |
| D5 | Sidebar attachments are included in the QC context. |
| D6 | Code lives in `the_visaguy`, in a new module **Quality Check**. |
| D7 | The Schengen operations team runs the pilot, in all three Schengen departments (`- T`, `- TQ`, `- TS`). |
| D8 | No per-department on/off switch. The button is the same everywhere; only the prompt differs. |
| D8a | One huf agent for QC. Each department has its own huf **Agent Prompt** template, passed at run time (owner, 2026-10-19). |
| D9 | The owner chooses the AI provider and model and configures the agent in huf. |
| D10 | Team Leads see the per-associate report (R6) for their departments. |
| D11 | No separate Quality Check workspace. **Placement in the existing workspaces is pending owner clarification** (open question 3). |
| D12 | When a check leaves no open findings, the group's QC action rows are marked Completed automatically. Which action is configured per department in settings, not hard-coded. |

## User value

- No download and upload to an external portal.
- The same check and prompt for every file, with the documents that exist at
  check time.
- A record on the process file: checked or not, when, by whom, the result,
  what was fixed, and whether it was rechecked.
- Team leads see QC coverage and findings for their departments; management
  sees all departments, the cost, and the trend.
- Admins change the prompt or model in huf without a deploy.

## Scope

### Included

- **Check QC** and **Recheck** buttons on the process file.
- QC summary fields on the process file and a QC Run history record.
- A context builder that takes all available data and documents for the
  group at check time.
- One huf agent for QC, called with structured output.
- A **Quality Check** tab with the latest report, finding resolution, history
  and recheck.
- QC settings: the QC agent, a default prompt template, and per department a
  prompt template and the action to complete; limits.
- Automatic completion of the configured QC action rows (D12).
- Reports, number cards and charts for associates, team leads and
  management, placed in the existing workspaces.

### Excluded

- Workflow states or transitions.
- A fixed checklist of required documents.
- The way operations attach prepared documents (D4).
- Automatic correction of data or documents.
- Operations access to the huf UI.
- Changes to the RPA or PDF Filler services.

## Requirements

### QC run

1. **Button.** A **Check QC** button shows on every process file for users
   with Operations Associate or Operations Team Lead. On a dependant file it
   runs QC for the whole group and stores the result on the primary.
1a. **Prompt choice.** The run uses the QC agent with the prompt template
   mapped to the primary file's department in settings, or the default
   template when the department has no row. The run records the template,
   its version, and the huf prompt snapshot (see "Prompt templates").
2. **No enforcement.** Running or not running QC does not change
   `workflow_state` or any workflow rule.
3. **Background run.** The click creates a QC Run (Queued) and enqueues a job
   in the `long` queue. Only one run per group can be Queued or Running; the
   button is disabled while one is.
4. **All available documents.** The context covers the primary and every
   dependant. For each applicant it takes: form data from the process file
   collection and the lead collection; every file collection upload that has
   a file (applicant uploads, including the applicant's Additional
   Documents); the application form; every RPA Documents row; every action
   row attachment; and sidebar attachments.
5. **Manifest.** Each file gets a label (applicant, source, name, upload
   date). The run stores the manifest with a hash of each file, so the report
   says what it saw and the tab can show "documents changed since last
   check".
6. **Skips.** Files missing on disk, unsupported, or over the limits are
   skipped and listed. Duplicate files (same hash, for example the RPA form in
   both its field and the sidebar) are sent once.
7. **Report.** The agent returns JSON that matches a fixed schema (see
   Proposed design). A response that does not match fails the run.
8. **Summary on the process file.** When a run ends, the adapter updates the
   QC fields on the primary (and a pointer on each dependant) with
   `db_set`, so that no process file save hooks run.
9. **Resolution.** In the tab, a user marks each finding **Fixed**, **Not an
   issue**, or **Open**, with an optional remark. User and time are recorded.
10. **Recheck.** **Recheck** starts a new run that links to the previous run
    and sends its findings to the agent, which states for each one: resolved,
    still present, or cannot tell. The tab shows "Rechecked after fixes" with
    the counts.
11. **Alert.** The user who clicked gets a realtime alert when the run ends.
11a. **Action completion (D12).** When the group has no Open findings (the
    run verdict is Passed, or a user resolves the last Open finding), the
    adapter reads the **QC action** set for the primary file's department in
    settings (falling back to the default row). It sets every action row on
    the group's process files whose `action` equals that `PF Process Action`
    to Completed, with `db_set` on the child row, and adds a comment that QC
    completed it. Nothing is hard-coded: a department with no QC action gets
    no change. Rows are never set back to Pending automatically. See "Which
    action is completed" below.
12. **huf optional at import.** `the_visaguy` imports huf only inside the QC
    job. If huf is not installed, the button does not show and nothing else
    in `the_visaguy` changes.

### Access

13. Process file readers can read the QC result of that file.
14. QC Run list, reports and number cards are scoped by department:
    - Operations Associate: QC runs on files they can open; the "My QC"
      view shows runs they started.
    - Operations Team Lead: their `Employee.department` plus their
      `Additional Operation Department` rows (the existing Insights rule),
      including R6 (QC by Associate) for those departments.
    - Management Role and System Manager: all departments and companies.
15. Only Operations Associate and Operations Team Lead can run QC or change
    finding resolution. Only System Manager can change QC settings.

### Reports and dashboards

16. Reports, cards and charts listed under "Reports and dashboards" below,
    with the department scope in Requirement 14 applied on the server.
17. Each report filters by date range, company, department, destination and,
    where it makes sense, user.
18. No passport numbers, dates of birth, or other applicant values appear in
    any report or chart. Finding text appears only in the per-file tab and in
    the findings report for users who can open that process file.

## Proposed design

### Flow

```text
[Check QC] / [Recheck]  (any time, any workflow state)
        │
        ▼
create Process File QC Run (Queued) ──▶ enqueue job (long queue)
        │
        ▼
build context for primary + dependants
  form data ─┐
  uploads ───┤ manifest + files (deduplicated by hash)
  RPA docs ──┤
  action ────┤
  sidebar ───┘
        │
        ▼
huf run_agent_sync(agent, prompt_template=<department template>,
                  prompt, files, response_format)
        │
        ▼
save findings on the QC Run ──▶ db_set QC summary on process files ──▶ realtime alert
```

### Code layout (`the_visaguy`, module Quality Check)

```text
the_visaguy/quality_check/
  doctype/process_file_qc_run/
  doctype/process_file_qc_finding/
  doctype/process_file_qc_settings/
  context.py      # group expansion, document sources, manifest, hashes
  runner.py       # enqueue, huf call, schema check, save, db_set, alert
  api.py          # whitelisted: start check, recheck, set resolution, tab data
  scope.py        # department scope used by permissions and reports
  report/…        # script reports
  number_card/…, dashboard_chart/…   # placed in visaguy_crm workspaces
public/js/pf_process_file_qc.js   # buttons and tab rendering
```

Custom fields on `PF Process File` ship as fixtures from `the_visaguy`, like
the visa tracking fields.

### QC summary fields on `PF Process File` (Quality Check tab)

| Field | Type | Meaning |
|---|---|---|
| `custom_qc_status` | Select: Not checked / Running / Passed / Issues found / Could not check / Failed | Result of the latest run |
| `custom_qc_last_run` | Link Process File QC Run | Latest run |
| `custom_qc_last_checked_on` | Datetime | When the latest run ended |
| `custom_qc_last_checked_by` | Link User | Who started it |
| `custom_qc_run_count` | Int | Number of runs for the group |
| `custom_qc_open_findings` | Int | Findings still Open on the latest run |
| `custom_qc_rechecked` | Check | The latest run is a recheck of an earlier run with issues |
| `custom_qc_html` | HTML | Report view, filled by client script |

### New DocTypes

- `Process File QC Run`: `process_file` (primary), `group_files`,
  `department`, `company`, `destination` (copied at run time for reports),
  `status` (Queued / Running / Completed / Failed), `verdict` (Passed /
  Issues found / Could not check), `summary`, `recheck_of`, `is_first_run`,
  `triggered_by`, `started_at`, `finished_at`, `duration_seconds`,
  `workflow_state_at_run`, `documents_sent`, `documents_skipped`,
  `manifest` (JSON), `agent_run` (Link Agent Run), `model`,
  `total_tokens`, `cost`, `error_code`, `error`, `result_json`, counts per
  severity, `findings` (child table).
- `Process File QC Finding` (child): `severity` (Error / Warning /
  Clarify), `applicant`, `topic`, `topic_category` (Personal data / Passport
  / Previous visa / Travel dates / Accommodation / Flight / Itinerary / Cover
  letter / Financial / Missing document / Other), `documents`, `expected`,
  `found`, `explanation`, `previous_finding`, `recheck_result` (Resolved /
  Still present / Cannot tell), `resolution` (Open / Fixed / Not an issue),
  `resolved_by`, `resolved_on`, `remark`.
- `Process File QC Settings` (single): `agent` (Link Agent),
  `default_prompt_group` and `default_qc_action` (Link PF Process Action,
  optional), `departments` (child table `Process File QC Department`, below),
  `max_files`, `max_total_mb`, `include_sidebar_attachments` (default on),
  `monthly_cost_alert` (optional).
- `Process File QC Department` (child): `department` (Link Department,
  unique), `prompt_group` (the huf template family; the latest active
  version is used), `pinned_prompt` (Link Agent Prompt, optional: use this
  exact version instead), `qc_action` (Link PF Process Action, optional).
  The pilot needs three rows: `Operations - Schengen - T`, `- TQ`, `- TS`,
  all pointing to the Schengen template.
- `Process File QC Run` also stores `prompt_template` (Link Agent Prompt),
  `prompt_version`, and `qc_action_completed` (Check).

Results live in their own DocType, not in a child table on the process file.
A process file save fires many hooks (tracking sync, visa centre sync,
refetch of missing fields, timers, form-disable logic) and adds a version
row. A separate record keeps the full history and does not race with a user
who edits the file. The copied `department`, `company` and `destination`
fields keep reports fast and stable if the file moves later.

### Prompt templates (huf Agent Prompt)

huf keeps prompt templates in the `Agent Prompt` DocType: `title`, `category`,
`prompt_body`, `version`, `is_latest`, `prompt_group` (all versions of one
template), `previous_version`, `is_active`. `run_agent_sync` takes
`prompt_template` (and optional `prompt_version`). When it is passed, huf
uses that template as the agent's system prompt for this run only, without
changing the agent. huf also saves the system prompt actually used in
`Agent Run Prompt Snapshot`. (Source, commit `69d65d8`:
`agent_integration.run_agent_sync`, lines around 1551 and 2070.)

How the QC uses this:

1. The owner creates one QC agent (provider, model, OCR, temperature) and
   one template per department in huf, under a category such as "Process
   File QC". Departments that share rules can share a template.
2. Settings map each department to a template family (`prompt_group`). The
   adapter resolves the latest active version at run time, so a prompt edit
   in huf takes effect on the next run without a deploy. A department can
   pin one exact version instead.
3. The adapter builds the user message in code: the shared rules that must
   not vary (use only the manifest labels, say "not readable", do not guess,
   give a result for every previous finding on a recheck), the manifest, and
   the form data. The JSON schema goes in `response_format`. So department
   templates hold only the department's checking rules, and a template edit
   cannot break the output format.
4. Every QC Run stores the template name and version, so reports can compare
   results before and after a prompt change.

### Department template content (Schengen draft, to refine with the team)

- Compare every applicant's form data with every document provided. Do not
  expect a fixed set of documents; check what is there.
- When a Schengen visa copy is present, use the latest issued one for
  previous-visa answers in the application form.
- Check that names, dates, passport numbers, cities and travel dates agree
  across all documents, for every applicant.
- Report a finding only with the document labels that show it. Say "not
  readable" when a document cannot be read. Do not guess values.
- List document types that are usually expected but are not in the
  manifest as Clarify findings with category Missing document.
- Give each finding one `topic_category` from the fixed list.

(The recheck and output rules are in the code-built message, not in the
template.)

### Structured output (draft schema)

```json
{
  "verdict": "passed | issues_found | could_not_check",
  "summary": "string",
  "findings": [
    {
      "severity": "error | warning | clarify",
      "applicant": "string",
      "topic": "string",
      "topic_category": "personal_data | passport | previous_visa | travel_dates | accommodation | flight | itinerary | cover_letter | financial | missing_document | other",
      "documents": ["string"],
      "expected": "string",
      "found": "string",
      "explanation": "string"
    }
  ],
  "previous_findings": [
    { "id": "string", "result": "resolved | still_present | cannot_tell", "note": "string" }
  ],
  "unreadable_documents": ["string"]
}
```

### Which action is completed (D12)

The action is **configured, not hard-coded**:

- Each `Process File QC Department` row has an optional `qc_action` (Link
  `PF Process Action`). `default_qc_action` covers departments without a row.
  Empty means "complete nothing".
- The adapter matches action rows by exact link value
  (`PF Process File Action.action == qc_action`), on the primary and every
  dependant process file.
- Action names differ between templates today (2026 counts): "Quality Check"
  in UK, US and Asia (about 3,400 rows); "QUALITY CHECK (INTERNAL) &
  SUBMISSION" in Asia (about 600); "QUALITY CHECK (INTERNAL)" (2). The
  combined QC-and-submission action should not be set as `qc_action`,
  because QC does not do the submission.
- Schengen templates have no QC action in 2026, so the Schengen rows start
  with `qc_action` empty (open question 1).
- The form-disable logic in `visaguy_crm` uses `TVG CRM Settings.action_name`
  ("Application Preparation" on `visaguy`). The adapter rejects a
  `qc_action` equal to that value, because `db_set` would skip the form-
  disable hook that a normal save runs.

## Reports and dashboards

### Metric definitions

| Metric | Definition |
|---|---|
| Delivered file | Primary process file whose `custom_documents_delivered_date` is in the period |
| QC coverage | Delivered files with at least one completed QC run before or on the delivered date ÷ delivered files |
| Delivered without QC | Delivered files with no completed run |
| First-pass rate | Groups whose first completed run is Passed ÷ groups with a completed run |
| Issues per file | Error + Warning findings on the first run ÷ groups checked |
| Recheck rate | Groups with an Issues found run followed by a recheck ÷ groups with an Issues found run |
| Time to clear | Time from the first Issues found run to the first later Passed run, or to the last Open finding marked Fixed / Not an issue |
| Not-an-issue rate | Findings marked Not an issue ÷ resolved findings (a measure of false alarms) |
| Delivered with open findings | Delivered files whose latest run still has Open Error findings |
| Cost per file | Sum of run `cost` ÷ groups checked |

### Script reports (module Quality Check, standard)

| # | Report | Audience | Content |
|---|---|---|---|
| R1 | **QC Coverage** | Team Lead, Management | One row per department (group by company or destination optional): delivered files, checked, not checked, coverage %, first-pass rate, issues per file. Chart: coverage % by week |
| R2 | **Delivered Without QC** | Team Lead | List of delivered files with no QC run: process file, applicant count, department, designated user, delivered date. Department filter defaults to the user's departments |
| R3 | **QC Runs** | Associate, Team Lead | One row per run: process file, started by, started on, workflow state at run, verdict, errors / warnings / clarify, recheck of, documents sent / skipped, duration. "My QC" is this report filtered to the session user |
| R4 | **Open QC Findings** | Associate, Team Lead | Open findings on latest runs, oldest first: process file, severity, category, applicant label, age, designated user, workflow state. Highlights files already delivered |
| R5 | **QC Findings Analysis** | Team Lead, Management | Counts by category and severity per department and month; not-an-issue rate per category. Chart: top categories. No finding text |
| R6 | **QC by Associate** | Team Lead (own departments), Management | Per user: files checked, first-pass rate, issues per file, recheck rate, time to clear |
| R7 | **QC Usage and Cost** | Management, System Manager | Per month and department: runs, failed runs by `error_code`, tokens, cost, cost per file, average duration. Chart: cost per month |

### Number cards and charts

| Item | Type | Audience |
|---|---|---|
| QC runs today | Number card | All QC roles |
| Open Error findings | Number card | Associate (own), Team Lead (scope) |
| QC coverage this month | Number card | Team Lead, Management |
| Delivered without QC this month | Number card | Team Lead, Management |
| First-pass rate this month | Number card | Team Lead, Management |
| QC cost this month | Number card | Management |
| Coverage by week, per department | Line chart | Team Lead, Management |
| Verdicts by week | Stacked bar | Team Lead, Management |
| Findings by category | Bar chart | Team Lead, Management |

### Placement (pending owner clarification, D11)

There is no separate Quality Check workspace. Where the cards, charts and
report links appear is pending the owner (open question 3). Facts for that
decision: the existing Operation Associate, Operation Manager and Management
workspaces are standard workspace JSON files in `visaguy_crm` (module
Visaguy Crm), synced on migrate, so adding QC items there is an edit in
`visaguy_crm`; a database-only change is lost on the next migrate.

A possible split by role, for discussion:

| Workspace (role) | QC content |
|---|---|
| Operation Associate (Operations Associate) | Cards: QC runs today, my open Error findings. Links: R3 (My QC), R4 |
| Operation Manager (Operations Team Lead) | Cards: coverage this month, delivered without QC, first-pass rate, open Error findings. Charts: coverage by week, verdicts by week, findings by category. Links: R1–R6 |
| Management (Management Role) | Cards: coverage this month, first-pass rate, QC cost this month. Charts: coverage by week per department, findings by category. Links: R1, R5, R6, R7 |

Number cards and charts that need department scope use Script Report
sources or custom methods, because the standard Count / Group By cards do not
apply the Employee department rule.

## Tasks

Draft only. No task can be `ready` until the ADR is accepted. The open
questions do not block the build; task 9 waits for open question 3.

1. ADR: huf on the same site as a lazy dependency of `the_visaguy`; QC
   module boundary; data sent to the AI provider; one agent with
   department prompt templates.
2. Install huf on `visa-tracker-test.localhost`; check package conflicts,
   worker queues and scheduler load.
3. Quality Check module: DocTypes, settings, custom fields, permissions and
   department scope.
4. Context builder with tests (group expansion, every source, labels, hashes,
   skips, duplicates).
5. Runner: huf call, schema check, save, `db_set` summary, realtime alert,
   one active run per group, recheck linkage.
6. Check QC and Recheck buttons, Quality Check tab, finding resolution.
7. Automatic completion of the configured QC action rows (D12).
8. Reports R1–R7.
9. Number cards and charts. Placement waits for open question 3.
10. Schengen pilot in `Operations - Schengen - T`, `- TQ` and `- TS`: run on
    real past files, compare with the manual QC answer, tune the prompt, and
    review the not-an-issue rate after two weeks.

## Acceptance criteria

- **Check QC** produces a QC Run and a report in the tab, with no huf screen
  opened and no change to `workflow_state`.
- The run includes every dependant and every document available at check
  time, including sidebar attachments, and the manifest lists them with
  skipped files and reasons.
- A deliberately wrong date of birth, passport number, or hotel date in a
  test file is reported with the correct applicant and documents.
- After a fix, **Recheck** reports the earlier finding as Resolved, and the
  process file shows Rechecked.
- Each finding can be marked Fixed or Not an issue, with user and time.
- A Team Lead sees only their departments in every report and card; a
  Management Role user sees all; an Associate sees only files they can open.
- R1 coverage for a test period matches a manual count.
- No report or chart shows applicant personal values.
- A department with its own template row uses the latest version of that
  template; a department without a row uses the default template; the QC
  Run shows the template and version used.
- Editing a template in huf changes the next run with no deploy, unless the
  department pins a version.
- When the last Open finding is resolved, the action set as `qc_action` for
  the department becomes Completed on every file in the group, no other
  action changes, and no process file save hooks run. A department with no
  `qc_action` gets no action change.
- With huf uninstalled, `the_visaguy` works and the button is hidden.

## Dependencies

- huf installed on the same site.
- An AI provider account with a model that reads images and PDFs, and an OCR
  model for scanned files.
- The owner's decision on how operations attach prepared documents (D4). QC
  works without it but sees fewer documents.

## Risks

- **Personal data to an AI provider.** Passports and visas go to the model
  provider set in huf. This already happens by hand today, but now it is
  systematic. Use a provider and plan with no training on inputs and short
  retention, and record the choice in the ADR.
- **Public application forms.** `generate_application_form` saves the RPA
  and PDF Filler output with `is_private=0`, so the application form is a
  public file. Outside this feature; recommend a separate fix.
- **Incomplete document set.** Cover letters and itineraries are mostly
  outside VisaGuy in 2026. A "Passed" verdict covers only the documents in
  the manifest; the tab shows the document count next to the verdict.
- **AI errors.** The agent can miss mistakes or report false ones. The report
  is advisory. R5 tracks the not-an-issue rate.
- **Per-person metrics.** R6 can be read as a performance score. The AI is
  not exact, so agree its use with management before showing it widely.
- **huf footprint.** huf adds `doc_events["*"]` hooks on every DocType (the
  lookup is cached), about 18 scheduler jobs, and large Python dependencies
  (litellm, chromadb, faiss, llama-index). Check worker capacity and package
  conflicts on the test site before live.
- **Large groups.** Many applicants and scanned PDFs can exceed the model
  context or the job timeout. Enforce the file and size limits, and list
  what was not checked.
- **Use outside the pilot.** Any operations user can click the button on any
  file, so non-Schengen files can be checked with the default prompt, and
  each click costs money and sends data to the provider. Tell other
  departments not to use it yet, or give their department its own prompt template. R7 shows use by department.
- **Low coverage outside Schengen.** Coverage is low by design for
  departments that do not use QC yet. Filter R1 by department when reading
  it.
- **Schengen has no "Quality Check" action.** In 2026 the action exists in
  UK, US and Asia templates (about 3,400 rows), but not in Schengen
  templates. D12 does nothing for the pilot until the Schengen process
  templates get the action.
- **Missing files on `visaguy`.** The dev copy has no uploaded files on disk,
  so end-to-end tests there need files copied by hand.

## Open questions

1. Should the "Quality Check" action be added to the Schengen process
   templates, so D12 works in the pilot? (Template data, owner or operations
   decision.)
2. How should operations attach prepared documents (D4)? Owner decision; QC
   reads every candidate source meanwhile.
3. Where do the QC cards, charts and report links go? **Pending owner
   clarification** (D11).

## Completion notes
