---
id: FEAT-006
title: AI quality check for process files (huf)
status: planned
priority: medium
repositories:
  - the_visaguy
  - huf
owners: []
depends_on: []
created: 2026-10-19
updated: 2026-10-23
---

# AI quality check for process files (huf)

> Numbering: FEAT-002 to FEAT-004 are taken on the unmerged branch
> `chore/workspace-audit-remediation`, and FEAT-005 is the UK refusal checker.
> This feature is FEAT-006.
>
> "QC" in this document means the operations quality check that the team
> calls "QZ".

## Planning status (resume here)

Last updated 2026-10-23. Status: **planned**. Phase 1 design agreed with the
owner on 2026-10-23 (simple flow below). No ADR, no task files, no code yet.

**Pending the owner:** nothing open for Phase 1 (all open questions closed
on 2026-10-23).

**Next steps when resuming:**

1. Write the ADR: huf on the same site as a lazy dependency of
   `the_visaguy`; the Quality Check module; data sent to the AI provider;
   prompt template per destination.
2. After the ADR is accepted, create Phase 1 task files from the "Phase 1
   tasks" list (check the highest TASK number first; it was TASK-047 on
   2026-10-23).
3. The owner configures the huf agent and the Schengen prompt template.

**Evidence sources:** bench source on `erpcode` (`processflo`, `fileflo`,
`visaguy_crm`, `the_visaguy`), huf commit `69d65d8`, and read-only counts on
the `visaguy` development site (a database copy of live). Re-check counts
after a new database restore.

## Summary

Before operations deliver a visa file, a person checks that the form data,
the applicant's uploads, and the documents that operations prepared all
agree. Today they download everything and paste it into an external AI chat.

Phase 1 adds a **Check QC** button to the process file. The button sets the
QC status to Processing and starts a huf agent in the background. The agent
checks the file's data and documents against the prompt template set on the
file's destination. The output is saved on the process file and shown in a
**Quality Check** tab. Operations users do not open the huf UI. QC is
optional and does not touch the workflow.

## Decisions (owner)

| # | Date | Decision |
|---|---|---|
| D1 | 2026-10-19 | QC is an optional **Check QC** button, not a workflow state. It never blocks a transition. |
| D2 | 2026-10-19 | Documents vary by file and client. A run takes every document available at check time; nothing is mandatory. |
| D3 | 2026-10-19 | The FileFlo "Additional Documents" upload is client-facing and is not used for operations documents. |
| D4 | 2026-10-23 | Prepared documents (cover letter, itinerary, bookings and others) are read from whatever is in the sidebar attachments. No new attachment field or route is added. |
| D5 | 2026-10-19 | Sidebar attachments are included. |
| D6 | 2026-10-19 | Code lives in `the_visaguy`, in a new module **Quality Check**. |
| D7 | 2026-10-19 | The Schengen operations team runs the pilot. |
| D9 | 2026-10-19 | The owner chooses the provider and model and configures huf. |
| D11 | 2026-10-23 | QC reports go in a **separate Quality Check workspace** for Operations Team Leads and Management (replaces the 2026-10-19 "no separate workspace" decision). |
| D13 | 2026-10-23 | A new single DocType **Visaguy AI Settings** in `the_visaguy` holds the huf agent used for QC. |
| D14 | 2026-10-23 | The prompt template is set **per destination**: a custom tab on `Destination` (added from `the_visaguy`) links the huf prompt template. This replaces the per-department template idea (old D8a). |
| D15 | 2026-10-23 | On a primary file, the user chooses **this file only** or **primary and all dependants**. On a dependant file, QC runs for that file only. |
| D16 | 2026-10-23 | Phase 1 flow: click → status Processing → huf agent checks the data and files against the prompt → output saved on the process file. |
| D17 | 2026-10-23 | No "Quality Check" action is added to the Schengen templates. Automatic action completion (old D12) moves to Phase 2. |
| D18 | 2026-10-23 | Phase 1 reads all sources: the process file collection and the **lead file collection** (data and uploads), the application form, RPA Documents, action attachments and sidebar attachments. |

## Phase 1 — simple QC run

### User flow

```text
Process file (any workflow state)
  └─ [Check QC]
       ├─ primary file:   dialog → "This file only" | "Primary and all dependants"
       └─ dependant file: this file only
            │
            ▼
  QC status = Processing on every included file   (form shows "QC running")
            │
            ▼  background job (long queue)
  collect data + files → huf agent (destination's prompt template)
            │
            ▼
  save output on every included file, status = Completed (or Failed)
  realtime refresh of the open form + alert to the user who clicked
```

