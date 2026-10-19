---
id: FEAT-006
title: AI quality check for process files (huf)
status: planned
priority: medium
repositories:
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

## Summary

Before operations deliver a visa file, a person checks that the data in the
file collection, the applicant's uploaded documents, and the documents that
operations prepared (the RPA application form, hotel bookings, flight
reservations, itinerary, cover letter) all agree. Today they do this by hand
in an external AI chat. This feature moves that check into the process file.
A new workflow state starts a huf agent in the background. The agent gets the
data and documents of every applicant in the group, and it returns findings.
The findings show in a **Quality Check** tab on the process file. The
workflow then moves to a review state. Operations users do not open the huf
UI.

## Current state (verified 2026-10-19)

Evidence comes from source on the erpcode bench and from read-only counts on
the `visaguy` development site (a database copy of live, latest process file
2026-10-05). Counts are production estimates, labelled **data-observed**.

### How the team does QC today (owner report, not verified in code)

1. Download the file collection data of the process file as CSV.
2. Download every applicant upload and every prepared document.
3. Upload all of them to Claude or ChatGPT with a prompt such as: cross check
   the data against the documents, use the latest issued Schengen visa in the
   application form, make sure hotel vouchers, flight reservations and the
   itinerary agree, make sure dates and personal data on the cover letter and
   application form agree, and flag errors or points that need more clarity
   for each person.
4. Read the answer and fix the file by hand.

There is no record of the check in VisaGuy: no result, no reviewer, no list of
what was fixed.

### Where the data and documents live

| Item | Location | Label |
|---|---|---|
| One process file per applicant | `PF Process File` (`processflo`); `custom_type` = Primary or dependant; the primary lists dependant files in `custom_dependent_details` (`Dependent Process File Details.process_file`); a dependant points back by `custom_primary_process_file` | source-wired |
| Applicant form data | `FF File Collection.information` (`FF File Collection Data`: `field_name`, `value`, `group_name`, `field_id_link`), linked by `PF Process File.file_collection`; a lead-level collection is linked by `custom_lead_file_collection` | source-wired |
| Applicant uploads | `FF File Collection.file_collection_file` rows → `FF Document.attach`; row `status` is Uploaded / Completed / Rejected | source-wired |
| Applicant "additional documents" | FileFlo form uploads with `is_additional_documents` create extra `FF Document` rows (`file_type` Others) on the same file collection (`fileflo.data_collection.add_form_data`) | source-wired |
| RPA application form | Button **Generate Application Form** → `visaguy_crm.server_scripts.rpa.generate_application_form`. It posts the `information` table as CSV (RPA) or JSON (PDF Filler), plus mapped files, to the URL in `TVG CRM Settings`, and saves the returned PDF in `PF Process File.custom_application_form` | source-wired |
| Hotel bookings and flight tickets | `PF Process File.custom_rpa_documents` (`RPA Documents`: `document_name` Select = Flight Tickets / Hotel Bookings, `attachment`). They are also inputs to the RPA call | source-wired |
| Itinerary and cover letter | **No dedicated field in source, and in 2026 almost none are in VisaGuy.** In 2025 they were sidebar attachments (by file name: 1,806 cover letters on 1,463 files, 1,248 itineraries on 1,065 files). In 2026, 5,921 files reached Documents Delivered or Completed, but the sidebar holds 1 cover letter and 1 itinerary, and `FF Document` holds none. Action row `custom_attach` is used 4 times in total. They are probably kept outside VisaGuy (an action named "Drive Upload" exists) | data-observed |
| Task list | `PF Process File.action` (`PF Process File Action`: `action`, `status` Pending / Completed, `custom_attach`, `custom_appointment_date`). 19,557 of 196,821 rows are Completed, which matches the owner report. Templates already have a **Quality Check** action (5,109 rows, plus variants such as "QUALITY CHECK (INTERNAL) & SUBMISSION") | data-observed |
| Workflow | `Process File Workflow` (fixture in `visaguy_crm`): Unassigned → Assigned → Inprogress → Documents Delivered → Completed, plus Hold and Rejected. No QC state | source-wired |

Correction to the brief: the prepared documents are not in a field named
"Additional documents". In 2026:

- The application form is in `custom_application_form` (1,724 files). The
  same PDF is also a sidebar attachment, because `save_file` attaches it to
  the process file.
- Hotel bookings and flight tickets are in the **RPA Documents** table (rows
  on 1,092 process files; 1,095 Hotel Bookings and 1,084 Flight Tickets rows
  in total).
