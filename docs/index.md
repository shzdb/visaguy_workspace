# VisaGuy Documentation

Canonical map and reading paths for the VisaGuy workspace.

## Quick start

- New to the project? Read [`product/overview.md`](product/overview.md) and [`architecture/system-overview.md`](architecture/system-overview.md).
- Need to understand how a feature works end to end? Read [`architecture/workflows.md`](architecture/workflows.md).
- Looking for a specific repository? Read [`architecture/repository-catalog.md`](architecture/repository-catalog.md).
- Planning implementation work? Read `.agents/rules/project-rules.md`, then [`features/README.md`](../features/README.md) and [`tasks/README.md`](../tasks/README.md).
- Reviewing risks? Read [`risks-and-open-questions.md`](risks-and-open-questions.md) and [`security-and-privacy.md`](security-and-privacy.md).

## Reading paths

### Product

- [`product/overview.md`](product/overview.md) — users, surfaces, and product scope.
- [`product/capabilities.md`](product/capabilities.md) — capability map and status.

### Architecture

- [`architecture/system-overview.md`](architecture/system-overview.md) — topology, trust boundaries, verified vs unresolved joins.
- [`architecture/workflows.md`](architecture/workflows.md) — **end-to-end code flows** (W1–W9): entry point → hook → service → DocType → downstream effect. Read this to understand how a feature is actually built.
- [`architecture/repository-catalog.md`](architecture/repository-catalog.md) — all 33 repositories with ownership, install status, version/HEAD, and role.
- [`architecture/frappe-apps.md`](architecture/frappe-apps.md) — per-app responsibility and interface inventory (what each app owns), and external app roles.
- [`architecture/frontends.md`](architecture/frontends.md) — frontend architecture, auth models, and API contracts.
- [`architecture/customizations.md`](architecture/customizations.md) — customization precedence, hooks, overrides, fixtures, schedulers, patches, and upgrade gates.
- [`architecture/integrations.md`](architecture/integrations.md) — integration matrix using the four-level verification model.

### Operations

- [`operations/local-development.md`](operations/local-development.md) — safe local setup, build, lint, and test commands.
- [`operations/bench-operations.md`](operations/bench-operations.md) — site inspection, migrate/build/restart/update/backup procedures.
- [`operations/deployment.md`](operations/deployment.md) — deployment topology, release sequence, rollback, and validation checkpoints.

### Security, risks, and decisions

- [`security-and-privacy.md`](security-and-privacy.md) — auth storage, CORS/guest access, PII/uploads, provider secrets, and recommended follow-up decisions.
- [`risks-and-open-questions.md`](risks-and-open-questions.md) — evidence-backed risk register and unresolved questions.
- [`decisions/README.md`](../decisions/README.md) — ADR index and running decision log. Start here, not with the individual files.

## Authority model

- This workspace is authoritative for intent, architecture, decisions, procedures, risks, and status.
- Application repositories are authoritative for implementation, tests, generated schemas, builds, and releases.
