---
id: TASK-016
feature: FEAT-001
title: Derive client-facing status automatically from Process File state
status: in-progress
repository: the_visaguy
owners: []
depends_on:
  - ADR-010
expected_files:
  - the_visaguy/the_visaguy/visa_tracking/status_resolution.py
  - the_visaguy/the_visaguy/visa_tracking/handlers/pf_process_file_handlers.py
  - the_visaguy/the_visaguy/visa_tracking/jobs.py
  - the_visaguy/the_visaguy/visa_tracking/reconciliation.py
  - the_visaguy/the_visaguy/visa_tracking/doctype/visa_tracking_status/visa_tracking_status.json
  - the_visaguy/the_visaguy/visa_tracking/fixtures/visa_tracking_status.json
  - the_visaguy/the_visaguy/visa_tracking/api/status.py
  - the_visaguy/the_visaguy/visa_tracking/tests/test_status_resolution.py
  - the_visaguy/the_visaguy/visa_tracking/tests/test_pf_process_file_status_trigger.py
  - the_visaguy/the_visaguy/visa_tracking/tests/test_reconciliation_status.py
created: 2026-09-01
updated: 2026-09-02
---

# TASK-016: Derive client-facing status automatically from Process File state

## Objective

Replace hand-typed client-facing status with a value **automatically derived**
from `PF Process File` state, per ADR-010. Implement the resolver, the trigger
hooks, the queued recompute job, the reconciliation-sweep extension, the
read-only conversion of `custom_client_status`, and the new `public_title`
field on `Visa Tracking Status` (consumed by the public status/timeline API).
This task covers backend only; the frontend wire-contract change is TASK-017.

## Context

Owner decision recorded 2026-09-01 (see ADR-010) supersedes and narrows parts
of `features/ongoing/visa-tracking/README.md` "Status ownership rules" and
"Required status model". Recon backing this work is
`ongoing/visa-tracking-client-status/01-recon.md`.

**Correction to the recon report, made independently by the owner and to be
treated as ground truth:** the recon recommended `FF File Collection.form_submitted`
as the questionnaire-submitted signal. Live data shows that field is set on
only 18 of 3,862 relevant collections, because `FF File Collection` rows are
regenerated on destination change (`visaguy_crm/visaguy_crm/server_scripts/lead/lead_hooks.py`)
and the flag is lost with the deleted collection. The correct signal is
`PF Process File.custom_form_submitted` (2,710 of 3,866 set), the
Process-File-level flag, which is durable across collection regeneration. Any
implementation or future reader that reaches for `FF File Collection.form_submitted`
instead is reintroducing a defect this task exists to avoid — do not use it,
and do not re-read the recon's Stage 1/2 recommendation without this
correction.

**Verified signals (live data on `visaguy`, 3,866 Process Files):**

- `PF Process File.workflow_state` — active Frappe Workflow, 7 states:
  `Documents Delivered` 2344, `Unassigned` 691, `Assigned` 596, `Inprogress`
  118, `Hold` 59, `Completed` 55, `Rejected` 3.
- `PF Process File.custom_form_submitted` (2710 of 3866) — the durable
  questionnaire signal (see correction above).

**Prerequisite — three missing Custom Fields must exist before this task can
write or display anything.** `Lead-custom_visa_tracking_application`,
`PF Process File-custom_visa_tracking_application`, and
`PF Process File-custom_client_status` are defined in
`the_visaguy/.../fixtures/custom_fields.json` but do not currently exist as
`Custom Field` records on site `visaguy` — deleted 2026-08-07 by an
untracked, indiscriminate sweep (owner `Administrator`) that also removed
hundreds of unrelated Custom Fields and Property Setters across other
doctypes (see risk 25 in `docs/risks-and-open-questions.md`). The DB columns
survive so no data is lost, but the fields do not render until restored (a
fixture sync / `bench migrate` restoring the fixture-defined fields, or
equivalent). Verify these fields exist, live, before implementing or testing
any part of this task; without `custom_client_status` there is nothing to
write the derived status to or display.

## Required behaviour

### The six statuses (replacing the previous six; no data migration — dev sites only)

