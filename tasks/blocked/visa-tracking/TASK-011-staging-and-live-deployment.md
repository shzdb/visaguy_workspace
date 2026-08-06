---
id: TASK-011
feature: FEAT-001
title: Merge dependent apps and deploy to staging, then live
status: blocked
repository: multiple
owners:
  - project-owner
depends_on:
  - TASK-010
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Merge dependent apps and deploy to staging, then live

## Objective

Promote the `feat/visa-tracker` work across all dependent applications into `develop` and then `main`, and deploy it to staging and to live as two separate, independently confirmed events.

## Ownership — manual, project owner only

**This task is performed manually by the project owner. No agent may merge, deploy, or change branch state for this task.**

An agent's role here is limited to: preparing the change list, reporting current branch state, and recording confirmed outcomes in this workspace after the owner reports them.

## Repositories in scope

| Repository | Feature branch | Current head | Merge target sequence |
|---|---|---|---|
| `the_visaguy` | `feat/visa-tracker` | `8254f93` | `develop` → `main` |
| `fileflo` | `feat/visa-tracker` | `c7244a4` | `develop` → `main` |
| `passport_extractor` | `feat/visa-tracker` | `0216829` | `develop` → `main` |
| `visa_tracker` (SPA) | n/a — not yet created | — | per TASK-008 once a remote exists |
| `processflo` | not branched | `develop` | no change |

All three backend feature branches are pushed to their `tridz-dev` / `tvgglobal` upstreams as of 2026-08-06.

## Merge order

Dependencies require this order. `the_visaguy` subscribes to a hook that `fileflo` must already provide, and orchestrates a DocType that `passport_extractor` must already define.

1. `fileflo` — provides the `fileflo_extension_handlers` extension point.
2. `passport_extractor` — provides the `Passport Extraction` DocType.
3. `the_visaguy` — subscribes to the hook and links the extraction.

## Prerequisite: reconcile blockers

Before deployment, the standing upgrade gates in `docs/architecture/customizations.md` apply. In particular `processflo` still has a dirty working tree on the bench; it is not in scope for a code change but it sits in the same runtime.

The bench working copy of `the_visaguy` is currently checked out on `main`, and stale `visa_tracking/**/__pycache__/` files remain from the feature branch. These must be cleared before or during deployment to avoid stale-bytecode imports.

## Gate 1 — staging deployment

Confirmed separately from Gate 1. Record here:

- Date staged:
- Apps merged to `develop`:
- Staging site:
- `bench migrate` result:
- Fixture import result:
- Smoke test result:
- Confirmed by:

## Gate 2 — live deployment

Confirmed separately from Gate 1. Record here:

- Date deployed live:
- Apps merged to `main`:
- Live site:
- `bench migrate` result:
- Rollback point (pre-deploy backup / tag):
- Post-deploy validation:
- Confirmed by:

## Definition of done

Both gates are recorded above with the project owner's explicit confirmation.

**FEAT-001 must not be moved to `features/completed/` until both Gate 1 and Gate 2 are confirmed.** Staging confirmation alone is not sufficient. Any agent asked to mark FEAT-001 complete must ask the project owner these two questions separately:

1. Has the visa tracker been **deployed to staging**?
2. Has the visa tracker been **deployed live**?
