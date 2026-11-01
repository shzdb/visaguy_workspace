# ADR-017: Process File Quality Check Runs a Pinned huf Agent from `the_visaguy`

## Status

Accepted (2026-11-02). Implementation: TASK-048 (FEAT-006 Phase 1),
`the_visaguy` branch `feat/process-file-qc`.

## Context

Operations check each visa file by hand before delivery: they download the
file collection data and every document, upload them to an external AI chat,
and fix what it reports (FEAT-006). The owner wants this inside the process
file, using huf (tridz-dev/huf), without operations opening the huf UI.

Facts that shape the decision (verified 2026-10-23):

- huf `v1.0.0-beta.4` (`c82da78`) is installed on the dev bench, on sites
  `visaguy` and `visa-tracker-test.localhost`. The checkout tracks `develop`,
  so a `bench update` would move it past the tag.
- huf's no-code Doc Event trigger reads Attach fields of the firing document
  only. QC documents are behind links (`FF File Collection File.document` →
  `FF Document.attach`), in other DocTypes, and on dependant process files.
- `run_agent_sync` queues by default (default queue, 600-second timeout) and
  returns before the model answers, unless `now=1` is passed.
- `run_agent_sync` sends only image files to the model. PDFs and other
  documents in `files` are ignored; huf's own automations read them first
  with `huf.ai.ocr_engine.extract_document` and add the text to the prompt.
- With `Agent.persist_conversation` on, every call reuses one conversation,
  so each run would carry earlier runs' messages.
- huf is under active development; later releases may change these APIs.

## Decision

1. **Code home.** The quality check is a new module **Quality Check** in
   `the_visaguy` (`the_visaguy/quality_check/`). huf is not a required app:
   no module imports huf at load time. Without huf, or without a migrate,
   the button does not show and nothing else changes.
2. **Pinned huf.** The check runs only on huf versions listed in
   `huf_adapter.SUPPORTED_HUF_VERSIONS` (today `1.0.0-beta.4`). Every site,
   live included, checks out that tag and runs `bench exclude-app huf`. A huf
   upgrade is a tested change: test site first, then add the version to the
   list, then live.
3. **One adapter.** All huf calls go through `quality_check/huf_adapter.py`:
   version check, agent validation, prompt template resolution, document
   text extraction, the run, and linking the Agent Run to the process file.
4. **Context built in VisaGuy.** `the_visaguy` collects the data and files
   (both file collections, the application form, RPA Documents, action
   attachments, sidebar attachments), removes duplicates by content hash,
   applies count and size limits, reads non-image documents with huf's
   `extract_document`, and sends images as files.
5. **Run inside our job.** A Check QC click marks the files Processing and
   enqueues one job on the `long` queue. The job calls `run_agent_sync` with
   `now=1`, so the model runs inside that job.
6. **Agent rules.** The QC agent is set in **Visaguy AI Settings**. Saving the
   settings, and every run, refuse an agent that is disabled or has
   Persist Conversation on.
7. **Prompts.** Each Destination links one huf `Agent Prompt` (custom field
   `custom_qc_prompt_template`); the latest active version of its
   `prompt_group` is used. Rules that must not vary (use only the given
   documents, refer to documents by key, do not guess) and the JSON schema
   (`response_format`) are in code, so a template edit cannot change the
   answer's shape.
8. **Results on the process file.** The latest result is written with
   `frappe.db.set_value` on every file in the check: no process file save
   hooks run and the workflow is untouched, but `modified` and `modified_by`
   change, so a checked file moves up in lists sorted by last update (owner,
   2026-10-23). The tab reloads an open form only when it has no unsaved
   edits, and Check QC asks the user to save first.
   History is the huf Agent Run log plus the check count; a run history
   DocType is FEAT-006 Phase 2.
9. **Who may run a check (owner, 2026-11-02).** The job runs as the user who
   clicked; there is no service user. huf requires `Agent Run` create
   permission and agent access for that user, so:
   - patch `the_visaguy.patches.v1_0.grant_huf_user_role` gives **Huf User**
     to every enabled desk user (258 on `visaguy`). Users created later need
     it added by hand;
   - the QC agent's Allowed Roles are `Operations Associate` and `Operations
     Team Lead`;
   - `start_check` checks both at the click, before any OCR is spent.
   Agent Runs therefore belong to the real user. Everyone with Huf User can
   open the huf UI; the owner accepted this.
10. **Data sent out.** Form data and documents of the checked applicants
   (passports, visas, bookings, letters) go to the AI provider configured on
   the huf agent. The owner chooses the provider; use a plan with no
   training on inputs and short retention.

## Consequences

### Positive

- Operations never leave the process file and never handle downloads.
- A huf upgrade cannot silently break QC: the job stops with a clear error.
- Template edits in huf apply on the next run without a deploy.
- The workflow and process file save hooks are untouched.

### Negative

- Every desk user gets the Huf User role and can open the huf UI.

- The QC context and OCR handling duplicate a little of what huf
  automations do, because huf's trigger cannot reach linked documents.
- A long OCR or model call holds a `long` worker for the whole run.
- Personal data now goes to the AI provider on every check, not only when a
  person chooses to paste it.
- Pinning means huf fixes arrive only through a deliberate upgrade.

## Alternatives considered

- **huf Doc Event automation on a workflow state.** Rejected: it cannot
  read documents behind links or on dependant files, and the owner chose a
  button over a workflow change (FEAT-006 D1).
- **huf custom tool that fetches the documents.** Rejected for Phase 1: tool
  results are text, so images would still need OCR, and the agent would
  decide what to fetch.
- **Queue-first `run_agent_sync`.** Rejected: the result arrives later on
  another queue with a 600-second limit, and VisaGuy would need a callback
  to save it.
- **Separate huf bench called by API.** Rejected: files would have to leave
  the server twice, and an API key would be needed.

## Revisit when

- huf releases a version VisaGuy wants (re-test, then extend
  `SUPPORTED_HUF_VERSIONS`).
- huf's triggers can read linked documents, or `run_agent_sync` reads PDFs
  itself.
- FEAT-006 Phase 2 adds per-issue findings and a run history.