- The cover letter and itinerary are not stored on the process file at all.
- "Additional Documents" is a FileFlo upload group for the applicant's own
  extra files (23,247 in 2026). Schengen visa copies are in groups such as
  "Copy of Schengen Visa" and "Copy of Previous Schengen Visa".

So the QC cannot check the cover letter and itinerary until operations upload
them into the process file. This is a prerequisite (see Requirement 0 and
open question 1). Only about 1 in 5 delivered files in 2026 has RPA
Documents, so the same applies to hotel and flight documents on most files.

### huf (commit `69d65d8`, 2026-10-10)

huf is **not installed** on the bench. Its source shows:

| Capability | Evidence | Use here |
|---|---|---|
| Agent with provider, model, instructions, OCR, temperature, reasoning settings | `Agent` DocType | Holds the QC prompt and the model choice. Admins change them in huf without a deploy |
| Python entry point with files and structured output | `huf.ai.agent_integration.run_agent_sync(agent_name, prompt, files=…, response_format=…)` | The VisaGuy side calls this |
| Run log with reference document, status, response, tokens, cost | `Agent Run` (`reference_doctype`, `reference_name`, `response`, `total_tokens`, `cost`) | Audit and cost per QC run |
| Images go to the model as images; PDFs and other files go through text or vision OCR first | `providers/litellm.py` `_file_dict_to_data_image_url`; `ocr_engine.extract_document` | Scanned passports and visas need the OCR model set on the agent |
| No-code Doc Event automation with a condition and file fields | `Automation` + `Automation Trigger` (`file_attachments`: DocField or Child Table Field) | **Not enough alone**, see below |
| Compatibility | `frappe >= 15`, `requires-python >= 3.10` | Matches the bench (Frappe 15.113, Python 3.10.12) |

Why the no-code Doc Event trigger is not enough: it reads only Attach fields
on the document that fired, or on that document's child tables. The QC needs
(a) form data from another DocType (`FF File Collection`), (b) files reached
through a link (`FF File Collection File.document` → `FF Document.attach`),
and (c) the same for every dependant process file. So a small VisaGuy-side
adapter must collect the context and call huf.

## User value

- Operations do not download and upload files to an external portal.
- Every file gets the same check, with the same prompt, before delivery.
- Findings stay on the process file with who fixed what, so team leads can
  audit QC and see repeat mistakes.
- Admins change the prompt or the model in huf without a code deploy.
- Cost and token use per file are recorded.

## Scope

### Included

- New workflow states for QC on `Process File Workflow`.
- A background QC run when a primary process file enters the QC state.
- A context builder that collects data and documents for the primary and
  every dependant.
- One huf agent for QC, called through `run_agent_sync` with structured
  output.
- A QC result record with findings, and a **Quality Check** tab on the
  process file that shows the latest result, the history, and a re-run
  button.
- Automatic move to the review state when the run ends, and a realtime alert
  to the designated user.

### Excluded

- Automatic correction of data or documents. The agent only reports.
- Automatic approval or delivery. A person always decides.
- Changes to the RPA service or the PDF Filler service.
- QC for files that do not follow the process file workflow.
- Operations access to the huf UI.

## Requirements

0. Every prepared document has a named slot on the process file. Add
   **Cover Letter**, **Itinerary** and **Travel Insurance** to the `RPA
   Documents.document_name` options (or rename the table to Prepared
   Documents). **Send to QC** is blocked until the application form, hotel
   booking, flight reservation, itinerary and cover letter are present. The
   list per destination is open question 1.
1. An Operations Associate or Team Lead moves a primary process file from
   **Inprogress** to **Quality Check** with action **Send to QC**.
2. The QC run starts after the transition commits, in the `long` queue. The
   form shows "QC running" at once.
3. The context covers the primary and every dependant in
   `custom_dependent_details`. For each applicant it includes the form data,
   applicant uploads, the application form, the RPA Documents, and the
   confirmed itinerary and cover letter source.
4. Each file is labelled with applicant, source, and document name, so a
   finding can point to it.
5. Files missing on disk, unsupported, or over the size limit are skipped and
   listed in the result as "not checked". A run with skipped mandatory
   documents cannot have the verdict Pass.
6. The agent returns JSON that matches a fixed schema (see Proposed design).
   A response that does not match is a failed run.
7. When the run ends (success or failure), the process file moves to **QC
   Review** and the designated user gets a realtime alert.
8. In QC Review, a user marks each finding **Fixed**, **Not an issue**, or
   **Open**, with an optional remark. The user and time are recorded.
