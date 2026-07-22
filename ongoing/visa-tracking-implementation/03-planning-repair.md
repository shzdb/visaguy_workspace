# Phase 3: Ready-Task and Decision Reconciliation

## Phase objective

Materialize the missing ADR references (ADR-003 through ADR-005) and create the first ready task (TASK-001) so that the hard implementation gate — a task in `tasks/ready/` — is satisfied. No application code was written; no application repository was mutated.

## Authored files

### ADR-003: FEAT-001 Repository/Component Ownership and Dependency Direction

- Path: `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- Status: Accepted
- Decisions preserved:
  - Ownership matrix for `fileflo`, `passport_extractor`, `the_visaguy`, `processflo`, `visa_tracker`, and `visaguy-website-client`.
  - Allowed and forbidden dependency directions from `features/planned/visa-tracking/01-architecture-and-data-model.md`.
  - Branch/workflow ownership rules from `features/planned/visa-tracking/README.md` repository and branch rules table.
- No new product behavior or architecture was introduced.

### ADR-004: Passport Extraction App and Async Processing Boundary

- Path: `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- Status: Accepted
- Decisions preserved:
  - `passport_extractor` is a new, reusable Frappe app with no imports from FileFlo, ProcessFlo, Lead, Customer, or Visa Tracking Application.
  - FileFlo post-save handler is synchronous only to the extent of enqueuing an inspection job; all passport-specific logic runs in queued workers.
  - Extraction history is private, append-only, and auditable.
  - Verified-data ownership model: `passport_extractor` owns reviewed values; `the_visaguy` decides when a verified extraction becomes the preferred Lead/Customer passport.
- Source: `features/planned/visa-tracking/01-architecture-and-data-model.md` queue requirements, data model, and passport ownership rules.

### ADR-005: Public Tracking Security and Privacy Model

- Path: `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- Status: Accepted
- Decisions preserved:
  - HMAC-SHA256 lookup over canonical passport number + DOB; HMAC key is server-side configuration and not committed.
  - Opaque short-lived Redis session token; no passport/DOB/session in `localStorage`, URLs, analytics, or error messages.
  - Generic failures for all invalid lookup scenarios.
  - Rate limiting and temporary lockout.
  - CORS restricted to the approved frontend base URL.
  - Masking and minimal response boundary for public status/timeline.
  - Public SPA uses only purpose-built whitelisted methods; no direct `/api/resource/*` access.
- Source: `features/planned/visa-tracking/README.md` public information boundary, acceptance criteria, and risks; `features/planned/visa-tracking/01-architecture-and-data-model.md` secure lookup and permissions sections.

### TASK-001: Preflight and Branch Setup

- Path: `tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md`
- Status: ready
- Folder: `tasks/ready/visa-tracking/`
- Scope:
  - Exact source/runtime reconnaissance on the remote bench.
  - Clean-state checks for `the_visaguy`, `fileflo`, and `processflo`.
  - Safe feature branch or dedicated worktree setup for `the_visaguy` and `fileflo`.
  - Scaffold and branch setup for `passport_extractor`.
  - Local initialization of `/home/shzd/Projects/tridz/visa_tracker` with Vite + React + TypeScript.
- Explicitly prohibited:
  - Feature implementation.
  - Dirty-tree cleanup (stash, reset, clean, or commit of unrelated changes).
  - Pushing to remotes.
  - Production data access or secret copying.
- Stop conditions included for dirty default branches, unexpected branches, missing repositories, contradictory integration evidence, unsafe remote state, and permission denial.

## FEAT-001 metadata/links

- `features/planned/visa-tracking/README.md` already listed `ADR-003`, `ADR-004`, `ADR-005` in `depends_on` and linked `TASK-001` to `../../../tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md`.
- No direct FEAT-001 edits were required because the created filenames match the references and the task link path is correct.
- References to `TASK-002` through `TASK-010` and supporting specifications `02-06` remain unchanged and visibly planned; their files were not fabricated.

## Decisions preserved (not invented)

All ADRs extract decisions already present in accepted FEAT-001 documents:

- Repository ownership matrix and dependency arrows from `01-architecture-and-data-model.md` sections "System boundary", "Dependency direction", and "Repository responsibility matrix".
- Async processing boundary from `01-architecture-and-data-model.md` "Queue requirements" and FEAT-001 "Scope" items 4–5.
- Private audit history and verified-data ownership from `01-architecture-and-data-model.md` "Passport ownership rules" and "Passport Extraction" data model.
- Public security model from FEAT-001 "Scope" item 15, "Public information boundary", and acceptance criteria items 21–25.

## Validation results

### Markdown metadata and template sections

| File | Metadata | Required sections | Verdict |
|---|---|---|---|
| `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md` | Title + Status | Context, Decision, Consequences, Alternatives, Revisit when | pass |
| `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md` | Title + Status | Context, Decision, Consequences, Alternatives, Revisit when | pass |
| `decisions/ADR-005-public-tracking-security-and-privacy-model.md` | Title + Status | Context, Decision, Consequences, Alternatives, Revisit when | pass |
| `tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md` | id, feature, title, status, repository, created, updated | Objective, Context, Inputs, Required behaviour, Constraints, Expected changes, Validation, Definition of done | pass |

### Path existence

- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`: present
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`: present
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`: present
- `tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md`: present

### Link resolution

- `features/planned/visa-tracking/README.md:285` links to `../../../tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md`; the target exists.
- `features/planned/visa-tracking/README.md:13-15` lists `ADR-003`, `ADR-004`, `ADR-005`; the corresponding files exist in `decisions/`.

### Application-code path check

- No files under `/home/shzd/Projects/tridz/` were modified.
- No SSH connection was made.
- All changes are limited to `decisions/`, `tasks/ready/visa-tracking/`, and `ongoing/visa-tracking-implementation/03-planning-repair.md`.

### Git diff check

Run: `git diff --check`

Result: no whitespace errors reported.

### rg verification

Run: `rg -n "ADR-003|ADR-004|ADR-005|TASK-001" features/planned/visa-tracking/README.md decisions tasks/ready`

Result: all references resolve to existing files or to the expected IDs in feature metadata.

## Ready-task verdict

TASK-001 is in `tasks/ready/visa-tracking/`, its metadata `status` is `ready`, it references FEAT-001, and it requires no new product or architecture decision. The hard ready-task gate is satisfied.

## Next phase

Phase 4 (Implementation sub-phases) can begin once an implementation agent picks up TASK-001. TASK-002 through TASK-010 and supporting specifications 02-06 should be authored before their respective implementation phases start.
