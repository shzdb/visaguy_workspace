# QC document selection implementation plan

Status: **accepted plan; not implemented or runtime-verified**. Owner discussion:
2026-11-04. Feature: FEAT-006. Decision:
[ADR-018](../../../decisions/ADR-018-qc-document-selection.md). Implementation:
[TASK-049](../../../tasks/ready/operations-quality-check/TASK-049-qc-document-selection.md).

## Objective and boundaries

Operations choose which documents QC uses before the first check or any recheck.
Template defaults reduce repetitive deselection; saved document choices survive
uploads and subsequent runs. QC remains advisory and does not change workflow.
Structured form answers from both collections remain included: excluding a file
does not exclude form data. HUF receives only the selected, validated documents
through the existing adapter; no HUF change or version upgrade is required.

This document extends Phase 1, not the deferred Phase 2 findings workflow.
The scope is schema, copy/preservation paths, selection UI, batched reads, run
snapshots, reporting and validation. Dedicated queues, OCR caching and a full
run-history DocType remain separate follow-ups.

## Source evidence and technical verification

Read-only source review on 2026-11-04:

| Repository / ref | Evidence | Verification |
|---|---|---|
| `shzdb/visaguy_workspace/main` at `b965b5b` | Existing FEAT-006, TASK-048 and ADR-017 | present |
| `tvgglobal/the_visaguy/main` at `e196be0` | `quality_check/context.py`, `runner.py`, `api.py`, `huf_adapter.py`, `public/js/pf_process_file_qc.js` | source-wired |
| `tridz-dev/visaguy_crm/main` at `f960e94` | `hooks.py`, `data_collecting_form.py`, `file_collection_rows.py`, rejection and collection-creation functions | source-wired |
| `tridz-dev/huf` tag `v1.0.0-beta.4` at `c82da78` | Existing pinned adapter contract | source-wired |
| `tridz-dev/FileFlo` | Connected GitHub reads returned 404 | not verified |

These are review baselines, not claims about deployed revisions. Re-read current
application source before implementation. No live provider calls were made.

CRM hooks override `fileflo.data_collection.fetch_form_data`,
`fileflo.data_collection.add_form_data` and form generation. Upload/rejection
replacement rows use `FileRowFactory`. Its truthy inheritance fallback cannot be
reused unchanged for a boolean: explicit zero must survive a template value of one.
Lead and process collection creation directly import and call
`fileflo.document_fetch.document_fetch`. A whitelisted-method override does not
intercept those direct Python calls. Trace that exact initial-copy implementation
before coding; do not claim the hook alone covers it. Extend the existing seam
or initialize new collection rows in the CRM creation paths. Any helper invoked
from CRM must be optional/guarded when `the_visaguy` or its fields are absent;
do not make generic FileFlo depend on VisaGuy. Verify every creation entry point.
No new product decision is needed for this source trace.

## Schema ownership and persistence

**All new fields and the new child DocType belong to `the_visaguy`, module
Quality Check**, including custom fields on DocTypes owned by other apps.
Use Export Customizations in `the_visaguy/quality_check/custom/` with
`sync_on_migrate: 1`; do not add fixtures. The child DocType uses normal JSON and
controller files under `quality_check/doctype/`.

| DocType | Proposed field | Behaviour |
|---|---|---|
| FF File Template File | `custom_exclude_from_quality_check` (Check, default 0) | Per-document default copied only during initial collection creation |
| FF File Collection File | Same Check | Stored choice for that collection row, for either lead or process collection |
| RPA Documents | Same Check | Stored choice for the row attachment |
| PF Process File Action | Same Check | Stored choice for `custom_attach` |
| PF Process File | `custom_manage_qc_documents` (Button) | Inside Quality Check tab, opens modal; no additional toolbar button |
| PF Process File | `custom_qc_document_selection` (Table: QC Document Selection) | Explicit choices for sources without a row checkbox |

Suggested QC Document Selection columns: source doctype, source record name,
File ID, content hash, exclude flag. Its parent is the applicant's process file.
Keep an explicit include (exclude=0) when needed to override a default such as
the sidebar setting. Store only explicit choices, not a second inventory of all
files. Preserve source provenance and enforce unique logical source/file entries.

The Table field is not permanently Hidden and does not get a higher permission
level. On form refresh, JavaScript shows it only to `Administrator` or users with
`System Manager`; all other users manage choices through the modal. This is UI
visibility, not an API confidentiality boundary. Backend authorization is required.

| Source | Selection storage |
|---|---|
| Lead/process collection uploads | Collection row checkbox |
| RPA Documents / action attachments | Corresponding child-row checkbox |
| Application form | QC Document Selection on the applicant's process file |
| Process-file sidebar | QC Document Selection on the applicant's process file |
| Own or primary's Process Deliverables attachments | QC Document Selection on the applicant's process file |

Template edits never rewrite previously generated collection choices. Existing
collection and attachment rows start included (new checkboxes default 0); do not
backfill today's template exclusions into them. Existing sidebar choices start
from `qc_include_sidebar_attachments`, now a default, not a hard prohibition.