9. From QC Review the user can move to **Documents Delivered** or back to
   **Inprogress**, or start a new run. Each run is kept; the tab shows the
   latest first. Moving to Documents Delivered marks the existing **Quality
   Check** action row Completed, if the template has one.
10. Only one run per group can be Queued or Running at a time.
11. Roles that can read the process file can read its QC results. Only
    Operations roles can run QC or change finding status.

## Proposed design

### Flow

```text
Inprogress ──Send to QC──▶ Quality Check ──(run ends, system)──▶ QC Review
                               │                                   │
                       enqueue QC job                    ├─Documents Delivered─▶ …
                               ▼                         ├─Back to In Progress─▶ Inprogress
   build context (primary + dependants)                  └─Run QC again──────▶ Quality Check
                               ▼
   huf run_agent_sync(agent="Process File QC",
                      files=[…], response_format=QC schema)
                               ▼
   save Process File QC Run + findings, link Agent Run
```

### Components

1. **Workflow change** (`visaguy_crm` workflow fixture). Add states
   *Quality Check* and *QC Review*. Add transitions: Inprogress → Quality
   Check (Associate, Team Lead); QC Review → Documents Delivered; QC Review →
   Inprogress; QC Review → Quality Check; Quality Check → QC Review (allowed
   only for a QC service role, used by the job). Add Hold transitions to
   match the other states. Condition on Send to QC: `doc.custom_type ==
   "Primary"`.
2. **QC adapter** (new code; home is open question 3). It has:
   - a `on_update` hook on `PF Process File` that enqueues the job when
     `workflow_state` changes to Quality Check (after commit, same pattern as
     visa tracking);
   - a **context builder** that returns a text manifest (form data per
     applicant as `label: value` lines, grouped as in the file collection)
     and a file list in huf's `files` format (`file_id`, `file_url`,
     `filename`, `is_image`);
   - a **runner** that calls `run_agent_sync` as the QC service user, checks
     the JSON, saves the result, and applies the QC Review transition.
3. **huf configuration** (data, not code): AI Provider with the API key, an
   Agent "Process File QC" with the model, the OCR setting, low temperature,
   and the instructions below. Keep it as a fixture or a documented setup
   step so test and live match.
4. **Result DocTypes**:
   - `Process File QC Run`: `process_file` (primary), `status` (Queued /
     Running / Completed / Failed), `verdict` (Pass / Issues found / Could
     not check), `summary`, `agent_run` (Link Agent Run), `model`, `cost`,
     `total_tokens`, `files_checked`, `files_skipped` (text list),
     `triggered_by`, `started_at`, `finished_at`, `error`, `result_json`,
     `findings` (child table).
   - `Process File QC Finding` (child): `severity` (Error / Warning /
     Clarify), `applicant`, `topic` (for example "Date of birth"),
     `documents` (labels from the manifest), `expected`, `found`,
     `explanation`, `resolution` (Open / Fixed / Not an issue),
     `resolved_by`, `resolved_on`, `remark`.

   Results are a separate DocType, not a child table on the process file.
   Saving the process file fires many hooks (tracking sync, visa centre sync,
   refetch of missing fields, timers) and adds a version row. A separate
   record keeps history and does not race with a user who edits the file.
5. **Quality Check tab** on `PF Process File`: a Tab Break and an HTML field
   (custom fields), filled by client script from a whitelisted method. It
   shows the verdict, summary, findings grouped by applicant with resolution
   controls, skipped files, run history, cost, and a **Run QC again**
   button. No huf screen is needed.

### Agent instructions (draft, to refine with operations)

Base the instructions on the operations prompt and make the rules explicit:

- Compare every applicant's form data with the passport, the latest issued
  Schengen visa, the application form, the cover letter, the itinerary, the
  hotel vouchers and the flight reservations.
- Use the latest issued Schengen visa for previous-visa questions in the
  application form.
- Check that travel dates, cities and names agree across hotel, flight,
  itinerary, cover letter and application form, for every applicant.
- Report a finding only with the document labels that show it. Say "not
  readable" when a document cannot be read. Do not guess values.
- Return only JSON that matches the schema.

### Structured output (draft schema)

```json
{
  "verdict": "pass | issues_found | could_not_check",
  "summary": "string",
  "findings": [
    {
      "severity": "error | warning | clarify",
      "applicant": "string",
      "topic": "string",
      "documents": ["string"],
      "expected": "string",
      "found": "string",
      "explanation": "string"
    }
  ],
  "unreadable_documents": ["string"]
}
```

## Tasks

Draft only. No task can be `ready` until the open questions below have
answers and the proposed ADRs are accepted.

