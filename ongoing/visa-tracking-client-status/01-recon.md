# Client-facing visa tracking status — recon

Read-only reconnaissance for deriving the five client-facing visa tracking
stages automatically from `PF Process File` state. No code was written, no
migration run, no database row modified. All SSH commands were `SELECT` /
`SHOW` / `DESC` / `git log` / `grep` against the `visaguy` development bench
and its app checkouts (`~/bench/apps/*`, mostly on `feat/visa-tracker` or
similar feature branches — see per-repo notes below).

Evidence labels follow `AGENTS.md`: **present**, **source-wired**,
**configured-unverified**, **runtime-verified**.

## Summary table

| Stage | Recommended signal | Confidence |
|---|---|---|
| 1. Questionnaire Not Submitted | `PF Process File` exists AND its own `FF File Collection` (`file_collection`) has `form_submitted = 0` | Medium |
| 2. Questionnaire Submitted | that same `FF File Collection.form_submitted = 1` | Medium-High (mechanism proven; live incidence low) |
| 3. File Assigned | `PF Process File.workflow_state = "Assigned"` | High |
| 4. In Progress | `PF Process File.workflow_state = "Inprogress"` | High |
| 5. Completed | `PF Process File.workflow_state = "Documents Delivered"` | High |

Everything below is the evidence for each row, then the five specific
questions, then the Custom Field investigation, then unknowns/risks.

---

## Stage 1 — Questionnaire Not Submitted

**Recommended signal:** a `PF Process File` row exists, and the `FF File
Collection` reached via `PF Process File.file_collection` has
`form_submitted = 0` (or the collection cannot be found at all — see
Unknowns).

- **present** — `PF Process File.file_collection` is a native `Link` field to
  `FF File Collection`, defined in `processflo` itself:
  `processflo/processflo/processflo/doctype/pf_process_file/pf_process_file.json:42-46`.
- **source-wired** — the collection this field points at is exactly the
  "second FC" (questionnaire) the owner described. Proof is in the fork's own
  destination-change handler, which explicitly separates "1st FC" (Lead) from
  "2nd FC" (Process File) when regenerating: `visaguy_crm/visaguy_crm/server_scripts/lead/lead_hooks.py:291-296`
  (`pf_fcs = frappe.db.get_all("FF File Collection", filters={"reference_type": "PF Process File", "reference_name": pf}, ...)`, comment: `# For each pf_process_file, find its FF File Collections (2nd FC)`).
- **source-wired** — the collection is created at Process File creation time
  in `visaguy_crm/visaguy_crm/allocated_to_process_file.py:270-283`
  (`generate_file_collection_process_file(...)`, then
  `pf_process_file.file_collection = file_collection_name`).
- **runtime-verified** — relationship is strictly 1:1 in live data: every
  `PF Process File` referenced by `FF File Collection.reference_type =
  "PF Process File"` has exactly one such collection (3,862 process files,
  3,862 rows, max count per process file = 1). No ambiguity about "which
  collection is the questionnaire" — there is only ever one per Process File.
- **runtime-verified** — `custom_lead_file_collection` (the *first* form,
  passport-collection stage, reference_type `Lead`) is a **separate** field,
  populated on 3,846/3,866 rows, confirming the two forms are distinct fields
  and distinct collections, matching the owner's framing.
- **runtime-verified** — `file_collection` itself is populated on 3,851/3,866
  Process Files (99.6%); the small gap is backfilled defensively by
  `refetch_missing_fields` in
  `visaguy_crm/visaguy_crm/server_scripts/pf_process_file/pf_process_file_hooks.py:5-27`.

Confidence: **Medium** — the relationship and the field are solid
(source-wired + runtime-verified), but the fitness of `form_submitted` itself
as the truth signal is undermined by the low live incidence discussed under
Stage 2 and Question 2 below; that uncertainty is inherited by "not yet
submitted" as its inverse.

## Stage 2 — Questionnaire Submitted

**Recommended signal:** `FF File Collection.form_submitted = 1` on the
collection reached via `PF Process File.file_collection`.

- **present** — `form_submitted` is a **native** column on `FF File
  Collection` (`int(1) NOT NULL DEFAULT 0`), not a custom field — confirmed
  via `SHOW COLUMNS`. It is a real, persisted value, not a transient
  in-memory flag.