| sequence | status_code | status_name | public_title | message (existing field) |
|---|---|---|---|---|
| 10 | QUESTIONNAIRE_NOT_SUBMITTED | Questionnaire Not Submitted | Let's get your journey started. | (existing default message field, unchanged shape) |
| 20 | QUESTIONNAIRE_SUBMITTED | Questionnaire Submitted | Thank you — we've got what we need. | |
| 30 | FILE_ASSIGNED | File Assigned | Your file just found its travel companion. | |
| 40 | IN_PROGRESS | In Progress | Final checks before takeoff. | |
| 50 | COMPLETED | Completed | Wheels up! | |
| 0 | ON_HOLD | On Hold | Holding at the gate. | |

Add a `public_title` field (Data) to `Visa Tracking Status` and to its
fixture/seed records. It is a new field, additive to the doctype; do not
remove or rename existing fields on `Visa Tracking Status` unless this task's
own required behaviour needs it (the six replacement status records do).

### Mapping (`resolve_client_status`)

| `PF Process File.workflow_state` | `custom_form_submitted` | -> status_code |
|---|---|---|
| `Unassigned` | 0 (false) | `QUESTIONNAIRE_NOT_SUBMITTED` |
| `Unassigned` | 1 (true) | `QUESTIONNAIRE_SUBMITTED` |
| `Assigned` | any | `FILE_ASSIGNED` |
| `Inprogress` | any | `IN_PROGRESS` |
| `Documents Delivered` | any | `COMPLETED` |
| `Completed` | any | `COMPLETED` |
| `Hold` | any | `ON_HOLD` |
| `Rejected` | any | no change (unhandled) |
| any unknown/unrecognised state | any | no change |

### The resolver

- Implement `resolve_client_status(process_file) -> status_code | None` as a
  **pure function**: given a `PF Process File` document (or the minimal data
  needed from it), return the target `status_code` per the mapping table
  above, or `None` when no change should be applied (`Rejected`, unknown
  state, or the forward-only guard below blocks the move).
- No side effects: no writes, no enqueues, no logging inside the resolver
  itself. It computes; callers act.
- The resolver must apply the forward-only guard and the Rejected guard
  itself (see below), so every caller — the job and the reconciliation sweep
  — gets identical, centralised guard behaviour rather than reimplementing it.

### Forward-only guard (ladder sequence 10-50)

