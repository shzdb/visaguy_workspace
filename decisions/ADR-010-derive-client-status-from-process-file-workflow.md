# ADR-010: Client-Facing Status Derived From Process File Workflow

## Status

Accepted

Supersedes the parts of `features/ongoing/visa-tracking/README.md`
"Status ownership rules" that describe `PF Process File.custom_client_status`
as "the normal operations input", and narrows its "Required status model"
section, which lists the previous six status records. All other parts of the
feature README, and ADR-005 through ADR-009, remain in force and are
unaffected by this decision.

## Context

The feature as originally built (TASK-005, TASK-006) let operations staff
type the client-facing status by hand on `PF Process File.custom_client_status`,
which then synchronized to the linked `Visa Tracking Application` and its
status log. This required ops to remember to update a field that exists
alongside — but separately from — the `workflow_state` field they already
drive through the real `Process File Workflow` (an active Frappe Workflow,
7 states, live-operated: `Documents Delivered` 2344, `Unassigned` 691,
`Assigned` 596, `Inprogress` 118, `Hold` 59, `Completed` 55, `Rejected` 3, out
of 3,866 Process Files). In practice this is duplicate manual work riding on
top of a signal the system already has.

Reconnaissance (`ongoing/visa-tracking-client-status/01-recon.md`) confirmed
two durable, live-operated signals exist and are sufficient to derive the
client-facing stage automatically:

- `PF Process File.workflow_state` — high confidence for stages 3-5 (File
  Assigned, In Progress, Completed), corroborated independently by
  `the_visaguy/the_visaguy/handlers/whatsapp_message.py` already firing a
  client-facing WhatsApp message specifically on the transition into
  `Documents Delivered`.
- `PF Process File.custom_form_submitted` — durable questionnaire-submitted
  signal for stages 1-2 (Questionnaire Not Submitted / Submitted).

**Correction to the recon report, made independently by the owner and
recorded here so no future reader re-derives the wrong conclusion:** the
recon's own summary table recommended `FF File Collection.form_submitted` as
the stage-1/2 signal. Live data shows that field is set on only 18 of 3,862
relevant `FF File Collection` rows, because those collections are
regenerated on destination change
(`visaguy_crm/visaguy_crm/server_scripts/lead/lead_hooks.py`) and the flag is
lost with the deleted collection — it is not durable. The correct signal is
`PF Process File.custom_form_submitted` (2,710 of 3,866 rows set), which
lives on the Process File itself and survives collection regeneration. The
recon flagged this exact discrepancy as its top open unknown without
resolving which field to trust; this ADR resolves it in favor of the
Process-File-level field.

A prerequisite blocks implementation: three Custom Fields defined in
`the_visaguy/.../fixtures/custom_fields.json` —
`Lead-custom_visa_tracking_application`,
`PF Process File-custom_visa_tracking_application`, and
`PF Process File-custom_client_status` — do not currently exist as `Custom
Field` records on site `visaguy`, deleted 2026-08-07 by an untracked,
indiscriminate sweep that also removed hundreds of unrelated Custom Fields
and Property Setters (see risk 25, `docs/risks-and-open-questions.md`). DB
columns survive, so no data is lost, but without `custom_client_status`
there is nothing for a derived status to write to or display. This must be
restored before TASK-016 can be validated at runtime.

## Decision

Client-facing status becomes **automatically derived** from Process File
state instead of being typed by hand.

### Architecture

- A pure `resolve_client_status(process_file)` function, with no side
  effects, is the single place mapping logic lives.
- Thin hooks on `PF Process File` only enqueue a recompute job, and only when
  a watched field (`workflow_state` or `custom_form_submitted`) actually
  changed on that save — never on every save.
- The queued job re-reads current state at execution time and calls the
  resolver, so a job that executes late or out of order against a
  since-changed record is self-correcting rather than applying stale intent.
- Writes are routed through the existing lifecycle/status service (TASK-006),
  preserving the established "one effective change, exactly one log row"
  contract for `Visa Tracking Status Log`.