- **source-wired** — set at `visaguy_crm/visaguy_crm/data_collecting_form.py:342-345`:
  ```
  if document_name and form_submitted==1:
      ff_file_collection.form_submitted = 1
  ```
  inside the live `add_form_data` whitelisted endpoint (the fork used by the
  production form, per the workspace's prior finding — not `fileflo`'s
  original). This directly answers the "most important" question (Q2 below).
- **source-wired** — the same code block also sets a companion flag on the
  *parent* document (`Lead` / `CRM Lead` / `PF Process File`):
  `data_collecting_form.py:349-356` sets `doc.custom_form_submitted = 1` and
  saves it, when `reference_type` is one of those three. This is why a
  `custom_form_submitted` Check field exists on `PF Process File` itself
  (Custom Field, `read_only=1`, defined in
  `visaguy_crm/visaguy_crm/visaguy_crm/custom/pf_process_file.json:790-813`).
- **runtime-verified but weak** — live incidence of the ground-truth field is
  very low: of 3,862 `FF File Collection` rows with
  `reference_type = "PF Process File"`, only **18** have `form_submitted = 1`
  (3,844 are 0). By contrast the *derived* `PF Process File.custom_form_submitted`
  field is 1 on **2,710** of 3,866 rows (70%) — a **large, unexplained
  mismatch**: 2,692 Process Files show `custom_form_submitted = 1` with **no**
  matching `FF File Collection.form_submitted = 1` row at all (checked by
  join). No committed code path other than the one above writes
  `custom_form_submitted`, and the field is `read_only=1` on the form (not
  editable by ops), and Version history has only 3 tracked changes for it
  site-wide — far fewer than 2,710. See "Unknowns and risks" — this must be
  understood (most likely candidate: collections get deleted and recreated
  on destination change, per `lead_hooks.py`'s regeneration flow, which would
  strand the parent's flag from a now-deleted collection's flag, but this was
  not proven against a concrete example row) before `custom_form_submitted`
  or `form_submitted` can be trusted as the sole stage-2 gate.
- **runtime-verified** — a client script toggle exists confirming the
  product intent that submit and save are different states meant to be
  tracked: `custom_form_saved` (Check, also read_only) sits alongside
  `custom_form_submitted`; live counts show `custom_form_saved` is almost
  never used alone (4/3,866 non-zero combinations), so "saved but not
  submitted" is not currently a live-observed state on Process Files.

Confidence: **Medium-High on mechanism, Low on current live trustworthiness.**
The field exists, is real, and is written by the one code path that matters —
but the discrepancy above means a resolver reading `custom_form_submitted`
today would call ~70% of Process Files "submitted" while the more literal
source (`FF File Collection.form_submitted`) says <1% are. This is the single
biggest open question from this recon and should block finalizing Stage 1/2
resolution until explained (see "Unknowns and risks").

## Stage 3 — File Assigned

**Recommended signal:** `PF Process File.workflow_state = "Assigned"`.

- **present/configured-unverified→runtime-verified** — a real, active
  Frappe Workflow exists for `PF Process File`:
  `tabWorkflow` row `Process File Workflow`, `document_type = "PF Process
  File"`, `is_active = 1`, `workflow_state_field = "workflow_state"`.
- **runtime-verified** — states in order: `Unassigned → Assigned →
  Inprogress → Documents Delivered → Completed`, plus side states `Rejected`
  and `Hold`. Live distribution across all 3,866 Process Files:
  `Documents Delivered` 2,344, `Unassigned` 691, `Assigned` 596, `Inprogress`
  118, `Hold` 59, `Completed` 55, `Rejected` 3. All states are actively used,
  none is empty — this is a live-operated field, not dead config.
- **runtime-verified** — the transition into `Assigned` is `Unassigned →
  (Approve) → Assigned`, allowed role `Operations Team Lead`
  (`tabWorkflow Transition`, idx 3). This matches "file is with a specialist"
  semantically (a Team Lead approves the assignment).
- **runtime-verified — disproves the `custom_lead_visa_consultant` lead** —
  that field (candidate from the prompt) is populated on only **17 of 3,866**
  rows; it is essentially dead in practice. Do not use it.