- A client must never see their status regress on the sequence-10-through-50
  ladder (e.g. "Final checks before takeoff" reverting to "we've got what we
  need"). If the newly-computed status's `sequence` is lower than the
  currently-stored status's `sequence`, and both are on the ladder, the
  resolver returns `None` (no change) rather than moving backward.
- **Reason to record in tests/comments:** a visible regression reads as a
  bug to the client and erodes trust, even though it may reflect a real
  operational fact (e.g. a file moved out of Hold to an earlier
  `workflow_state` than before Hold began).

### ON_HOLD exemption

- `ON_HOLD` (sequence 0) is **off-ladder** and **exempt from the forward-only
  guard in both directions**: entering Hold from any ladder position is
  always allowed (it must be, since entering Hold is by definition a
  backwards move relative to sequence numbering), and leaving Hold back onto
  the ladder is also allowed without being treated as a regression check
  against the pre-Hold value — the resolver computes the new ladder position
  from current `workflow_state`/`custom_form_submitted` normally once no
  longer on Hold, and the guard compares only against the ladder value
  immediately prior to the Hold detour where applicable per the mapping
  table, not a synthetic "highest ever reached" ratchet unless subsequent
  investigation proves otherwise — implement literally against the mapping
  table and the forward-only rule as stated above, and record in the PR/task
  evidence which interpretation was implemented if any ambiguity is hit in
  practice.

### Rejected guard

- `Rejected` is **deliberately unhandled** (owner's call) — resolver returns
  `None`. Clients on a Rejected file keep showing their previous status
  message; the team contacts them directly outside the tracker.
- Add an explicit hard guard so a Rejected Process File's linked
  `Visa Tracking Application` can **never** be advanced to `COMPLETED` (or
  any other status) by this mechanism — this must hold even if a future
  mapping-table edit or a bug elsewhere would otherwise produce a
  status_code for a Rejected file. Do not rely solely on "Rejected is absent
  from the mapping table" — add a defensive check.

### Trigger hooks (thin, enqueue-only)

- Hook on `PF Process File` `on_update` (or equivalent) that enqueues a
  recompute job **only when `workflow_state` or `custom_form_submitted`
  actually changed** on this save (compare against `doc.get_doc_before_save()`
  or equivalent) — never on every save.
  - **Reason:** recomputing on every save would silently overwrite a manual
    ops override (see below) within seconds of it being set, and would look
    like a bug to ops staff who just set a value and watched it vanish.
- The hook must do no resolution work itself: it enqueues an identifying
  reference (the Process File name) and returns. All resolution logic lives
  in the queued job, using the resolver.
- Use `enqueue_after_commit=True` consistent with this feature's established
  queue pattern (see ADR-007, TASK-006).

### The queued job

- Re-reads the **current** state of the Process File and its linked
  `Visa Tracking Application` at execution time (not data captured at
  enqueue time), so a job that runs late or out of order against a
  since-changed record is self-correcting rather than applying stale intent.
- Calls the resolver to get the target status_code (or `None`).
- When a change is indicated, writes it through the **existing
  lifecycle/status service** used elsewhere in this feature (see TASK-006),
  so the "one effective change, exactly one log row" contract already
  established for `Visa Tracking Status Log` holds here too. Do not add a
  second, parallel status-writing path.
- Idempotent: running the job twice for the same underlying state produces
  no second log row and no duplicate work.
- Dedupe concurrent/duplicate enqueues for the same Process File where the
  existing queue infrastructure supports it (consistent with idempotency
  requirements elsewhere in this feature, e.g. TASK-004's FileFlo
  idempotency key); document what dedupe mechanism is used.

### Ops override becomes transient, not removed

- `PF Process File.custom_client_status` becomes **read-only/derived** — no
  longer "the normal operations input" (that sentence in the feature README
  is superseded by ADR-010 and must be corrected as part of this task, see
  "Expected changes" below).
- Ops may still set a status by hand on the `Visa Tracking Application`
  (direct/exceptional path, already established by the feature) in rare
  cases. The **next automatic recompute overwrites it.** This is intended
  behaviour, not a bug to be "fixed" by adding a suppression flag — do not
  add one unless a future task explicitly asks for it.

### Reconciliation sweep

- Extend the existing reconciliation path (see feature README "A
  reconciliation path for missed FileFlo events and mismatched tracking
  statuses") to use the **same resolver**, so it can **repair drift**
  (correct a Visa Tracking Application whose status has fallen out of sync
  with its Process File's current state) rather than only reporting
  mismatches.
- The sweep must apply the same guards (forward-only, ON_HOLD exemption,
  Rejected) as the queued job — it calls the same resolver, so this should
  follow automatically; write a test that proves it (the sweep does not
  bypass the guard by calling something lower-level).

### `public_title` on the public API

- Add `public_title` to `Visa Tracking Status` (see "The six statuses"
  above).
- Wire it into the public status/timeline payload as `title`, alongside the
  existing `public_message` (unchanged field, unchanged wire name).
- This is a backend-only change to the payload shape in this task; the
  frontend consumption of the new `title` key is TASK-017, not this task.
  Do not modify `visa_tracker` (the frontend repository) as part of this
  task.

## Constraints

- No data migration for the six new statuses; this replaces the six status
  records only on dev sites. Do not write a migration for `visaguy`
  production-style data as part of this task.
- Do not touch `FF File Collection.form_submitted`; per the correction above,
  it is not the signal this task uses.
- Do not remove the per-Process-File `custom_client_status` field or its
  underlying DB column; only its read-only/derived status changes.
- Follow this project's rule that **tests are written to the contract and
  mutation-proven** (see TASK-011's "Definition of done" for the established
  pattern on this feature): each required behaviour below must have a test
  that is demonstrated to fail when the corresponding implementation is
  removed or reverted, not merely a test that currently passes.
- Do not commit, do not push (matches the workspace instruction for this
  session). Record implementation and validation evidence in this task file
  or in `ongoing/` instead.

## Test requirements

At minimum, one test (mutation-proven) per:

1. Every row of the mapping table above (`Unassigned`/false ->
   `QUESTIONNAIRE_NOT_SUBMITTED`, `Unassigned`/true ->
   `QUESTIONNAIRE_SUBMITTED`, `Assigned` -> `FILE_ASSIGNED`, `Inprogress` ->
   `IN_PROGRESS`, `Documents Delivered` -> `COMPLETED`, `Completed` ->
   `COMPLETED`, `Hold` -> `ON_HOLD`, `Rejected` -> no change, an unrecognised
   `workflow_state` value -> no change).
2. The forward-only guard: a computed status with a lower `sequence` than the
   currently-stored status on the 10-50 ladder does **not** apply.
3. `ON_HOLD` enter: moving to Hold from any ladder position always applies,
   even though it is numerically a regression.
4. `ON_HOLD` release: moving from Hold back onto the ladder applies normally
   per the mapping table, not blocked by the guard.
5. Rejected never advances: a Process File in `Rejected` state can never
   reach `COMPLETED` (or any other status) through this mechanism, including
   via a deliberately malformed/adversarial test input to the resolver
   directly (not only through the normal hook path).
6. Enqueue only on watched-field change: saving a Process File with no
   change to `workflow_state` or `custom_form_submitted` does not enqueue a
   recompute job; saving with either field changed does.
7. Dedupe: two rapid saves that each change a watched field do not produce
   two log rows or double-apply work beyond the documented dedupe mechanism.
8. Idempotency: running the job (or the reconciliation sweep) twice against
   the same underlying state produces exactly one effective status and no
   duplicate `Visa Tracking Status Log` row.
9. The "one effective change, exactly one log row" contract: a job run that
   results in the same status as already stored writes no new log row.
10. Reconciliation repair: a Visa Tracking Application whose stored status
    has drifted from what the resolver would currently compute is corrected
    by the sweep, using the same guards as the job (not a bypass path).
11. `custom_client_status` read-only/derived: an ops-set manual value on `PF
    Process File.custom_client_status` (or the Visa Tracking Application
    direct-correction path) is overwritten by the next genuine-signal
    recompute, and this is asserted as intended behaviour, not treated as a
    regression to guard against.
12. `public_title` present on the public API payload as `title`, correctly
    matching the resolved status's `public_title`, for at least one status
    with a non-empty timeline.

## Validation

- `bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`
  (per TASK-011's established invocation).
- Report the before/after test count (baseline should be read from the most
  recent recorded count — TASK-011 reported 276 green — and updated here).
- Prove each new test fails when its corresponding behaviour is removed
  (mutation-proven), consistent with TASK-011's definition of done and this
  project's standing rule.
- Confirm the three prerequisite Custom Fields exist and render on `visaguy`
  before running any test that depends on `custom_client_status` being
  writable/readable; if they are still missing, stop and report rather than
  working around their absence (e.g. by writing directly to the DB column).

## Definition of done

- `resolve_client_status` implemented as a pure function covering the full
  mapping table, the forward-only guard, the ON_HOLD exemption, and the
  Rejected guard.
- Thin enqueue-only hook on `PF Process File`, triggered only on genuine
  `workflow_state`/`custom_form_submitted` change.
- Queued job that re-reads current state, calls the resolver, and writes
  through the existing lifecycle/status service.
- Reconciliation sweep extended to use the same resolver and repair drift.
- `custom_client_status` is read-only/derived; ops override remains possible
  but is transient by design.
- `public_title` field added to `Visa Tracking Status` and wired into the
  public API as `title`.
- All twelve test requirements above covered and mutation-proven.
- Full `the_visaguy` suite green; before/after counts reported.
- Evidence recorded (this file's own "Completion evidence" section, or a
  linked `ongoing/` report) before this task moves to `completed`.

## Definition of not-done

Do not mark this task `completed` while any prerequisite Custom Field is
missing on `visaguy`, while any of the twelve test requirements is untested
or not mutation-proven, or while the frontend `title` consumption (TASK-017)
is treated as in scope here — it is a separate task.

## Completion evidence (2026-09-02)

**Status stays `in-progress`.** All required behaviour below is implemented
and independently verified green in `the_visaguy` on branch
`feat/visa-tracker`, uncommitted on top of local HEAD `53b0f28`. Per this
workspace's convention, a task with only unsaved working-tree edits is not
moved to `completed` — commit, then deploy, remain outstanding (see "What
remains" below).

### Delivered

- `resolve_client_status()` — a pure function in the new
  `the_visaguy/the_visaguy/visa_tracking/status_resolution.py`. Implements
  the full mapping table, the forward-only ladder guard, the ON_HOLD
  exemption (both directions), and a hard Rejected guard that returns `None`
  regardless of what the mapping table would otherwise produce.
- A thin, enqueue-only trigger on `PF Process File` that fires only when
  `workflow_state` or `custom_form_submitted` actually changed on that save
  (compared against the pre-save document), consistent with
  `enqueue_after_commit=True`.
- A `recompute_client_status` queued job that re-reads current Process File
  / Visa Tracking Application state at execution time (not data captured at
  enqueue time) and calls the resolver.
- `run_client_status_reconciliation_sweep`, wired to an hourly scheduler
  entry in `hooks.py`, and `repair_client_status_drift` in
  `reconciliation_service.py`, both routed through the same resolver as the
  job — the sweep repairs drift rather than only reporting it.
- The six replacement `Visa Tracking Status` records (sequence 0-50, per the
  table in "Required behaviour" above).
- `public_title` added to `Visa Tracking Status`, and `title` added to the
  public status API payload — both the current-status object and each
  timeline entry — immediately after `current_status` / `status`
  respectively (see "Exact public payload shape" below).
- `PF Process File.custom_client_status` set `read_only: 1`.

### Suites verified (independent runs, not an executor's self-report)

| Suite | Result | Note |
|---|---|---|
| `the_visaguy` | **342/342** | Up from the 298 baseline recorded in `ongoing/visa-tracking-implementation/12-session-2026-09-01-task-011-012.md` — **+44 tests, none removed.** |
| `passport_extractor` | 63/63 | Unchanged, confirms no cross-app regression. |
| `fileflo` | 8/8 | Unchanged, confirms no cross-app regression. |

The 342 figure was obtained against a test site rebuilt 2026-09-01 that
initially lacked `visaguy_crm` and `hrms` — see the session report
(`ongoing/visa-tracking-implementation/13-session-2026-09-02-task-016.md`)
for the full account of that gap, what it exposed (28 fixture-related
failures once both apps were installed), and the shared
`the_visaguy/visa_tracking/tests/fixtures.py` written to fix it without
weakening any assertion.

### Mutation proofs (four recorded; each demonstrates the corresponding test has teeth)

| Mutation | Tests that failed |
|---|---|
| Disabling the forward-only guard | 2 |
| Removing the Rejected guard | 4 |
| Enqueueing the recompute job on every save (not just watched-field changes) | 2 |
| Disabling the ON_HOLD exemption | 4 |

All twelve test requirements in this task's "Test requirements" section are
covered; see the session report for the fixture-chain root cause that
initially made 28 unrelated tests fail when the corrected test environment
was installed, and how it was resolved.

### Exact public payload shape (for TASK-017)

Top-level `data` object:

```
applicant_name_masked, passport_number_masked, destination, visa_type,
current_status, title, public_message, last_updated, timeline, support_link
```

`title` is new, positioned immediately after `current_status`. Each
`timeline` entry:

```
status, title, message, effective_on, icon
```

`title` is new here too, positioned immediately after `status`. In both
places `title` is always a string, never null — every resolvable status has
a non-empty `public_title`. The generic-failure response body is unchanged
and remains byte-identical across every failure mode (unaffected by this
task).

### What remains

1. Commit this work in `the_visaguy` on `feat/visa-tracker`.
2. Deploy to `visaguy`, per `docs/operations/visa-tracking-runbook.md`.
3. Only then may this task move to `completed`.
