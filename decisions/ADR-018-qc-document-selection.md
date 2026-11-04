# ADR-018: Explicit QC document selection with template defaults

## Status

Accepted (owner discussion, 2026-11-04). Implementation is planned, not completed.
Feature: FEAT-006. Task: TASK-049.

## Context

QC currently discovers uploads from lead and process collections, application
forms, RPA/action attachments, process-file sidebars and Process Deliverables.
Dependants also use primary deliverables. Not every available document is useful
for a check; the same content can occur through several source paths.

The owner requested per-template document defaults copied into collection rows,
plus a Desk modal where operations can include/exclude all available documents.
The owner confirmed that all new schema belongs to `the_visaguy`, the launcher is
a Button field in the QC tab, applicants have tabs, shared badges are useful,
and the raw selection table is visible only to admins through JavaScript.

## Decision

1. All new custom fields and the QC Document Selection child DocType are owned
   by `the_visaguy`'s Quality Check module. Export customizations with
   `sync_on_migrate: 1`; no fixtures. Existing generic CRM code may need guarded
   copy/preservation changes without depending unconditionally on VisaGuy.
2. Each FF File Template File row has Exclude from Quality Check, default 0.
   Copy it once to a new collection row. Existing collections are not rewritten
   from templates. Preserve explicit 0/1 through upload expansion, rejection and
   re-upload. Internal QC choices cannot be supplied by customer form requests.
3. Store choices on collection/RPA/action rows where a checkbox exists. For
   application-form, sidebar and deliverable files, store explicit source/file
   choices on the applicant's PF Process File child table. Templates are never
   changed by the modal. Shared collection rows intentionally share their setting.
4. The Table field uses normal permission level and is shown by JS only for
   Administrator/System Manager. It is not permanently Hidden. JS is presentation,
   not access control; selection APIs enforce roles, source membership and parent
   permissions. Higher field permission levels are not part of this decision.
5. Manage QC Documents is a Button field in the QC tab, available on saved,
   authorized records before any QC. Use a native Frappe Dialog, applicant tabs,
   standard controls and a compact HTML document list. Retain excluded rows and
   Shared document badges. Tabs navigate; explicit This File/Group selects run
   scope. Save and Save & Run are supported; Check/Recheck reuses stored choices.
6. Group duplicates per applicant, retaining every source association. Exclusion
   wins conflicting source defaults; an explicit modal choice overrides defaults
   across duplicate paths. Deliverable choices are applicant-scoped. Group runs
   send identical content once for all applicants who selected it; one applicant's
   exclusion does not remove another's inclusion. The shared flag is display only.
7. Batch metadata reads for all sources. No OCR/content reads or HUF calls on
   modal load. No long-lived inventory cache initially. Use optimistic revisions,
   atomic saves and source authorization; missing source write permission produces
   a clear denial rather than a blanket permission bypass.
8. Snapshot selected documents, identities, associations, exclusions and form data
   durably at start; the worker uses that input and revalidates file identity.
   Fence outdated jobs from overwriting newer runs. Apply exclusions before OCR
   and limits. Reports distinguish exclusion from read/limit failures and indicate
   when saved selection differs from the prior completed check.
9. The sidebar inclusion setting becomes an initial selection default that can
   be explicitly overridden. Existing source rows start included. Empty selections
   can be saved but cannot start a run with no selected documents. File exclusion
   does not remove structured form answers. QC remains advisory with no workflow
   changes. Existing HUF pin/adapter and authorization remain in force.

This supersedes FEAT-006 D2's unconditional file inclusion and refines D5/D18/D20
and ADR-017 decision 4. Other ADR-017 decisions remain applicable. The complete
contract, edge cases, validation and rollout are in the
[implementation plan](../features/ongoing/operations-quality-check/document-selection.md).

## Consequences

### Positive

- Operations can configure the first check and reuse choices for rechecks.
- Template defaults reduce manual work without rewriting old cases.
- Duplicate sources cannot silently bypass exclusions.
- Batched metadata reads and selected-file snapshots avoid repeated graph walks.
- Schema ownership and shared-document behaviour are explicit.

### Negative

- Row replacement paths must preserve flags across application boundaries.
- Shared collection-row choices affect every reader of that row.
- Admin-only table visibility is not confidentiality from API readers.
- Revision handling, duplicate provenance and durable input add implementation work.
- A rollback to the old collector would include excluded files and requires
  disabling QC until compatible selection-aware code is restored.

## Alternatives considered

- Template-only exclusions: cannot handle sidebar files or case-specific changes.
- Editing the template from the modal: would change future unrelated cases.
- Global exclusion on File: cannot represent different applicant choices for
  shared deliverables.
- Permanently hidden child table or high permission level: the owner wants admins
  to inspect it in Desk and operations to save via the modal; chose JS visibility.
- New toolbar button: rejected in favour of a Button field in the QC tab.
- Long-lived inventory cache, OCR cache or new queue in this task: deferred;
  batching is the initial optimization and OCR/queue work remains separate.

## Revisit when

- Measured group payloads require lazy tab loading.
- Source-parent permissions prevent the intended operations users managing files.
- Product requirements call for per-process overrides of shared collection rows.
- New document sources, HUF versions or OCR caching are introduced.