- **runtime-verified — `custom_designated_to` is a better-populated
  alternative (3,172/3,866, 82%) but is strictly worse than `workflow_state`
  as the stage-3 signal**, because it is set well before the workflow moves
  out of `Unassigned`: even within `workflow_state = "Unassigned"`, 55/691
  rows already have `custom_designated_to` populated (queued/pre-assigned but
  not yet actually started), whereas every row that has left `Unassigned` has
  `custom_designated_to` set (596/596 `Assigned`, 2,343/2,344 `Documents
  Delivered`, 117/118 `Inprogress`, 54/55 `Completed`). `workflow_state` is
  therefore the tighter, more work-actually-started signal; `custom_designated_to`
  can be used as a secondary "who" field once the stage is reached, not as
  the stage gate itself.
- **source-wired** — Frappe's native assignment mechanism (`_assign`/`tabToDo`)
  was in the candidate list but was not found used anywhere in the relevant
  code paths for `PF Process File`; `custom_designated_to` (a plain Link
  field set by app code, e.g. `visaguy_crm/visaguy_crm/allocated_to_process_file.py:16,250`)
  is the actual "who is responsible" mechanism used by this app, not
  `ToDo`-based assignment. Ruled out as redundant with the above.

Confidence: **High.**

## Stage 4 — In Progress

**Recommended signal:** `PF Process File.workflow_state = "Inprogress"`.

- **runtime-verified** — transition `Assigned → (Approve) → Inprogress`,
  allowed roles `Operations Associate` and `Operations Team Lead`
  (`tabWorkflow Transition`, idx 2, 8). 118 live rows in this state.
- **source-wired, disproves the "timer" hypothesis** — the owner's phrase
  "documents are going through a quality check" maps to entries in the
  `PF Process File Action` child table (`processflo/.../pf_process_file_action.json`),
  which references `PF Process Action` master records. Live `PF Process
  Action` names include `Quality Check`, `QC - Internal`, `QUALITY CHECK
  (INTERNAL)`, `DOCUMENTATION REVIEW`, `Application Verification`, etc. —
  i.e. "quality check" is one of many named per-file action rows that get
  worked through *while* `workflow_state = "Inprogress"`, not a separate
  status field of its own. There is no single field that isolates "currently
  in QC specifically" vs. other in-progress actions; `workflow_state =
  "Inprogress"` is the right granularity for a client-facing stage.
- **runtime-verified — disproves `custom_timer_current_status` as a stage
  signal**, despite being a real, present field (`Select`,
  `Idle/Running/Paused/Completed`, defined in
  `visaguy_crm/visaguy_crm/visaguy_crm/custom/pf_process_file.json`). Live
  distribution: `Idle` 3,863, `Paused` 2, `Completed` 1 — essentially always
  `Idle`. It is a per-session work-timer (start/pause/stop for time-tracking
  a single associate's session), evidenced by its own field cluster
  (`custom_timer_started_at`, `_paused_at`, `_elapsed_seconds`,
  `_session_id`) and by `the_visaguy/the_visaguy/utility/pf_process_file_timer.py`.
  It is not a document-lifecycle field and must not be used for the
  client-facing stage.

Confidence: **High.**

## Stage 5 — Completed

**Recommended signal:** `PF Process File.workflow_state = "Documents
Delivered"`.

- **runtime-verified** — this is the largest single state in live data
  (2,344/3,866, 61% of all Process Files), reached from both `Assigned` and
  `Inprogress` via a `Documents Delivered` action (idx 5,6,9,10), allowed by
  `Operations Associate` and `Operations Team Lead`.
  reached from both `Assigned` and `Inprogress` via a `Documents Delivered`
  action.
- **source-wired — the decisive evidence.** `the_visaguy/the_visaguy/handlers/whatsapp_message.py`
  fires a client-facing WhatsApp message **exactly** on this transition:
  ```python
  # send_process_file_updates, line ~169
  if (
      workflow_state_changed
      and doc.workflow_state == "Documents Delivered"
      and doc.custom_reference_type in ["CRM Lead", "Lead"]
  ):
      frappe.enqueue(method=_send_process_file_documents_delivered, ...)
  ```
  and the handler it enqueues (`whatsapp_message.py:359-389`) sends a
  `"Completion Feedback"` WhatsApp template with a header image, described in
  its own code as "process file documents delivered feedback". This is the
  application's own encoding of "the visa package is complete and sent to
  the client" — the exact owner phrasing for Stage 5.
