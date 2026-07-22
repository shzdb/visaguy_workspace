# TASK-002 Planning Log

> Generated: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-002 — Passport extractor scaffold and DocType

## Scope

This log records the planning decisions and task-authoring work for TASK-002. It contains no application code, secrets, PII, raw diffs, passport samples, or production records.

---

## 1. Planning decisions

### 1.1 Scope boundary

TASK-002 is deliberately limited to the `passport_extractor` app and the `Passport Extraction` DocType only. The following are explicitly excluded:

- OCR/MRZ processing (TASK-003).
- FileFlo queued detection and orchestration (TASK-004).
- `Visa Tracker Settings`, `Visa Tracking Application`, `Visa Tracking Status`, and `Visa Tracking Status Log` (TASK-005 and TASK-006).
- Public APIs and security controls (TASK-007).
- Frontend scaffold and tracking flow (TASK-008 and TASK-009).

### 1.2 Worktree authorization

Implementation is authorized only in the feature worktree:

- Path: `/home/shahzad/visa-tracker-worktrees/passport_extractor`
- Branch: `feat/visa-tracker`
- Base SHA: `07b8cab40cd4054b39a78f23a271d7201e71baa0`

Original repository checkouts must remain untouched.

### 1.3 No asset builds

The bench Node runtime remains at `12.22.9`, below Frappe 15's `>=18` requirement. TASK-002 validation gates must not depend on `bench build`, `bench build --app passport_extractor`, or any frontend asset bundling. Python compile checks, JSON validation, site migration, and targeted app tests are sufficient.

### 1.4 Field coverage

Every `Passport Extraction` field group from `01-architecture-and-data-model.md` Section 1 was translated into explicit required behavior:

- Source and provenance (9 fields).
- Processing (11 fields).
- Passport values (11 fields).
- MRZ evidence (8 fields).
- Raw/audit (8 fields).

Total: 47 fields. No fields were invented beyond the accepted specification.

### 1.5 Lifecycle transitions

The accepted transition graph from `01-architecture-and-data-model.md` was expanded into explicit controller requirements, including:

- timestamp population rules,
- verification metadata requirements,
- retry bounds,
- supersession and duplicate reference validation.

### 1.6 Privacy and security tests

The task mandates automated tests for:

- raw OCR/MRZ/error field privacy,
- PII-free error messages,
- mandatory private file references,
- invalid transition blocking that prevents unverified records from being treated as verified.

### 1.7 Dependency guards

The task forbids imports from or Link fields to `the_visaguy`, `fileflo`, `processflo`, Lead, Customer, and Visa Tracking Application. This preserves the dependency direction in ADR-003 and ADR-004.

---

## 2. Verification of planning inputs

| Input | Status | Notes |
|---|---|---|
| FEAT-001 README | reviewed | Confirms TASK-002 is extraction-history model only |
| 01-architecture-and-data-model.md | reviewed | Source of all `Passport Extraction` fields, transitions, and ownership rules |
| ADR-003 | reviewed | Dependency direction and repository boundaries |
| ADR-004 | reviewed | Reusable app, async boundary, private audit history, verified-data ownership |
| TASK-001 | completed | Provides worktree path, base SHA, and site installation evidence |
| 04a-task-001-recon-and-setup.md | reviewed | Integration evidence and blocked items |
| 04b-task-001-finish-setup.md | reviewed | Confirms scaffold SHA, site install, and worktree cleanliness |
| STATE.md | reviewed | Phase 5 now in planning |

---

## 3. Outputs

- `tasks/ready/visa-tracking/TASK-002-passport-extractor-scaffold-and-doctype.md` — ready task with complete frontmatter, scope, behavior, validation, and stop conditions.
- `ongoing/visa-tracking-implementation/05a-task-002-planning.md` — this planning log.

---

## 4. Open questions / blockers

None. All required architecture decisions are present in accepted documents.

---

## 5. Next step

Move TASK-002 from `ready` to `in-progress` and begin implementation in `/home/shahzad/visa-tracker-worktrees/passport_extractor`.