### Requirements

1. **Button.** **Check QC** shows for Operations Associate and Operations
   Team Lead when the file's destination has a QC prompt template. With no
   template, the button is hidden, so destinations outside the pilot cannot
   run QC by accident.
2. **Scope choice (D15).** On a primary file (`custom_type` = Primary) with
   dependants, a dialog asks: "This file only" or "Primary and all
   dependants" (from `custom_dependent_details`). On a dependant file, or a
   primary with no dependants, QC runs for that file with no dialog.
3. **One run at a time.** If any included file is already Processing, the
   click is refused with a message. A run stuck in Processing for more than
   30 minutes (job lost) can be started again.
4. **Status (D16).** The click sets `custom_qc_status` = Processing on every
   included file and enqueues the job. Writes use `db_set`, so no process
   file save hooks run (tracking sync, visa centre sync, timers,
   form-disable logic).
5. **Inputs.** For each included file, labelled by applicant name:
   - form data: the `information` rows of the process file's file collection
     and of the lead file collection (`custom_lead_file_collection`) as
     `label: value`, each labelled with its collection (D18);
   - file collection uploads: every `FF File Collection File` row with an
     `FF Document` file, in both collections (applicant uploads, including
     the applicant's Additional Documents);
   - the application form (`custom_application_form`);
   - RPA Documents rows (`custom_rpa_documents`);
   - action row attachments (`PF Process File Action.custom_attach`);
   - sidebar attachments (`File` attached to the process file with no field).
   Duplicate files (same content hash, such as the RPA form in its field and
   in the sidebar) are sent once. Files missing on disk or over the limits in
   settings are skipped and listed in the output.
6. **huf call.** The job calls `run_agent_sync` with the agent from Visaguy
   AI Settings, `prompt_template` from the destination, the files, and a
   small `response_format` (below). The user message, built in code, holds
   the shared rules (use the given labels, say "not readable", do not
   guess), the list of files, and the form data.
7. **Output (D16).** On success, every included file gets the result, the
   report, the time, the user, the scope, and links to the huf Agent Run and
   the prompt template. `custom_qc_check_count` goes up by one. On failure
   (provider error, timeout, output that does not match the schema), the
   status is Failed with a short error, and the previous report stays
   visible.
8. **Tab.** A **Quality Check** tab on the process file shows status, result,
   when and by whom, scope, the report (Markdown rendered), the list of files
   checked and skipped, and the run count.
9. **Alert.** The user who clicked gets a realtime alert when the run ends,
   and an open form refreshes the tab.
10. **huf is optional at import.** `the_visaguy` imports huf only inside the
    job and the button check. Without huf installed, nothing else in
    `the_visaguy` changes and the button does not show.

### Configuration

| Where | Field | Type | Notes |
|---|---|---|---|
| **Visaguy AI Settings** (new single, `the_visaguy`) | `qc_agent` | Link Agent (huf) | The agent used for QC: provider, model, OCR, temperature are set on it in huf |
| | `qc_max_files` | Int | Default 60 |
| | `qc_max_total_mb` | Int | Default 100 |
| | `qc_include_sidebar_attachments` | Check | Default on (D5) |
| **Destination** (custom tab "AI", custom fields from `the_visaguy`) | `custom_ai_tab` | Tab Break | New tab after Accounts |
| | `custom_qc_prompt_template` | Link Agent Prompt (huf) | Blank = QC not available for this destination |

Prompt template versions: huf keeps versions of one template in the same
`prompt_group`, with `is_latest` on the newest. The job uses the latest
active version in the linked template's group, so an edit in huf applies on
the next run without changing the destination. The output records the exact
template and version used, and huf saves the system prompt in `Agent Run
Prompt Snapshot`.

Pilot setup: link the Schengen template on each Schengen destination
(Switzerland, France, Netherlands, Germany, Spain, Denmark, Norway, Greece,
Belgium, Italy, Malta, and the others the Schengen departments use). All 2026
process files have a `custom_destination` that matches a `Destination`
record (15,365 of 15,365), so the lookup always resolves.

### Fields on PF Process File (custom fields, "Quality Check" tab)

| Field | Type | Meaning |
|---|---|---|
| `custom_qc_tab` | Tab Break | Quality Check |
| `custom_qc_status` | Select: Not Checked / Processing / Completed / Failed | Read-only |
| `custom_qc_result` | Select: Passed / Issues Found / Could Not Check | From the agent |
| `custom_qc_issue_count` | Int | From the agent |
| `custom_qc_checked_on` | Datetime | Run end time |
| `custom_qc_checked_by` | Link User | Who clicked |
| `custom_qc_scope` | Select: This File / Group | D15 |
| `custom_qc_check_count` | Int | Runs that included this file; above 1 means rechecked |
| `custom_qc_started_on` | Datetime | For the 30-minute stuck rule |
| `custom_qc_prompt_template` | Link Agent Prompt | Template and version used |
| `custom_qc_agent_run` | Link Agent Run | huf run (tokens, cost, prompt snapshot) |
| `custom_qc_output` | Long Text (read-only, hidden) | Report Markdown |
| `custom_qc_files` | Long Text (read-only, hidden) | Files checked and skipped |
| `custom_qc_error` | Small Text | Last failure |
| `custom_qc_html` | HTML | Rendered tab view |

All fields are read-only in the form and written only by the QC code with
`db_set`.

### Structured output (Phase 1)

```json
{
  "result": "passed | issues_found | could_not_check",
  "issue_count": 0,
  "summary": "string",
  "report_markdown": "string",
  "unreadable_documents": ["string"]
}
```

The report itself is free Markdown, written as the destination template
asks (for example, issues grouped by applicant). Phase 2 can add a findings
list to the schema.

### Code layout (`the_visaguy`, module Quality Check)

```text
the_visaguy/quality_check/
  doctype/visaguy_ai_settings/
  context.py   # included files, form data, file sources, hashes, limits
  runner.py    # enqueue, huf call, schema check, db_set output, realtime
  api.py       # whitelisted: can_run, start (scope), status
public/js/pf_process_file_qc.js   # button, scope dialog, tab rendering
fixtures: custom fields on PF Process File and Destination
```

### Phase 1 tasks

1. ADR (see Planning status).
2. Install huf on `visa-tracker-test.localhost`; check package conflicts,
   worker queues and scheduler load.
3. Visaguy AI Settings, Destination AI tab field, PF Quality Check fields.
4. Context builder with tests: scope (this file / group), every source,
   labels, hashes, skips, limits.
5. Runner with tests: lock, Processing, huf call, schema check, output
   saved on every included file, Failed path, stuck rule, realtime.
6. Button, scope dialog and tab.
7. Schengen pilot: configure the agent and template, run on real past files,
   compare with the manual QC answer, tune the template.

### Phase 1 acceptance criteria

- On a Schengen primary with dependants, **Check QC** asks for the scope;
  "Primary and all dependants" puts every file in Processing, and when the
  run ends every file shows the same report, result and time.
- On a dependant, QC runs for that file only, with no dialog.
- A destination with no template shows no button.
- A deliberately wrong date of birth, passport number, or hotel date in a
  test file appears in the report with the right applicant.
- A second click while Processing is refused.
- A provider failure sets Failed, shows the error, and keeps the previous
  report.
- `workflow_state` and the process file's `modified` time do not change.
- The output links to the huf Agent Run and the template version used.
- With huf uninstalled, `the_visaguy` works and the button is hidden.

## Phase 2 — later (agreed earlier, not in Phase 1)

Recorded so they are not lost. Each needs a short owner review before work:

- **Findings with resolution:** a findings list in the schema, each marked
  Fixed / Not an issue / Open by a user, and a recheck that reports each
  earlier finding as resolved or not.
- **Run history DocType:** one record per run, for reports. Phase 1 keeps
  only the latest output on the file, plus the huf Agent Run history.
- **Automatic action completion (old D12):** complete a configured action
  when no issues are open. Not needed for Schengen (D17).
- **Reports and dashboards** in a new **Quality Check** workspace (D11),
  owned by `the_visaguy` (module Quality Check), visible to Operations Team
  Lead and Management Role (System Manager for setup). Content: QC
  coverage, delivered without QC, first-pass rate, issues by category,
  open issues, per-associate figures (Team Leads see their departments), and
  usage and cost (Management). Department scope uses the existing rule:
  `Employee.department` plus `Additional Operation Department`; Management
  sees all departments. Because the workspace is new and owned by
  `the_visaguy`, no `visaguy_crm` workspace file changes. Operations
  Associates see QC only in the process file tab.

## Current state (verified 2026-10-19 and 2026-10-23)

### How the team does QC today (owner report)

They download the file collection data as CSV and every document, upload
them to Claude or ChatGPT with a prompt (cross check data and documents, use
the latest issued Schengen visa, make hotel, flight, itinerary, cover letter
and application form agree for each person), then fix the file by hand.
There is no record of the check in VisaGuy.

### Data and documents

| Item | Location | Label |
|---|---|---|
| One process file per applicant | `PF Process File`. `custom_type` = Primary or dependant; the primary lists dependants in `custom_dependent_details`; a dependant points back by `custom_primary_process_file` | source-wired |
| Destination | `PF Process File.custom_destination` (Data) holds a `Destination` name (`visaguy_crm`, autoname by `destination`, tabs RPA and Accounts). 117 destinations | source-wired, data-observed |
| Form data | `FF File Collection.information` via `file_collection`; a separate lead collection via `custom_lead_file_collection` (always a different collection in 2026) | source-wired, data-observed |
| Applicant uploads | `FF File Collection.file_collection_file` → `FF Document.attach` | source-wired |
| Application form | `custom_application_form`, made by `visaguy_crm.server_scripts.rpa.generate_application_form` (RPA or PDF Filler); saved with `is_private=0` and also attached to the sidebar | source-wired |
| RPA Documents | `custom_rpa_documents` (Flight Tickets / Hotel Bookings); rows on 1,092 files in 2026; section shown only for RPA-enabled destinations and zones | source-wired, data-observed |
| Action rows | `PF Process File Action` with `custom_attach` (4 attachments ever); about 10% of rows Completed | data-observed |
| Sidebar attachments | Main place for cover letters and itineraries in 2025 (16,007 files); 1,930 in 2026, mostly the RPA form | data-observed |
| Cover letters and itineraries in 2026 | Almost none in VisaGuy (1 of each); probably kept outside VisaGuy | data-observed |

### Schengen scope

Departments `Operations - Schengen - T` (8,601 files in 2026), `- TQ`
(1,270) and `- TS` (216). Top destinations: Switzerland, France,
Netherlands, Germany, Spain, Denmark, Norway, Greece, Belgium, Turkey,
Italy, Malta. Turkey is not in the Schengen area but is handled by these
departments; it needs its own template or no template.

### huf (commit `69d65d8`, 2026-10-10)

huf is **not installed** on the bench.

| Capability | Evidence | Use |
|---|---|---|
| Agent with provider, model, OCR, temperature | `Agent` | Set in Visaguy AI Settings |
| Prompt templates with versions | `Agent Prompt` (`prompt_body`, `prompt_group`, `version`, `is_latest`, `is_active`) | Linked on Destination |
| Run with files, template and structured output | `huf.ai.agent_integration.run_agent_sync(agent_name, prompt, files=…, prompt_template=…, response_format=…)`; a passed template replaces the agent's instructions for that run only | Called by the QC job |
| Run log with tokens, cost and prompt snapshot | `Agent Run`, `Agent Run Prompt Snapshot` | Linked from the process file |
| Files | Images go to the model as images; PDFs and other files go through text or vision OCR | Scanned documents need the OCR model set on the agent |
| No-code Doc Event trigger | Reads Attach fields on the firing document only | Not enough: files sit behind links and on other files, so `the_visaguy` builds the context |
| Compatibility | `frappe >= 15`, `requires-python >= 3.10` | Matches the bench |

## Risks

- **Personal data to an AI provider.** Passports and visas go to the provider
  set in huf. This happens by hand today; now it is systematic. Choose a
  provider plan with no training on inputs and short retention, and record
  it in the ADR.
- **Public application forms.** The RPA output is saved with `is_private=0`.
  Outside this feature; recommend a separate fix.
- **Incomplete documents.** Prepared documents come only from the sidebar
  (D4). Cover letters and itineraries were rarely attached there in 2026, so
  the team must attach them before clicking **Check QC**. A Passed result
  covers only the files listed in the output; the tab shows the file count
  next to the result.
- **AI errors.** The agent can miss mistakes or report false ones. The
  report is advisory.
- **huf footprint.** `doc_events["*"]` hooks on every DocType (cached
  lookup), about 18 scheduler jobs, and large dependencies (litellm,
  chromadb, faiss, llama-index). Check on the test site first.
- **Large groups.** Many applicants and scanned PDFs can exceed the model
  context or job time. The limits in settings apply; the output lists what
  was skipped.
- **Missing files on `visaguy`.** The dev copy has no uploaded files on
  disk; end-to-end tests there need files copied by hand.

## Open questions

None for Phase 1. For Phase 2, the owner reviews the list in "Phase 2 —
later" before work starts.

## Completion notes