- **Important nuance — a later `Completed` state also exists** (55 live
  rows), reached from `Documents Delivered` via `Approve` (Operations Team
  Lead only). It is gated by an **internal completeness check**, not a
  client-facing event:
  `visaguy_crm/visaguy_crm/completed_email_sending.py:19-22` throws if any
  `PF Process File Action` row is not `status = "Completed"` before allowing
  `workflow_state = "Completed"`. Its email-sending body is fully commented
  out (dead code) — no client notification is currently wired to this state.
  Recommendation: treat `Documents Delivered` **and** `Completed` together as
  the public "Completed" stage (`workflow_state IN ("Documents Delivered",
  "Completed")`), since `Completed` is a strict, ops-only superset reached
  after delivery, not a different client-visible milestone. This needs an
  owner decision — flagged in Unknowns.
- **runtime-verified — `Rejected` (3 rows) and `Hold` (59 rows) are real,
  live states with no mapping in the owner's 5-stage model** — see Unknowns.

Confidence: **High** for `Documents Delivered` as the trigger event;
**Medium** on whether `Completed` should be folded in (plausible, not
owner-confirmed).

---

## Answers to the five specific questions

### 1. How does a Process File relate to its questionnaire?

`PF Process File.file_collection` (native Link field, `processflo`) points
at the `FF File Collection` whose `reference_type = "PF Process File"` and
`reference_name = <process file name>`. This is exactly one collection per
Process File in live data (1:1, verified against all 3,862 collections of
that reference type — max count per process file is 1, no Process File has
more than one). The Lead-stage passport form is a **different** collection,
reached via the separate field `custom_lead_file_collection` (reference_type
`Lead`/`CRM Lead`), also populated near-universally (3,846/3,866). No
identification ambiguity exists today; a resolver can join on
`file_collection` directly without needing to filter by template or
`custom_type`. (`custom_type` on `FF File Collection` — `Primary`, `Child`,
`Spouse`, `Friend`, `Parents`, `Secondary`, plus some NULL — distinguishes
*applicant relationship* within a family/group booking, not form identity;
it is orthogonal to this question, not a filter needed here since the 1:1
relationship already holds per Process File.)

### 2. What marks a form as submitted? (most important question)

`form_submitted` is persisted as a **native, non-custom column** on
`FF File Collection` (`int(1) NOT NULL DEFAULT 0`) — it is not transient.
`visaguy_crm.data_collecting_form.add_form_data`'s extra `form_submitted`
argument, when `== 1`, sets `ff_file_collection.form_submitted = 1` and saves
it (`data_collecting_form.py:342-345`), and in the same code path also sets
a companion `custom_form_submitted` Check field on the parent `Lead` /
`CRM Lead` / `PF Process File` document (`:349-356`). So the mechanism is
real and detectable — **but** live data shows the two supposedly-linked
signals badly disagree (18 vs. 2,710 positive rows respectively, with 2,692
Process Files positive on the derived field and negative-or-absent on the
source field). This is flagged as the top open unknown; see Stage 2 and
"Unknowns and risks."

### 3. Is there a real workflow on `PF Process File`?

Yes. `Process File Workflow` in `tabWorkflow`, `document_type = "PF Process
File"`, `is_active = 1`, field `workflow_state`. Seven states (`Unassigned`,
`Assigned`, `Inprogress`, `Documents Delivered`, `Completed`, `Rejected`,
`Hold`) and 18 transitions (full transition table captured during recon,
available on request — omitted here for brevity but every state pair used
above was checked directly against it). It is the intended source for
stages 3-5, confirmed both by live usage volume (only 3/3,866 process files
have no workflow_state-relevant activity) and by the WhatsApp handler's
direct dependency on it.

### 4. What actually signals stages 3, 4 and 5?

Answered above: `workflow_state` values `Assigned`, `Inprogress`,
`Documents Delivered` (+ optionally `Completed`) respectively. The
`the_visaguy` WhatsApp handler (`handlers/whatsapp_message.py`) is the
strongest corroborating evidence — it is the one place in the codebase that
already encodes "this workflow_state transition means the client should be
told something," and it only does so for `Documents Delivered`.
`PF Process File Action` (per-action status child table) and
`custom_timer_current_status` were both examined and rejected as
stage-level signals — the first is too granular (many named actions per
file, not a single field), the second is essentially unused live data
(99.9% `Idle`) and semantically a work-session timer, not a document stage.

