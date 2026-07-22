---
id: TASK-001
feature: FEAT-001
title: Preflight and branch setup
status: completed
repository: visaguy_workspace, the_visaguy, fileflo, passport_extractor, visa_tracker
owners: []
depends_on:
  - ADR-003
  - ADR-004
  - ADR-005
expected_files:
  - ongoing/visa-tracking-implementation/04a-task-001-recon-and-setup.md
  - /home/shzd/Projects/tridz/visa_tracker/package.json
  - /home/shzd/Projects/tridz/visa_tracker/.git/HEAD
created: 2026-07-21
updated: 2026-07-21
---

# TASK-001: Preflight and branch setup

## Objective

Establish the exact source/runtime baseline and safe branch/worktree layout required before any FEAT-001 feature implementation begins. This task is purely reconnaissance, setup, and planning evidence; it must not implement feature logic.

## Context

FEAT-001 spans `the_visaguy`, `fileflo`, `passport_extractor`, and `visa_tracker`. The workspace already records high-level intent, architecture, and decisions (ADR-001 through ADR-005), but the implementation agent needs verified answers for exact FileFlo record structure, field-ID persistence, Lead/File Collection/PF Process File relationships, and the current branch/dirty state of each target repository. This task replaces those assumptions with source evidence and prepares clean, isolated branches or worktrees for the implementation work that follows.

## Inputs

- `features/ongoing/visa-tracking/README.md`
- `features/ongoing/visa-tracking/01-architecture-and-data-model.md`
- `decisions/ADR-003-feat-001-repository-ownership-and-dependency-direction.md`
- `decisions/ADR-004-passport-extraction-app-and-async-processing-boundary.md`
- `decisions/ADR-005-public-tracking-security-and-privacy-model.md`
- Local frontend workspace at `/home/shzd/Projects/tridz/`
- Remote Frappe bench at `/home/shahzad/bench` on `erpcode.tridz.in:2257`
- Installed Frappe apps on the bench, including `the_visaguy`, `fileflo`, and `processflo`

## Required behaviour

1. **Exact source/runtime reconnaissance**
   - Confirm the local paths of `the_visaguy`, `fileflo`, and `processflo` on the remote bench.
   - Record the current Frappe, ERPNext, and installed app versions.
   - Identify the exact FileFlo DocType and persisted-field structure used for form submissions.
   - Identify the exact property that holds the stable field ID for a submitted FileFlo value.
   - Identify the exact File Collection-to-Lead relationship path.
   - Identify the exact Lead-to-PF Process File creation/link path.
   - Determine whether both ERPNext Lead and CRM Lead require tracking Links in the deployed flow.

2. **Clean-state checks**
   - Verify the current branch and working-tree state of `the_visaguy` and `fileflo`.
   - Verify the dirty working-tree state of `processflo` and confirm it does not conflict with planned custom fields supplied by `the_visaguy`.
   - Confirm no uncommitted FEAT-001 changes already exist on any target repository.
   - Record any non-standard branches currently checked out.

3. **Safe feature branch or dedicated worktree setup**
   - For `the_visaguy` and `fileflo`: create a `feat/visa-tracker` branch from the current default branch, or create a dedicated git worktree for `feat/visa-tracker`, leaving the default branch untouched.
   - For `passport_extractor`: scaffold the new app locally on the bench, make an initial scaffold commit, then create `feat/visa-tracker`.
   - For `visa_tracker`: initialize `/home/shzd/Projects/tridz/visa_tracker` with a Vite + React + TypeScript scaffold, initialize Git, and commit the scaffold.
   - For `processflo`: do not create a branch or make commits unless reconnaissance proves a direct source change is unavoidable. If unavoidable, create `feat/visa-tracker` first and record the deviation.

4. **Planning/scaffold preparation for passport_extractor**
   - Record the intended app structure, module name, and initial dependencies.
   - Confirm the target bench can import the new app and that it is dependency-free relative to FileFlo, ProcessFlo, Lead, Customer, and Visa Tracking Application.

5. **Local initialization of /home/shzd/Projects/tridz/visa_tracker**
   - Use the approved frontend stack: React, Vite, TypeScript, React Router, Tailwind CSS, shadcn/ui, Axios, React Hook Form, Zod.
   - Initialize Git and make a scaffold commit.
   - No Git remote is required for this repository.
   - Do not copy Next.js-specific routing, image, server, environment, authentication, or data-fetching code from `visaguy-website-client`.

## Constraints

