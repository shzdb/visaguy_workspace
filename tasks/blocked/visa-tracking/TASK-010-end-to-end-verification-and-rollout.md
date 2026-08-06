---
id: TASK-010
feature: FEAT-001
title: End-to-end verification, security gate, and rollout evidence
status: blocked
repository: multiple
owners: []
depends_on:
  - TASK-009
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# End-to-end verification, security gate, and rollout evidence

## Objective

Prove the whole feature works together, close the outstanding review items, and record the evidence that permits FEAT-001 to be marked complete.

## Blocked by

**TASK-009**, and additionally by two review items carried forward from completed tasks (see below).

## Required behaviour

### Test execution evidence

Test *bodies* exist across `the_visaguy` (13 modules), `passport_extractor`, and `fileflo` (2 modules). No recorded pass evidence is held in this workspace. Run them and record results:

```bash
bench --site visa-tracker-test.localhost run-tests --app the_visaguy
```

```bash
bench --site visa-tracker-test.localhost run-tests --app passport_extractor
```

```bash
bench --site visa-tracker-test.localhost run-tests --app fileflo
```

### Carried-forward review items

1. **Auto-verification criteria (from TASK-006).** Commit `8254f93` "feat: auto verify extraction" introduces automatic verification. The feature document excludes "automatic use of unverified extraction data". Review the promotion criteria, confirm they are strict enough to satisfy that exclusion, and record them in ADR-005. If they are not strict enough, this is a stop-and-escalate condition, not a fix-in-place.
2. **PaddleOCR runtime verification (from TASK-003).** Confirm model files are available to production workers and that a live OCR run succeeds. Until then extraction stays **source-wired**, not **runtime-verified**.

### Migration and fixtures

`bench --site <site> migrate` applies cleanly; `Visa Tracking Status` fixtures import with the six seed statuses; queue jobs register on the `short` and `long` queues.

### Security gate

- Invalid passport/DOB returns the generic response.
- Rate limiting and temporary lockout trigger as designed.
- No sensitive value appears in URLs, logs, browser storage, analytics, or error messages.
- CORS is restricted to the deployed tracker origin.

### Manual acceptance matrix

Walk the full product flow: FileFlo passport upload → queued inspection → extraction → verification → Lead tracking application → Process File link and status → operations status change → public lookup in the SPA.

## Constraints

No real passport or production PII may be committed to any repository or recorded in this workspace.

## Validation

Every acceptance criterion in FEAT-001 has recorded evidence, with an explicit verification label.

## Definition of done

All tests pass with recorded output, both carried-forward review items are closed, the security gate passes, and the manual acceptance matrix is complete.

**This task does not include deployment.** Merging and deploying is TASK-011 and is performed manually by the project owner.