## Selection lifecycle and duplicate rules

1. New collection slots copy their matching template-row default once. A template
   with several document types has independent defaults per row.
2. Single upload, multi-upload expansion, remaining slots, rejection and re-upload
   preserve the stored collection-row value, including explicit 0. New additional
   documents inherit an existing slot/group choice when one exists; a genuinely
   new additional-document group starts included. Customer request data cannot
   set or override these internal QC flags.
3. The modal displays one logical document per applicant using stored content
   hash, falling back to File identity/URL when unavailable. Retain all source
   occurrences. No content read is needed to compute a fresh hash for the modal.
4. Explicit modal choices take precedence over defaults and apply across every
   duplicate source path for that applicant. When duplicate row defaults conflict
   and no explicit override exists, exclusion wins. Display the reason and allow
   inclusion. This prevents a sidebar duplicate bypassing a row exclusion.
5. Saving a logical document updates its eligible source-row flags and any
   necessary process-file choices in one transaction. Templates are never edited.
   A collection-row choice is shared by every QC reading that same row; this is
   intentional. Do not introduce a second collection override layer.
6. Shared primary deliverables retain applicant-specific choices: excluding the
   primary's itinerary for a dependant must not change the primary's setting.
   `shared` in the response is display metadata for this provenance, not an update
   instruction or persisted exclusion flag.
7. In group QC, identical selected content is sent once but retains all selected
   applicant/source associations. Exclusion by one applicant cannot remove a
   document another included applicant selected. It must not be attributed as
   selected for the applicant that excluded it.
8. Row-backed exclusion survives replacing its uploaded file. File-specific
   process choices are keyed to source plus file identity/hash: a new/replaced
   sidebar or deliverable file uses its default, not an unrelated old choice.
   Deleted sources are ignored/pruned safely. Missing/unreadable files remain
   visible with their condition; they are not silently presented as checked.

## Desk experience

- Use `frappe.ui.Dialog`, native field definitions and tabs, standard search and
  scope controls, and a compact custom document list in an HTML field per tab.
  No separate React/Vue frontend. Escape user-provided labels, constrain preview
  URLs to validated file URLs and keep selection state explicitly in JavaScript.
- The Button field is available on saved process files to authorized QC roles
  before the first QC. Managing selections does not require a previous report,
  a configured provider/agent, or a successful QC run. Starting a run keeps the
  existing HUF/destination availability checks.
- Require the process file to be saved before opening the modal. Show loading,
  error/retry and no-documents states. Cancel discards unsaved modal changes.
- Applicant tabs show selected/total counts. Opening from a primary exposes the
  permitted primary/dependant set; opening from a dependant manages that applicant
  and its eligible primary deliverables. Tab navigation is not run scope.
- Scope is explicit: this applicant or primary and all dependants, matching the
  existing This File/Group runner contract. Do not add arbitrary applicant subsets.
- Each row shows include checkbox, document label/name, source, size and preview;
  shared deliverables show a Shared document badge. Excluded rows remain visible
  unchecked, with a reason. Search, selected/excluded filters and per-applicant
  select/deselect controls operate without extra network calls. Filters do not
  silently change hidden selections.
- Footer shows selected documents/applicants and size, with Save and Save & Run QC.
  Save & Run validates/saves and starts in one server transaction; a failed start
  does not partially save. Disable duplicate submits and retain edits on error.
- A zero-document selection can be saved, but no run can start with zero selected
  documents. A group applicant with none selected is shown explicitly; included
  structured form data remains in scope and the report must not imply that
  applicant's documents were checked.
- Check/Recheck reuses saved choices without requiring the modal each time.
  Selection changes retain the previous report and display that it covers an
  earlier document selection. Do not mark an advisory result as current for a
  different selection.

## Backend contract and concurrency

`documents.py` owns `load_inventory`, `resolve_selections`, `save_selection` and
`create_run_snapshot`; `context.py` supplies batched source reads and form data.
`api.py` exposes get-documents, POST save-documents and save-and-start, alongside
the existing start-check entry point. These are proposed names, not existing APIs.

The inventory response contains applicant IDs/labels, opaque stable document keys,
labels, authorized file URLs, sizes, sources, included state, reason and shared
display metadata, plus an inventory revision. Stable keys are not filenames,
array indexes or the D1/D2 labels assigned within a run.

Writes accept changed keys and include booleans plus the expected revision.
Rebuild/validate the allowed source set server-side; do not accept arbitrary
doctypes, record names or URLs as update authority. Reject stale inventory or
selection revisions with a refresh message. Check role, process-file access,
every affected applicant and source parent, including primary deliverables.
Keep get/save behind the existing QC roles (Operations Associate, Operations
Team Lead, System Manager), with actual record access checked separately.
If normal source write permission is unavailable, reject that save clearly;
do not blanket bypass parent permissions. All changes are atomic and attributed
to the requesting user. Direct field writes must also enforce membership and
avoid exposing unrelated records.

