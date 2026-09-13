---
id: TASK-011
feature: FEAT-001
title: Tests for automatic passport extraction verification
status: in-progress
repository: the_visaguy
owners: []
depends_on:
  - ADR-007
  - TASK-002
expected_files:
  - the_visaguy/the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py
  - the_visaguy/the_visaguy/visa_tracking/jobs.py
  - the_visaguy/the_visaguy/visa_tracking/tests/test_passport_extraction_auto_verify.py
created: 2026-07-23
updated: 2026-09-01
---

# TASK-011: Tests for automatic passport extraction verification

## Objective

Cover the automatic verification behaviour introduced by ADR-007. The code is
implemented and deployed but **entirely untested** — it was written at the end of
a long session and its behaviour is unproven.

This matters more than usual here: five runtime defects on this feature survived
a fully green static suite, because the tests mocked exactly the seams that were
broken. Write these tests against the contract, not against observed behaviour.

## Context

Implemented on branch `feat/visa-tracker` in `the_visaguy`. **Update
2026-09-01: this is now committed, as `8254f93` (2026-08-06, "feat: auto
verify extraction"), and deployed — `Visa Tracker Settings.require_manual_verification = 0`
is live on `visaguy`.** It was uncommitted at the time this task was written;
that is no longer the state, but it remains untested, which is this task's
reason to exist. Verify current state (branch, HEAD, and whether this task's
own work has since been committed on top) before starting.

- `utils/constants.py` — added `EXTRACTION_STATUS_EXTRACTED`.
- `handlers/passport_extraction_handlers.on_update` — on a transition **into**
  `Extracted`, calls `_maybe_enqueue_auto_verification`.
- `handlers/passport_extraction_handlers._auto_verification_allowed` — requires
  settings `enabled`, `require_manual_verification` unset, and `mrz_valid`.
- `jobs.auto_verify_extraction` — reloads the document, re-checks every
  condition, sets `Verified`, saves through the ORM.

## Required behaviour

Cover at minimum:

1. A record transitioning into `Extracted` with `require_manual_verification`
   unset, `enabled` set, and `mrz_valid` true **enqueues** the job — assert
   `enqueue_after_commit=True`, since an inline save would re-enter the hook.
2. `require_manual_verification` set -> **no** enqueue.
3. `enabled` unset -> no enqueue.
4. `mrz_valid` false -> no enqueue.
5. A save where the record was **already** `Extracted` before -> no enqueue
   (not a transition).
6. `auto_verify_extraction` promotes `Extracted` -> `Verified` and the existing
   verified path then creates exactly one `Visa Tracking Application`.
7. **Re-check semantics:** the job takes no action when, between enqueue and
   execution, the record was manually verified, rejected, or moved to
   `Needs Review`, or `require_manual_verification` was set. This is the
   behaviour most likely to regress and is the reason the job reloads.
8. Idempotency: running the job twice creates one application, not two.
9. `verified_by` / `verified_on` are populated after automatic promotion.
   Assert this explicitly — the ORM save (rather than `db_set`) exists precisely
   so the controller stamps them; leaving them empty makes the **next** save of
   that document throw via `_preserve_verification_audit`.

## Validation

- `bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`
  (`--skip-test-records` is required; without it ERPNext fixture setup fails with
  `LinkValidationError: Could not find Warehouse Type: Transit`).
- Baseline before this task: **248** tests. Report the new count.
- **Prove each new test fails when the behaviour is removed**, as was done for
  the `fileflo` and `passport_extractor` fixes. A test that passes without the
  code under test is worthless.
- Re-run the full `the_visaguy` suite: it has not been run since the
  `response_service` CORS change (ADR-008).

## Constraints

- Synthetic data only in tests (`P0000000`, `1990-01-01`, `203.0.113.x`).
- Do not weaken a test to match observed behaviour. If behaviour and contract
  disagree, write the test to the contract, stop, and report the evidence.
- Do not push. Commits stay local pending owner authorisation.

## Definition of done

- All nine behaviours covered and passing.
- Each new test demonstrated to fail without the implementation.
- Full `the_visaguy` suite green and its count reported.
- Committed on `feat/visa-tracker` with evidence recorded in
  `ongoing/visa-tracker-branch-switch/`.

## Completion evidence (2026-09-01)

**Status is `in-progress`, not `completed`. The work is implemented and
verified in the working tree, but nothing is committed.** This section
records exactly what is done and what remains, so a future agent does not
re-derive it or mistake "implemented" for "shippable."

### What is done

- 15 new tests added in a new file,
  `visa_tracking/tests/test_passport_extraction_auto_verify.py`, covering all
  nine required behaviours from this task's "Required behaviour" section.
- Each of the 15 was proven to fail when its corresponding behaviour is
  removed (mutation-proven), matching this task's own "Definition of done"
  requirement and the workspace's standing lesson that a green suite alone is
  not trustworthy on this feature.
- No contract disagreement was found: observed behaviour matched ADR-007
  exactly, so no test was written to a weakened or renegotiated contract.
- Two mutations worth recording for future maintainers:
  - Replacing the controller's ORM `doc.save()` with `frappe.db.set_value()`
    in the promotion path leaves `verified_by` empty — this is what behaviour
    9's test catches, and it is exactly the failure mode ADR-007's "Decision"
    section warns about (`_preserve_verification_audit` would then break the
    *next* save of that document).
  - Removing the job's re-check of current status before promoting makes the
    already-Rejected-record case raise `ValidationError` on an illegal
    transition, rather than silently no-op as the contract (behaviour 7)
    requires.
- Full `the_visaguy` suite re-run on `visa-tracker-test.localhost`: **276
  green** (up from 261 green after the same-day test-isolation and CORS
  repairs; see the session report referenced below for the fuller
  progression). This run post-dates the ADR-008 `response_service` CORS
  change, closing the "has not been run since" gap noted in TASK-010's
  2026-07-23 progress section.

### What remains

- **Commit.** `visa_tracking/tests/test_passport_extraction_auto_verify.py`
  and the six other test files touched this session are all uncommitted in
  `the_visaguy`, branch `feat/visa-tracker`, on top of local HEAD `4192e36`.
  No commit has been made for this task's work.
- **Push.** Once committed, this rides along with `the_visaguy`'s existing
  one-commit-unpushed state relative to `upstream/feat/visa-tracker`
  (see TASK-010's 2026-09-01 repository-state table) — owner authorisation for
  pushing is still outstanding, tracked at TASK-010 blocker 4.
- No further test-writing work is believed to remain for this task's own
  scope; what remains is entirely the commit/push step, not additional
  implementation.

Full session narrative, including the five-failure triage that preceded this
work: `ongoing/visa-tracking-implementation/12-session-2026-09-01-task-011-012.md`.

### Update (2026-09-13)

- **Committed:** `the_visaguy` `25e3186` ("test(TASK-011): cover automatic
  passport extraction verification").
- **Pushed, as of the last fetch:** `the_visaguy` `feat/visa-tracker` HEAD
  equals `upstream/feat/visa-tracker`.
- Remaining: deploy. The task stays `in-progress` until then, like
  TASK-012 and TASK-016. See
  `ongoing/visa-tracking-implementation/16-session-2026-09-13-reconciliation.md`.
