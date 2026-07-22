# Visa Tracking Implementation Readiness Reconnaissance

## Executive summary

- **Hard blockers:** 1
- **Documentation drift items:** 18 (10 missing task files, 3 missing ADR files, 5 missing supporting-spec files)
- **Recommended next phase:** Phase 3 from `ongoing/visa-tracking-implementation/STATE.md` — "Ready-task preparation or blocker resolution" — focused on authoring TASK-001 and the minimal ADR/spec documents needed to satisfy the ready-task gate.
- **Verdict:** Implementation cannot start now. The workspace lacks any task in `tasks/ready/`, which is the explicit entry gate for implementation work under `.agents/rules/project-rules.md` and `README.md`.

---

## R1. Existence audit: referenced files that are absent

### Method

- Inspected the working tree under `tasks/`, `decisions/`, and `features/planned/visa-tracking/`.
- Reviewed the full Git history (`git log --all --name-only`) and deletion history (`git log --all --diff-filter=D --summary`) for the referenced paths.
- Checked `git reflog`, `git stash list`, and untracked files for any hidden or orphaned copies.

### Findings

| Category | Referenced paths | Evidence |
|---|---|---|
| Task documents | `tasks/ready/visa-tracking/TASK-001.md` through `TASK-010.md` | Listed in `features/planned/visa-tracking/README.md:285-294`. None exist in the working tree; `tasks/ready/` contains only `.gitkeep`. None were ever committed to Git. |
| ADR documents | `decisions/ADR-003*.md`, `ADR-004*.md`, `ADR-005*.md` | Listed in `features/planned/visa-tracking/README.md:13-15` under `depends_on`. None exist; `decisions/` contains only `ADR-001` and `ADR-002`. None were ever committed. |
| Supporting specifications | `features/planned/visa-tracking/02-backend-workflows-and-api-contracts.md`, `03-frontend-design-and-layout.md`, `04-security-privacy-and-abuse-controls.md`, `05-test-and-verification-matrix.md`, `06-developer-runbook.md` | Listed in `features/planned/visa-tracking/README.md:296-303`. Only `01-architecture-and-data-model.md` exists. None of 02-06 were ever committed. |

### Conclusion

All referenced TASK, ADR, and supporting-spec files are **merely referenced but uncreated**. They were **not deleted** from the repository. The only files ever committed for FEAT-001 are:

- `features/planned/visa-tracking/README.md` (commit `add4f14`)
- `features/planned/visa-tracking/01-architecture-and-data-model.md` (commit `3ae854f`, merged via PR #1 at `4b2ad88`)

---

## R2. Lifecycle gates separating planning from implementation

### Hard blocker

1. **No ready task exists.**
   - `tasks/ready/` contains only `.gitkeep`.
   - `README.md:9` states: "All implementation work must start from a task marked `ready` and follow `.agents/rules/project-rules.md`."
   - `.agents/rules/project-rules.md:38` states: "Mark a task `ready` only when it requires no new product or architecture decision."
   - `features/planned/visa-tracking/README.md:368-370` states: "Move this feature to `ongoing/` only when TASK-001 is assigned and implementation work actually begins."
   - This is a **hard, unambiguous gate**. Until at least TASK-001 is authored, reviewed, and placed in `tasks/ready/`, no implementation agent should touch application repositories.

### Documentation drift (not a hard blocker)

The following are broken links to files that were never created. They do not block implementation once a ready task exists, but they must be reconciled to keep the workspace authoritative and navigable.

| Drift item | Count | Notes |
|---|---|---|
| Broken task links in FEAT-001 | 10 | `TASK-001` through `TASK-010`. The feature doc describes task order and purpose in enough detail that the task files can be drafted from accepted intent. |
| Broken ADR links in FEAT-001 `depends_on` | 3 | `ADR-003`, `ADR-004`, `ADR-005`. The architecture-and-data-model document already captures the equivalent decisions (repository boundaries, dependency direction, data ownership, security boundaries). `features/planned/visa-tracking/README.md:356-359` explicitly states: "No unresolved product or architecture decision blocks implementation." This evidence indicates the `depends_on` entries are stale metadata rather than active blockers. |
| Broken supporting-spec links | 5 | `02-backend-workflows-and-api-contracts.md`, `03-frontend-design-and-layout.md`, `04-security-privacy-and-abuse-controls.md`, `05-test-and-verification-matrix.md`, `06-developer-runbook.md`. These can be authored from the existing feature and architecture documents. |

### What is not a blocker

- The feature status is `planned` and the file lives in `features/planned/visa-tracking/`. This is correct for pre-implementation planning.
- The architecture-and-data-model document is present and accepted (committed and merged). It provides sufficient intent for the first ready task.
- No unresolved product or architecture decisions are declared in the feature document.

---

## R3. Smallest safe next phase

### Recommended phase

**Phase 3 from `ongoing/visa-tracking-implementation/STATE.md`: Ready-task preparation or blocker resolution.**

This phase should produce, at minimum:

1. **ADR-003, ADR-004, ADR-005** (or a deliberate decision to remove the stale `depends_on` entries). These can be extracted directly from the accepted `01-architecture-and-data-model.md` and the feature README. They do not require new product decisions — only recording decisions that are already implicit in accepted documents.
2. **TASK-001** moved to `tasks/ready/visa-tracking/TASK-001-preflight-and-branch-setup.md`. TASK-001 is the natural first ready task because the feature README already defines it as "preflight, local repository setup, and exact integration evidence." Its scope is bounded and does not require new architecture decisions.
3. Optionally, the remaining task documents (TASK-002..TASK-010) and supporting specs (02-06) can be drafted in the same phase, but only TASK-001 is strictly required to satisfy the ready-task gate.

### Documents that can be authored from accepted FEAT-001 intent

- ADR-003 through ADR-005 (extract architecture decisions already in `01-architecture-and-data-model.md`).
- TASK-001 through TASK-010 (the feature README already defines order, objective, and repository for each).
- Supporting specs 02-06 (the feature README and architecture doc provide the source material).

### Documents that require user/product decisions

- **None** for the initial ready-task gate, assuming ADR-003..005 are treated as stale/architecture-already-recorded.
- If the product owner decides the ADRs represent genuinely unresolved decisions, then ADR-003..005 become blockers and must be accepted before TASK-001 can be marked ready.
- Any future mismatch found by TASK-001 (e.g., exact FileFlo field ID property, Lead-to-PF Process File path) may require a workspace decision, per `features/planned/visa-tracking/README.md:360-366`.

---

## R4. Repository and worktree prerequisites

No SSH, network access, or mutation of application repositories was performed. Only local filesystem metadata was inspected.

### Local frontend repositories

| Repository | Path | State | Relevance |
|---|---|---|---|
| `visa_eligibility_checker` | `/home/shzd/Projects/tridz/visa_eligibility_checker` | Exists (present on disk) | Existing React/FastAPI frontend; not a direct target for FEAT-001 but shows the local `tridz/` workspace is active. |
| `visaguy_business_client` | `/home/shzd/Projects/tridz/visaguy_business_client` | Exists (present on disk) | B2B portal; not a FEAT-001 target. |
| `visaguy-website-client` | `/home/shzd/Projects/tridz/visaguy-website-client` | Exists (present on disk) | Read-only design reference for the new tracker, per FEAT-001. |
| `visa_tracker` (new SPA) | `/home/shzd/Projects/tridz/visa_tracker` | **Does not exist** | Must be created locally (Vite + React + TypeScript scaffold) before TASK-008/TASK-009. No remote required. |

### Remote Frappe bench

| Item | Value | Source |
|---|---|---|
| Bench path | `/home/shahzad/bench` | `README.md:34`, `features/planned/visa-tracking/README.md:153` |
| SSH host/port | `erpcode.tridz.in:2257` | `README.md:34`, `features/planned/visa-tracking/README.md:153` |
| Dirty working trees known | `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven` | `README.md:20` |

No connection was made to validate the current branch state, dirty-tree status, or bench app layout. TASK-001 will need to perform that reconnaissance before creating `feat/visa-tracker` branches.

### Clean worktree prerequisites for implementation

Before TASK-001 branches any repository, the following must be true:

1. The target Frappe apps (`the_visaguy`, `fileflo`) must be on their default branch with a clean working tree, or their unrelated changes must be stashed/committed.
2. `processflo` has a known dirty working tree; FEAT-001 plans no source changes there, but TASK-001 must confirm the dirty state does not conflict with planned custom fields supplied by `the_visaguy`.
3. The new `visa_tracker` local repository must be initialized from a clean Vite scaffold, committed, and then feature work can proceed on the default branch (no `feat/visa-tracker` branch required per FEAT-001 repository rules).

---

## R5. Proposed phase sequence

| Phase | Output | Purpose | Entry gate |
|---|---|---|---|
| 1. Readiness reconnaissance | `ongoing/visa-tracking-implementation/01-readiness-recon.md` | Confirm what exists, what is missing, and why implementation cannot start yet. | **Complete.** |
| 2. Orchestrator triage | `ongoing/visa-tracking-implementation/02-triage.md` | Decide whether to author missing ADRs/specs now or treat them as drift and proceed directly to TASK-001. | Pending. |
| 3. Ready-task and ADR/spec reconciliation | `tasks/ready/visa-tracking/TASK-001*.md`; optionally `decisions/ADR-003*.md`, `ADR-004*.md`, `ADR-005*.md`; optionally `features/planned/visa-tracking/02-06*.md` | Satisfy the hard ready-task gate and remove stale/broken dependencies. | Requires author/editor access to workspace docs; no application repo mutation. |
| 4. Implementation sub-phases | TASK-001 through TASK-010 completion evidence in application repositories | Execute the feature across `the_visaguy`, `fileflo`, `passport_extractor`, and `visa_tracker`. | Requires TASK-001 in `tasks/ready/`. |
| 5. Verification | `tasks/completed/visa-tracking/TASK-010*.md` with test matrix evidence | Close the feature and move FEAT-001 to `features/completed/`. | Requires all acceptance criteria evidenced. |

---

## Evidence paths

- `README.md` — workspace role and development paths.
- `.agents/rules/project-rules.md` — lifecycle rules and ready-task criteria.
- `tasks/README.md` — task state definitions and entry criteria.
- `features/planned/visa-tracking/README.md` — FEAT-001 intent, task order, ADR dependencies, acceptance criteria, and completion notes.
- `features/planned/visa-tracking/01-architecture-and-data-model.md` — accepted architecture decisions embedded in the feature.
- `decisions/ADR-001-workspace-and-repository-authority.md` — workspace authority model.
- `decisions/ADR-002-app-ownership-classification.md` — repository ownership model.
- `ongoing/visa-tracking-implementation/STATE.md` — current phase table.
- Git history: commits `9e12be3`, `add4f14`, `3ae854f`, `4b2ad88`, `7d7861e`.

---

## Final verdict

**Implementation cannot start now.** The single hard blocker is the absence of any task in `tasks/ready/`. All other gaps are documentation drift that should be reconciled during the next phase. The smallest safe next step is to enter the ready-task preparation phase, author TASK-001 (and optionally the stale ADR/spec references), and place TASK-001 in `tasks/ready/` before any application repository is touched.