- The reconciliation sweep (feature README "A reconciliation path for missed
  FileFlo events and mismatched tracking statuses") is extended to use the
  same resolver, so it can **repair** drift, not only report it.

### The six statuses (replacing the previous six; no data migration — dev sites only)

| sequence | status_code | status_name | public_title |
|---|---|---|---|
| 10 | QUESTIONNAIRE_NOT_SUBMITTED | Questionnaire Not Submitted | Let's get your journey started. |
| 20 | QUESTIONNAIRE_SUBMITTED | Questionnaire Submitted | Thank you — we've got what we need. |
| 30 | FILE_ASSIGNED | File Assigned | Your file just found its travel companion. |
| 40 | IN_PROGRESS | In Progress | Final checks before takeoff. |
| 50 | COMPLETED | Completed | Wheels up! |
| 0 | ON_HOLD | On Hold | Holding at the gate. |

### Mapping

`Unassigned` splits on `custom_form_submitted` into
`QUESTIONNAIRE_NOT_SUBMITTED` / `QUESTIONNAIRE_SUBMITTED`; `Assigned` ->
`FILE_ASSIGNED`; `Inprogress` -> `IN_PROGRESS`; `Documents Delivered` and
`Completed` both -> `COMPLETED`; `Hold` -> `ON_HOLD`; `Rejected` -> no
change; an unrecognised `workflow_state` -> no change.

### Forward-only guard, and why

A client must never watch their status regress on the ladder (sequence
10-50) — e.g. "Final checks before takeoff" reverting to "we've got what we
need" reads as a bug and erodes trust, independent of whether the underlying
operational fact is real. The resolver refuses to move to a lower-sequence
ladder status than currently stored.

### ON_HOLD is off-ladder, and why

`ON_HOLD` (sequence 0) is exempt from the forward-only guard in both
directions. It has to be: entering Hold is, by construction, a backwards
move in sequence terms, so a strict guard would make Hold undisplayable.
Leaving Hold resumes normal ladder computation from current state.

### Rejected is deliberately unhandled, and why

The owner's call: `Rejected` produces no status_code from the resolver.
Those clients keep showing their previous message, and the team contacts
them directly outside the tracker. A hard guard, independent of the mapping
table's mere omission of `Rejected`, ensures a Rejected file can never be
advanced to `COMPLETED` and auto-display "Wheels up!" through this or any
future bug in the mapping.

### Ops override becomes transient, and why

`PF Process File.custom_client_status` becomes read-only/derived. Ops may
still set a status by hand on `Visa Tracking Application` in rare cases via
the existing exceptional direct-correction path; the next automatic
recompute overwrites it. This is intended: the alternative (an override that
sticks) would silently desynchronize the client-facing status from the
Process File's real state indefinitely, with no automatic path back to
correctness.

### Recompute only on genuine signal change, and why

Triggering only on an actual change to `workflow_state` or
`custom_form_submitted` — never on every save — is deliberate: recomputing
on every save would overwrite a manual ops value within seconds of it being
set, which would look broken to the person who just set it, even though the
overwrite-on-next-genuine-change behavior above is intended.

### `public_title`, and why

A new `public_title` field is added to `Visa Tracking Status` and sent as
`title` on the public status/timeline payload (frontend consumption is
TASK-017). This was chosen over two alternatives:

- Folding the title into the existing `public_message` field — rejected,
  because it would show the blunt internal-sounding label
  ("Questionnaire Submitted") as the client's heading rather than the
  intended marketing-voice title ("Thank you — we've got what we need.").
- Reusing `status_name` as the title — rejected, because it would show
  marketing copy ("Wheels up!") in the internal ops dropdown where
  `status_name` is meant to read as a plain operational label
  ("Completed").

This costs a frontend wire-contract change, tracked separately as TASK-017.

## Consequences

### Positive

- One decision function (`resolve_client_status`) to maintain, instead of
  scattered explicit status-setting calls at each phase transition.
- Idempotent by construction: recomputing against the same underlying state
  always yields the same result and, through the existing lifecycle service,
  writes no duplicate log row.
- Self-healing after a missed event or a downed worker: the reconciliation
  sweep uses the same resolver and can repair drift on its own schedule,
  without needing the original triggering event to be replayed.
- Immune to out-of-order job execution: because the job re-reads current
  state rather than acting on data captured at enqueue time, a late or
  reordered job converges on the correct status rather than overwriting a
  newer one with stale intent.
- Removes a category of ops error (forgetting to update
  `custom_client_status`) entirely, since the field is no longer a manual
  input.

### Negative

- **Derived status is harder to explain than an explicit event trail.** When
  a client asks "why does it say X," the answer is now "because
  `resolve_client_status` computed X from the Process File's current
  `workflow_state` and `custom_form_submitted`," not "because someone set it
  to X on this date" — a support agent must reconstruct the Process File
  state at the relevant time rather than reading an explicit intent log.
- **No worker means no updates.** If the RQ worker is down, no client sees
  their status change until the reconciliation sweep next runs and catches
  up — a period of staleness bounded by the sweep's schedule, not by the
  triggering event.
- The forward-only guard means a Process File that moves through Hold back
  to an earlier `workflow_state` than it held before Hold can display a
  ladder position that does not literally match `workflow_state` at that
  instant, until state progresses again — an intentional trade-off (see
  "Forward-only guard, and why" above) but a real divergence between
  internal state and displayed state that must be understood by anyone
  debugging a status complaint.
- `custom_client_status` becoming read-only removes a fallback: if the
  resolver has a bug, ops can no longer permanently correct a client-visible
  status by hand — any manual correction is overwritten by the next genuine
  signal change, by design.

## Alternatives considered

- **Scattered explicit `set_client_status` calls at each phase transition**
  (e.g. one call in the `workflow_state` transition hook, another in the
  `custom_form_submitted` handler, mirroring how `custom_client_status` was
  originally intended to be set by ops but now set by code instead). Rejected:
  this multiplies the number of places that encode the mapping logic, makes
  the forward-only guard and Rejected guard easy to apply inconsistently
  across call sites, and does not naturally support a reconciliation sweep
  repairing drift — each call site would need its own idempotency and
  guard logic re-implemented, exactly the failure mode this feature's own
  history warns about (five runtime defects survived a green suite because
  logic was duplicated across seams; see the feature README's "Testing
  lesson").
- **Derive-and-reconcile model (chosen).** One pure resolver, thin
  triggers, and a reconciliation sweep that shares the resolver. Chosen for
  the reasons in "Positive" above — primarily idempotency, self-healing, and
  immunity to out-of-order execution — despite the explainability and
  worker-dependency costs recorded under "Negative".

## Revisit when

The reconciliation sweep's repair frequency proves too coarse for real
support-ticket volume (i.e., staleness after a worker outage becomes a
recurring complaint), the forward-only guard's Hold-detour behavior is
observed to confuse ops or clients in a way that needs a different
interpretation than the one implemented in TASK-016, or the owner decides
`Rejected` should have client-facing handling after all.
