---
id: TASK-011
feature: FEAT-001
title: Tests for automatic passport extraction verification
status: ready
repository: the_visaguy
owners: []
depends_on:
  - ADR-007
  - TASK-002
expected_files:
  - the_visaguy/the_visaguy/visa_tracking/handlers/passport_extraction_handlers.py
  - the_visaguy/the_visaguy/visa_tracking/jobs.py
created: 2026-07-23
updated: 2026-07-23
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

Implemented on branch `feat/visa-tracker` in `the_visaguy` (uncommitted at time
of writing — verify state before starting):

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