At start, snapshot selected file references, identities/hashes, exclusions and
applicant/source associations; capture structured form data too so queued input
does not drift. Persist the snapshot durably with the job/result metadata (for
example a hidden server-owned Long Text field in the same module); do not rely
solely on browser state or Redis job arguments. Version the snapshot, record its
selection fingerprint, and tie worker completion to the active run token so an
older restarted job cannot overwrite a newer run.

The worker processes this saved snapshot without rediscovering the full graph.
It revalidates referenced files and rejects/skips changed, deleted or inaccessible
files with an explicit reason, never substituting a newer file silently. Apply
exclusions before disk reads, OCR and size/count limits. Keep existing supported
HUF version checks, provider authorization, schema parsing, advisory workflow,
result writes and realtime behaviour. Preserve snapshot metadata on success and
failure so the last report remains interpretable.

Output distinguishes deliberately excluded, selected/sent, missing, unreadable
and over-limit documents. A duplicate is an association, not a second OCR input.
The report lists its actual scope and documents, rather than equating a passed
answer with validation of excluded files. Compare current selection fingerprint
to the completed snapshot when showing the stale-selection notice; a later UI
save must not relabel an in-flight snapshot.

## Read scalability

One metadata request initially loads the permitted group. Batch source reads by
collection IDs, process-file IDs, FF Document IDs, deliverable IDs and File
IDs/URLs. Select required fields rather than full documents in per-row loops.
Keep identity maps for lookups and preserve deterministic ordering/provenance.
Authorization checks must not be removed to improve query counts.

The modal does not extract text, open files on disk, download content, or call HUF.
Use stored sizes/hashes; preview loads only when requested. Tabs and filters reuse
the response. Fresh validation occurs on save/start; avoid a long-lived inventory
cache and its cross-source invalidation problems. Lazy tab loading is a measured
follow-up if realistic metadata payloads justify it.

The worker bulk-loads selected File metadata and reads each unique selected file
once. Record query counts, payload size and load time for representative single
and family cases. Query growth should be by source batches, not by document count
(except justified permission checks), with no per-file metadata query loop.
Inspect existing indexes and EXPLAIN before adding an index; don't index boolean
exclusion fields speculatively. OCR/provider time is measured separately from
inventory queries. OCR caching by hash plus extraction configuration/version and
a dedicated QC queue remain follow-ups, not prerequisites.

## Delivery sequence and validation

1. Re-read app instructions/current heads; trace initial-copy and every upload,
   expansion and rejection entry point. Use a test site and isolated branches.
2. Add schema/customizations in `the_visaguy`; migrate the test site. Confirm
   existing choices start included and a second migration is idempotent.
3. Add guarded copy/preservation logic at the existing CRM seams; test with
   `the_visaguy` absent as well as installed. No accidental hard dependency.
4. Implement batched inventory, duplicate rules, atomic save and concurrency checks.
5. Build the Button field handler and dialog, role-based table visibility and
   shared badges. Wire both assets without changing existing QC rendering.
6. Wire start paths to durable snapshots, worker fencing and reporting; verify
   saved selection reuse from the existing Check/Recheck button.
7. Run automated tests and browser checks below; document query/payload timings.
8. Publish application PRs with schema and dependent CRM changes linked. Deploy
   compatible code together, migrate, build affected assets and restart workers
   as required. Do not enable a partial deployment that drops exclusions.

Required tests: per-template-row initial defaults; no retroactive template edits;
explicit 0 inheritance; existing rows; single/multi upload, remaining slots,
additional uploads, rejection/re-upload; every source; duplicate sidebar bypass;
conflicting defaults; shared primary/dependant choices and group deduplication;
deleted/replaced files; permission denial and forged IDs; stale and simultaneous
saves; rollback; no-document run prevention; form-data retention; queue snapshot
stability, worker replacement detection and stale-job fencing; prior-report
retention/staleness; count/size limits and OCR failures; absent HUF and absent
VisaGuy fields in generic CRM paths.

Browser checks: first-ever QC, primary/dependant tabs, counts, filters, preview,
shared badges, excluded files reselected, Save/Cancel/Save & Run, unsaved form,
refresh conflict, loading/error states, ordinary operations versus admin table
visibility, and realtime completion. Preserve keyboard usability and reasonable
layout for long filenames and multiple applicants.

Rollback: stop new starts/drain queued snapshot jobs before reverting incompatible
runner code. Prefer additive schema retention. Old runner code includes all files;
reverting to it silently would violate saved exclusions, so disable QC until the
selection-aware code is restored. Restore normal QC only after checking schema,
assets, worker revision and the pinned HUF compatibility.

## Completion evidence

Record application commits/PRs, test-site migration and browser results, performance
measurements and limitations here and in TASK-049. Planning does not mark TASK-048
or this extension implemented. Tasklane CLI/integration was unavailable in this
planning environment; synchronize the accepted specification and task to the
project's shared Tasklane record when that integration is available.
