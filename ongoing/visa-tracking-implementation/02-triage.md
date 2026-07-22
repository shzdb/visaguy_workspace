# Orchestrator Triage

## Verdict

Implementation is gated by one issue: no task exists in `tasks/ready/`. The feature's missing ADR references are documentation drift, but they should be repaired before TASK-001 is marked ready because FEAT-001 names them as dependencies.

## Decision

The next executor phase will:

1. Materialize ADR-003 through ADR-005 from decisions already recorded in the accepted FEAT-001 documents; it must not add new product scope.
2. Author only TASK-001 as `ready`, scoped to preflight, exact integration reconnaissance, safe branch/worktree preparation, and initialization of the local `visa_tracker` repository.
3. Repair only links and metadata directly affected by these newly created documents.
4. Leave TASK-002 through TASK-010 and supporting specs 02-06 for later planning phases before their implementation begins.

## Policies

- TASK-001 may authorize SSH reconnaissance and safe branch/worktree setup in the named Frappe repositories, but not feature implementation.
- Existing dirty working trees must not be stashed, committed, reset, cleaned, or otherwise altered.
- No source changes are allowed on default branches.
- The frontend repository may be initialized at `/home/shzd/Projects/tridz/visa_tracker`; no remote or push is required.
- Any contradiction found between deployed source and FEAT-001 stops the affected path and is recorded for a workspace decision.
- Application work starts only after TASK-001 exists in `tasks/ready/` and the orchestrator accepts the planning-repair diff.

## Risk focus for review

- ADRs must record existing decisions rather than quietly introduce new ones.
- TASK-001 must clearly separate reconnaissance/setup from feature implementation.
- Remote mutation authority must be narrow: feature branches/worktrees only, with no dirty-tree cleanup.
- The new frontend repository must not copy secrets or Next.js-specific runtime code from the visual-reference repository.