### 5. Ordering/monotonicity

**Not strictly monotonic.** The workflow explicitly allows moving backwards:
`Hold` has transitions to `Unassigned`, `Assigned`, `Inprogress`, and
`Documents Delivered` (idx 15-18, all `Operations Team Lead`), meaning a file
that had reached e.g. `Documents Delivered` can be put `Hold` and then routed
back to `Assigned` or `Unassigned`. 59 live rows are currently in `Hold`.
`Rejected` is also reachable only from `Documents Delivered` (idx 4,
`Reject`), a terminal-looking but non-owner-modeled state. No direct
evidence of `workflow_state` regressing *without* passing through `Hold` was
found (no transition allows e.g. `Inprogress → Assigned` directly), so
`Hold` is the sole detour mechanism — a resolver's status log must handle a
"downgrade via Hold" case rather than assuming append-only forward motion.
`form_submitted` (Stage 2) has no observed reset-to-0 code path once set,
but a whole collection can be deleted and regenerated on destination change
(`lead_hooks.py` regeneration flow), which is a different kind of
non-monotonicity (identity change, not value flip) not fully traced to a
concrete example row in this recon.

---

## Secondary question — the three missing Custom Fields

Confirmed as reported: `Lead-custom_visa_tracking_application`,
`PF Process File-custom_visa_tracking_application`, and
`PF Process File-custom_client_status` do not exist as `Custom Field`
records on `visaguy` today, while their DB columns (`varchar(140)`, matching
Link-field storage) still exist on `tabLead` and `tabPF Process File`. The
sibling fields on `Customer` and `CRM Lead` survive.

**Proof of deletion (runtime-verified):** `tabDeleted Document` has exact
records:

| deleted_name | owner | creation |
|---|---|---|
| `Lead-custom_visa_tracking_application` | Administrator | 2026-08-07 14:32:10 |
| `PF Process File-custom_visa_tracking_application` | Administrator | 2026-08-07 18:31:18.519 |
| `PF Process File-custom_client_status` | Administrator | 2026-08-07 18:31:18.643 |

These were explicit `frappe.delete_doc` calls (that is what populates
`Deleted Document`), not schema drift — the columns surviving in the DB while
the metadata records are gone is exactly what `delete_doc` on a `Custom
Field` produces (it does not drop the column by default in this Frappe
version's delete path... more precisely: the column removal is a separate,
optional step; here it clearly did not happen).

**Scale — this was not a targeted, 3-field deletion.** The same
`tabDeleted Document` window (2026-08-07, 14:00-19:00 UTC) contains **many
hundreds** of `Property Setter` and `Custom Field` deletions across entirely
unrelated doctypes — `Sales Order Item` (columns/precision/in_list_view
property setters), `Item Barcode`, `FF Document` (`main-autoname`,
`main-field_order`), etc. This rules out a hand-picked deletion of just the
visa-tracking fields; it was part of a broad, indiscriminate sweep.

