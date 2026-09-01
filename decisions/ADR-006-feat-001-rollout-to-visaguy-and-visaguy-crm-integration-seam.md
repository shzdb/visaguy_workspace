# ADR-006: FEAT-001 Rollout to `visaguy` and the `visaguy_crm` Integration Seam

## Status

Accepted

Amends ADR-003 (repository set) and supersedes the read-only scope constraints
recorded in TASK-010 for the 2026-07-22/23 session.

## Context

TASK-010 scoped FEAT-001 verification to the dedicated site
`visa-tracker-test.localhost` and explicitly prohibited editing application
code, running migrations on `visaguy`, or deploying. `HANDOFF.md` §8 further
characterised `visaguy` as "production and READ-ONLY; never migrate or test
against it."

On 2026-07-22 the project owner requested that the feature be made testable on
`visaguy` itself and, when shown an explicit three-way choice (test site /
deploy to `visaguy` / push branches first) including the stated consequences,
chose to deploy. The owner subsequently clarified that **`visaguy` is a
development bench**, served at `https://visaguy.erpcode.tridz.in`, not a
production system. The earlier "production, read-only" characterisation was
inaccurate and had already caused an execution agent to refuse an authorised
task.

Deploying and then exercising the feature against real traffic exposed a
structural fact that the architecture had not recorded: **the live data-collection
form does not call `fileflo.data_collection.add_form_data`.** It calls
`visaguy_crm.data_collecting_form.add_form_data`, a diverged fork of the same
function carrying extra CRM concerns (`custom_customer`, `form_submitted`,
upload-capacity re-creation). FEAT-001 had been integrated into the fileflo
original, so the integration point was bypassed entirely and could never have
fired on this bench.

## Decision

### Deployment posture

- `visaguy` is classified as a **development bench**, not production. The
  workspace must not describe it as production or as unconditionally read-only.
- FEAT-001 is deployed on `visaguy` from branch `feat/visa-tracker` in each
  participating repository.
- The "remote read-only default" in `.agents/rules/project-rules.md` continues
  to apply. Mutation of the bench remains permitted only under explicit
  authorisation, which was given for this session and is recorded here.
- `erpcode.tridz.in` remains a **shared host**. Processes belonging to other
  users must never be signalled or restarted. Only `bench start` under
  `/home/shahzad/bench` is ours.

### Repository set

- **`visaguy_crm` is added to the FEAT-001 repository set** as a fifth
  participating repository, joining `the_visaguy`, `fileflo`,
  `passport_extractor`, and `visa_tracker`.
- `visaguy_crm` hosts the live form-submission endpoint and must therefore
  carry the FileFlo extension-event dispatch and preserve `field_id`.
- The dependency direction of ADR-003 is unchanged: `passport_extractor`
  remains dependency-free, and `visaguy_crm` depends on `fileflo`, never the
  reverse.

### Known duplication

- `visaguy_crm.data_collecting_form.add_form_data` and
  `fileflo.data_collection.add_form_data` are **duplicated logic that has
  already drifted**. Both now carry the `field_id` fix independently.
- Consolidating them (making the CRM endpoint delegate to fileflo) was
  considered and deferred: it is a refactor of a live CRM path with its own
  extras, and the owner chose the lower-risk patch to unblock testing.
- Until consolidated, **any change to one must be evaluated against the other.**

## Consequences

### Positive

- The feature is exercisable against the real form flow on a real bench.
- The true integration seam is documented; future agents will not integrate
  into the fileflo original and assume coverage.
- Deployment is fast-forward-only in content terms; each pre-deploy HEAD was
  verified to be an ancestor of the deployed commit.

### Negative

- Two copies of the upload logic remain, and drift between them is now a
  standing risk.
- The `visaguy` database was migrated across **all installed apps**, not only
  the FEAT-001 apps. Pending patches in `insights`, `crm`, `raven`, `helpdesk`,
  `hrms` and others also ran. No adverse effect was observed, but the change
  surface was wider than FEAT-001.
- TASK-010's evidence was gathered partly on `visaguy` rather than exclusively
  on the dedicated test site, weakening its isolation guarantee.

## Rollback

Pre-deploy state, restorable per repository with `git checkout <branch>`:

| Repository | Pre-deploy branch | Pre-deploy HEAD |
|---|---|---|
| `the_visaguy` | `main` | `e690b5b` |
| `passport_extractor` | `develop` | `07b8cab` |
| `fileflo` | `fix/mandatory-file` | `6683010` |
| `visaguy_crm` | `main` | `b59c3ef` |

Database backup taken before migration:
`sites/visaguy/private/backups/20260722_202735-visaguy-database.sql.gz`
(restore with `bench --site visaguy restore <path>`).

## Revisit when

The duplicated upload logic is consolidated, `visaguy` changes role, or
FEAT-001 is promoted to a genuine production environment — at which point the
deployment posture above must be re-decided rather than inherited.