- Work only in `/home/shzd/Projects/workspaces/visaguy_workspace` and the explicitly named application repositories.
- Do not modify any application repository from its current default/non-feature branch.
- Do not stash, commit, reset, clean, or otherwise alter unrelated dirty working trees.
- Do not implement FEAT-001 feature logic, DocTypes, APIs, OCR pipeline, or public SPA screens.
- Do not push to any Git remote.
- Do not access or copy production data, secrets, passport samples, or sensitive raw data.
- Do not copy design assets, fonts, or images from `visaguy-website-client` unless they are already approved for reuse and committed into `visa_tracker` without secrets.
- Record only environment variable names, not values.

## Expected changes

- Updated reconnaissance notes in `ongoing/visa-tracking-implementation/` or a new evidence document referenced from TASK-001.
- New `feat/visa-tracker` branches or worktrees in `the_visaguy` and `fileflo`.
- New `passport_extractor` app scaffold with an initial commit and a `feat/visa-tracker` branch.
- New `/home/shzd/Projects/tridz/visa_tracker` directory with Vite scaffold and an initial Git commit.
- No changes to `processflo` unless a deviation is recorded.

## Validation

- [x] Each target repository path exists and its current branch/dirty state is recorded.
- [x] `git status` on default branches of `the_visaguy` and `fileflo` is clean or documented as unrelated.
- [x] `feat/visa-tracker` branch or worktree exists for `the_visaguy` and `fileflo`.
- [x] `passport_extractor` scaffold initializes without import errors on the bench.
- [x] `/home/shzd/Projects/tridz/visa_tracker` exists, contains a Vite scaffold, and has at least one Git commit.
- [x] Exact FileFlo field-ID property and Lead/PF Process File relationship paths are documented with source references.
- [x] No FEAT-001 feature code, secrets, or production data are committed.

Evidence is recorded in `ongoing/visa-tracking-implementation/04a-task-001-recon-and-setup.md` and `ongoing/visa-tracking-implementation/04b-task-001-finish-setup.md`.

## Definition of done

- All validation items are checked with evidence recorded in the workspace.
- The task is moved to `tasks/completed/visa-tracking/` with metadata status `completed` only after all validation evidence is recorded.
- Implementation agents can pick up TASK-002 knowing the exact integration points and branch layout.

## Stop conditions

Stop this task and record a workspace decision request if any of the following occur:

1. **Dirty default branches**: `the_visaguy` or `fileflo` has uncommitted changes on its default branch that cannot be safely isolated in a feature branch or worktree.
2. **Unexpected branches**: a target repository is on a non-standard branch and there is no safe way to create `feat/visa-tracker` from the intended default branch.
3. **Missing repositories**: `the_visaguy`, `fileflo`, or `processflo` cannot be located on the bench, or `/home/shzd/Projects/tridz/visa_tracker` cannot be created.
4. **Contradictory integration evidence**: the exact FileFlo persisted record, field-ID property, File Collection-to-Lead relationship, or Lead-to-PF Process File path contradicts the assumptions in FEAT-001 or `01-architecture-and-data-model.md`.
5. **Unsafe remote state**: SSH access is unavailable, the bench is in an inconsistent state, or remote mutation commands would affect unrelated apps or production data.
6. **Permission denial**: any required repository operation is denied by host policy or user approval.

## Completion notes

Completed on 2026-07-21.

- **runtime-verified**: `passport_extractor` 0.0.1 is installed on site `visaguy` and imports successfully from the bench environment.
- **statically-verified**: FileFlo persistence uses `FF File Collection`, `FF File Collection File`, `FF File Collection Data`, and stable `field_id`; Lead/CRM Lead to File Collection and PF Process File joins are recorded with source paths in the phase 04a evidence.
- Clean `feat/visa-tracker` worktrees exist for `the_visaguy`, `fileflo`, and `passport_extractor`; original checkouts remain clean and unchanged except the pre-existing `processflo` dirty file, which was not touched.
- Local frontend scaffold commit: `20b8c45` in `/home/shzd/Projects/tridz/visa_tracker`; lint passes with one generated shadcn warning and production build passes.
- Passport extractor scaffold commit: `07b8cab40cd4054b39a78f23a271d7201e71baa0`.
- No repositories were pushed and no Git remote was added for the new frontend or extractor app.
- Known environment limitation: Bench asset building uses Node.js 12.22.9 and fails Frappe 15's Node >=18 requirement. The empty app installed and imports successfully, but the bench Node runtime must be corrected before asset-producing backend work requires a build.