**Explanation (not proof) — most likely a full/unfiltered fixture
reconciliation, triggered manually and not currently present in any
committed hooks.py.** Frappe's fixture mechanism supports two shapes: a
filtered entry (`{"doctype": "Custom Field", "filters": [...]}`, upsert-only,
confirmed by reading `frappe/frappe/utils/fixtures.py` — no delete logic at
all for the filtered path) versus a bare-string entry (`"Custom Field"`),
which represents the *entire* doctype as fixture-owned and is the shape that
can prune extras not present in the export file during `bench migrate`.
Both `visaguy_crm/visaguy_crm/hooks.py:43-44` and
`visaguy_hrms/visaguy_hrms/hooks.py:307-308` contain exactly this bare-string
`"Property Setter"` / `"Custom Field"` shape today — **but both are
commented out**, and `git blame`/`git log -p` on both files shows they have
been commented out since their earliest tracked history (visaguy_crm since
initial commit `7af96a9`, 2025-09-04; visaguy_hrms since `05dedc0`,
2026-05-04) — i.e. **never active in any committed revision** covering the
incident window. This means:
- The mechanism that would explain this exact deletion pattern (broad,
  cross-doctype, one-shot) exists in the codebase, in the exact apps whose
  large `property_setter.json`/`custom_field.json` fixture exports (e.g.
  `visaguy_hrms/visaguy_hrms/fixtures/property_setter.json`, 8,000+ lines,
  covering `Sales Order Item`, `FF Document`, etc. — the same doctypes hit)
  would produce precisely this deletion set if that fixture entry were
  active and the visa-tracking fields (added later, `f7ad8c0` "feat: add
  visa tracking data model and settings" in `the_visaguy`) simply postdate
  those exports and were never added to them.
- But no committed code currently runs it, so the trigger was most likely a
  **local, uncommitted edit to a hooks.py** (temporarily uncommenting the
  fixture block, running `bench migrate`, then reverting the edit without
  committing — which would leave no git trace) or a **manual Desk/console
  action**, both performed by `Administrator`.
- `processflo` does not own these fields (they are `Custom Field` records,
  not native `DocField`s on `PF Process File`), and `processflo`'s own
  migration/DocType-reload path does not touch `Custom Field` records at
  all — ruled out as a cause.
- `the_visaguy`'s own current, active fixture allowlist for `Custom Field`
  (`the_visaguy/the_visaguy/hooks.py:297-317`) does not list **any**
  visa-tracking `Custom Field`, including the ones that still survive — so
  it offers no protection either way and is not implicated as the cause.

**Flagged explicitly as explanation, not proof:** I could not find a single
committed, currently-live code path that performs this deletion. The
"unfiltered fixture reconciliation" theory best fits the blast radius and
timing but requires an un-committed local action to have happened, which by
definition leaves no repository evidence to confirm.

---

## Unknowns and risks — what a resolver could not yet decide reliably

1. **Stage 2 ground truth is contested (top priority).** `FF File
   Collection.form_submitted` (18 positive rows) and
   `PF Process File.custom_form_submitted` (2,710 positive rows) disagree on
   ~2,692 rows, and no code path other than the one that sets both together
   was found. Before shipping a resolver, trace at least one concrete example
   row end-to-end (ideally with `bench console`, still read-only) to learn
   whether `custom_form_submitted` is stale from a deleted/regenerated
   collection, was bulk-set by an untracked migration, or something else.
   Until resolved, do not treat `custom_form_submitted = 1` as proof the
   questionnaire was submitted through the digital form.
2. **`Rejected` (3 rows) and `Hold` (59 rows) have no place in the owner's
   five-stage model.** Product decision needed: hide them behind whichever
   of stages 1-5 they last passed through, add a sixth/seventh internal state
   not exposed publicly, or something else.
3. **Backward motion via `Hold` is real and allowed** (see Question 5). A
   status-log resolver needs an explicit policy for a regression (e.g. keep
   the log append-only and simply record the earlier stage again, vs.
   collapsing/hiding it) — not covered by the owner's stage list.
4. **Whether `Completed` (55 rows) should fold into public "Completed"
   alongside `Documents Delivered` (2,344 rows), or be treated as a distinct,
   later, still-public milestone, is unresolved** — no client notification is
   currently wired to `Completed` (the email code is commented out), which
   argues for folding it in, but this is an inference, not a stated product
   decision.
5. **No resolver code exists yet anywhere in `the_visaguy`.** This recon
   found the *signals*; nothing in `the_visaguy`'s `visa_tracking` module
   currently reads `workflow_state` or `form_submitted` to drive
   `Visa Tracking Application.current_status`. That link (and the mapping
   from `Visa Tracking Status` master records' `status_code` to these
   concrete `PF Process File` values) is entirely unbuilt — confirm before
   assuming any part of this is source-wired into the tracking application
   already.
6. **`custom_process_status`, the Select field with `Pending / Document
   Collection / Approved / Rejected` options mentioned as a candidate in the
   task brief, does not exist anywhere in the current codebase or DB** — it
   was searched for across all apps and in `tabCustom Field` for
   `PF Process File` and not found. Treat it as disproven / not present in
   this environment, not merely unused.
7. **One collection per Process File was verified only for the *current*
   live data set (3,862 rows, all count = 1).** No structural database
   constraint enforces this 1:1 relationship (it is convention, not a unique
   index), so a resolver should not assume it will always hold without a
   defensive `LIMIT 1` / most-recent-row tie-break.
