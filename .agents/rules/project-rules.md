# Project Rules

## Repository boundaries

- Keep the workspace separate from application code repositories.
- Treat this workspace as authoritative for intent, architecture decisions, procedures, risks, open questions, feature scope, and status.
- Treat application repositories as authoritative for implementation, tests, generated schemas, builds, and releases.
- VisaGuy maintained organizations are `tridz-dev` and `tvgglobal`. Repositories owned by these organizations are internally maintained; `crm` and `helpdesk` are maintained forks. All other owners are external.

## Remote read-only default

- Application repositories and the remote bench are read-only sources of evidence.
- Do not execute SSH commands that mutate the remote bench or application repositories unless explicitly authorized by a task.
- Prefer local workspace files and already-accepted reconnaissance reports over new remote extraction.

## No secrets, data, or generated artifacts

- Do not commit secrets, production data, sensitive raw data, dirty diffs, database dumps, error logs, build outputs, or generated artifacts.
- Record only environment variable names, not values.
- Do not reproduce raw file paths, credentials, or private keys from the bench or application repositories.

## Verification labels

Use these labels consistently when reporting evidence:

- **present** — settings DocType or capability surface exists in source.
- **source-wired** — hooks, imports, or caller/callee relationships are evidenced in code.
- **configured-unverified** — environment/config values observed only as key names; activation not verified.
- **runtime-verified** — live traffic or provider call confirmed.

This audit runtime-verified SSH access, installed apps, versions, and CLI help; it did not verify provider traffic or production workflows.

## Decision and planning discipline

- Record significant architecture decisions as ADRs in `decisions/`.
- Do not mark work completed without implementation and validation evidence.
- Do not assign unresolved product or architecture decisions to implementation agents.
- Mark a task `ready` only when it requires no new product or architecture decision.

## Deployment authority

- Merging application repositories into `develop` or `main`, and deploying to staging or live, are **manual actions performed by the project owner**. No agent may perform them.
- An agent may prepare change lists, report branch state, and record confirmed outcomes. It may not merge, tag, deploy, or alter branch checkout state on the bench.
- Staging deployment and live deployment are **separate events** and must be confirmed separately.
- Before marking any feature `completed`, an agent must ask the project owner two distinct questions: whether the work is deployed to **staging**, and whether it is deployed **live**. Confirmation of staging alone is never sufficient.

## Lifecycle alignment

- Feature states: `planned`, `ongoing`, `completed`, `parked`.
- Task states: `draft`, `ready`, `in-progress`, `blocked`, `completed`.
- Keep folder status and document metadata `status` aligned.
- A parked feature must include a reason and revisit condition.

## Scope discipline

- Do not invent product decisions or features not supported by accepted evidence.
- Do not claim the consumer website calls `visaguy_business.create_process_file`; that join is unresolved.
- Do not claim integrations are actively used unless runtime-verified.
