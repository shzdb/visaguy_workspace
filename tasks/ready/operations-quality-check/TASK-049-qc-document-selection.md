---
id: TASK-049
feature: FEAT-006
title: Select documents for process-file quality checks
status: ready
repository: the_visaguy
repositories:
  - the_visaguy
  - visaguy_crm
owners: []
depends_on:
  - ADR-018
expected_files:
  - the_visaguy/quality_check/documents.py
  - the_visaguy/quality_check/context.py
  - the_visaguy/quality_check/api.py
  - the_visaguy/quality_check/runner.py
  - the_visaguy/quality_check/custom/
  - the_visaguy/quality_check/doctype/qc_document_selection/
  - the_visaguy/quality_check/tests/
  - the_visaguy/public/js/pf_process_file_qc.js
  - the_visaguy/public/js/qc_document_dialog.js
  - the_visaguy/hooks.py
  - visaguy_crm/file_collection_rows.py
  - visaguy_crm/data_collecting_form.py
  - visaguy_crm/allocated_to_process_file.py
  - visaguy_crm/file_collection_from_lead.py
  - visaguy_crm/rejection_document_email_sending.py
created: 2026-11-04
updated: 2026-11-04
---

# TASK-049: Select documents for process-file quality checks

## Objective

Implement the accepted document-selection extension to existing QC. Operations
can configure documents before the first check, save exclusions and run QC using
the exact selected document input. This task is ready; implementation has not
started. The current request authorizes workspace planning and its PR only.

## Context and inputs

- [Complete plan](../../../features/ongoing/operations-quality-check/document-selection.md)
- [ADR-018](../../../decisions/ADR-018-qc-document-selection.md)
- [FEAT-006](../../../features/ongoing/operations-quality-check/README.md)
- [ADR-017](../../../decisions/ADR-017-process-file-quality-check-with-pinned-huf.md)
- Existing TASK-048 code is the baseline, not a request to redo Phase 1.

## Required behaviour

Implement the entire linked plan, including its selection precedence, source
mapping, permissions, optimistic revisions, shared-document associations,
snapshot lifecycle and first-run UX. In particular:

1. Every new field/DocType belongs to `the_visaguy` Quality Check, including
   custom fields on FileFlo/CRM DocTypes. No schema additions in those apps.
2. New collections copy per-template-row exclusion once; existing collections
   remain included initially and template edits never rewrite them. Preserve
   source-row choices through every replacement flow, treating explicit 0 as set.
3. Launch with a Button field inside the QC tab. Applicant tabs, shared badges,
   excluded files, search/filter/counts, previews and explicit This File/Group
   scope are present before the first run. Save and atomic Save & Run work.
4. Admins see the raw child table through role-based JS; ordinary operations
   users use the modal. Backend roles and parent/source authorization are enforced.
5. Source flags plus applicant-scoped file choices resolve duplicate paths
   deterministically. Group deduplication retains every selected association.
6. Inventory loads with batched metadata queries, no OCR or content reads. Workers
   use a durable selected-document/form-data snapshot and detect file replacement.
   Fence stale jobs. Keep existing HUF integration and workflow semantics.
7. Reports retain actual inputs/exclusions/failure reasons and flag selection
   changes after a completed run. Zero selected documents cannot start QC.

## Constraints and technical prerequisites

- Read current application instructions and use isolated branches. Base references
  reviewed are main for `the_visaguy` and `visaguy_crm`; verify current heads and
  appropriate target branches before publishing application PRs.
- Trace the direct `fileflo.document_fetch.document_fetch` callers and the CRM
  whitelisted overrides before changing initial copy. FileFlo was inaccessible
  through the connector during planning; read installed/source code if needed.
  This is technical discovery, not an unresolved product decision.
- Do not unconditionally import VisaGuy from generic CRM/FileFlo paths. Verify
  compatible behaviour without the optional fields/app installed.
- Export Customizations, `sync_on_migrate: 1`; no new fixtures. No production data
  or secrets in workspace records. No live-site mutation in this task's tests.
- Dedicated queue, OCR cache and full history are outside this task.

## Expected changes and delivery

Follow the schema → inheritance → inventory/save → UI → runner/report sequence
in the plan. Snapshot storage/version metadata may require additional server-owned
PF fields, also exported from `the_visaguy`. Reuse existing helpers where suitable;
listed files are expected touch points, not a requirement to duplicate logic.
Publish linked application PRs and document compatible deployment ordering.
Migrate/build/restart and rollback instructions must preserve exclusion semantics.

## Validation

- Automated coverage for template defaults, existing rows, 0/1 inheritance,
  single/multi/additional upload, rejection/re-upload and every document source.
- Duplicate bypass, conflicting defaults, group deduplication and independent
  primary/dependant shared-deliverable choices.
- Forged source IDs, role/parent permission denial, stale/concurrent edits,
  rollback, empty selection, first run and no HUF/app-field fallback.
- Durable snapshot stability, replaced/deleted input, stale worker fencing,
  preserved form data, limits/OCR failures and report staleness.
- Browser checks for tab counts, search/filters, preview, badges, Save/Cancel,
  Save & Run, errors/retry, admin visibility and realtime result rendering.
- Query count, metadata payload size and latency for single and realistic family
  cases; no per-document File metadata query loop. Measure OCR separately.

## Definition of done

- Application changes implement the full plan with meaningful tests passing.
- Test-site migration is repeatable; normal operations and admin Desk behaviour
  are checked in browser with evidence recorded.
- Performance measurements and any limits are recorded; no speculative claim of
  runtime verification or deployment based only on source tests.
- Application PRs, commits and deployment/rollback details are linked here.
- Feature/task status reflects actual validation. Reconcile Tasklane when its
  integration is available; the CLI was unavailable in the planning environment.