1. Prepared document slots: new RPA Documents options and the Send to QC
   precondition (Requirement 0), after open question 1 is answered.
2. ADR: huf placement and the code home of the QC adapter.
3. Install huf on `visa-tracker-test.localhost`; check dependency conflicts,
   worker queues and scheduler load.
4. Workflow states and transitions; check the consumers listed under Risks.
5. Result DocTypes and permissions.
6. Context builder with tests (group expansion, file labels, skip rules).
7. Runner: huf call, schema check, save, transition, realtime alert, one
   active run per group.
8. Quality Check tab and finding resolution.
9. Pilot on one destination with real past files; compare with the manual
   QC result; tune the prompt.

## Acceptance criteria

- Moving a primary file to Quality Check produces a QC Run with findings and
  moves the file to QC Review, with no huf screen opened.
- The run covers every dependant in the group.
- A deliberately wrong date of birth, passport number, or hotel date in a
  test file is reported with the correct applicant and documents.
- Skipped or unreadable files are listed, and the verdict is not Pass when a
  mandatory document is skipped.
- Each finding can be marked Fixed or Not an issue, with user and time.
- The QC Run links to the huf Agent Run and shows tokens and cost.
- Visa tracking client status does not change because of the new states.

## Dependencies

- huf installed on the same site (recommended) or reachable by API.
- An AI provider account with a model that reads images and PDFs, and an OCR
  model for scanned files.
- Operations agree to upload every prepared document into the process file
  before QC (today the cover letter and itinerary are kept outside VisaGuy).

## Risks

- **Personal data to an AI provider.** Passports and visas go to the model
  provider set in huf. This already happens by hand today, but now it is
  systematic. Use a provider and plan with no training on inputs and short
  retention, and record the choice.
- **Public application forms.** `generate_application_form` saves the RPA
  and PDF Filler output with `is_private=0`, so the application form is a
  public file. This is outside this feature, but the QC adapter must not copy
  files to public URLs. Recommend a separate fix.
- **AI errors.** The agent can miss mistakes or report false ones. The check
  is advisory; a person decides. Track the share of findings marked Not an
  issue during the pilot.
- **huf footprint.** huf adds `doc_events["*"]` hooks on every DocType (the
  lookup is cached), about 18 scheduler jobs, and large Python dependencies
  (litellm, chromadb, faiss, llama-index). Check worker capacity and package
  conflicts on the test site before live.
- **Workflow consumers.** New states affect Insights queries and number cards
  that list states (for example `workflow_state NOT IN ('Completed',
  'Documents Delivered')`), department dashboards, and
  `completed_date_marking`. Visa tracking ignores unknown states (ADR-010),
  so client status does not change.
- **Large groups.** Many applicants and scanned PDFs can exceed the model
  context or the job timeout. Set file and page limits, and record what was
  not checked.
- **Missing files on `visaguy`.** The dev copy has no uploaded files on disk,
  so end-to-end tests there need files copied by hand.

## Open questions

1. Where do operations keep the cover letter and itinerary in 2026 (Google
   Drive?), and which prepared documents are mandatory per destination?
   Counts show they are not on the process file. (Recommendation: add named
   RPA Documents options, make the five core documents mandatory for Send to
   QC, and let a destination add or remove items later.)
2. Install huf on the same bench and site, or on a separate bench called by
   API? (Recommendation: same bench, same site. The adapter can then pass
   Frappe `File` records directly, and no file leaves the server except to
   the model provider. A separate bench needs file transfer and an API key.)
3. Which app holds the QC adapter and DocTypes: `visaguy_crm` (owns the
   process file workflow and RPA code), `the_visaguy`, or a new small app
   that depends on huf? (Recommendation: a new small app, so that huf stays
   an optional dependency of the core apps, as done for `passport_extractor`
   in ADR-004.)
4. QC for the whole group from the primary only, or per applicant?
   (Recommendation: from the primary only; dependants show a link to the
   primary's QC tab.)
5. Should the run end in one state (QC Review with a verdict field) or in
   two (QC Passed / QC Failed)? (Recommendation: one state. The verdict is
   advisory and a person chooses the next step.)
6. Is QC mandatory before Documents Delivered, or optional? If mandatory,
   remove the direct Inprogress → Documents Delivered transitions.
7. Which provider and model, and what monthly cost limit?
8. Should a failed run (provider error, bad JSON) go to QC Review with
   verdict Could not check, or stay in Quality Check with a retry?
   (Recommendation: go to QC Review, so the file is never stuck.)

## Completion notes
