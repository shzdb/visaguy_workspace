# Project Rules

## Repository boundaries

- Keep the workspace separate from application code repositories.
- Treat this workspace as authoritative for intent, architecture decisions, procedures, risks, open questions, feature scope, and status.
- Treat application repositories as authoritative for implementation, tests, generated schemas, builds, and releases.
- VisaGuy maintained organizations are `tridz-dev` and `tvgglobal`. Repositories owned by these organizations are internally maintained; `crm` and `helpdesk` are maintained forks. All other owners are external.

## Bench evidence and execution

- Build application code only on the bench `/home/fasil/fasil-bench2` on `code.tridz.in`, site `visaguy`. See `docs/operations/environment.md`.
- This workspace is at `/home/fasil/fasil-bench2/visaguy_workspace`, inside that bench folder. Run `bench`, `git` and site commands there directly; use `ssh -p 2203 fasil@code.tridz.in` only from another machine.
- Do not read or edit application code on the old local bench `/home/fasil/Tridz/bench_v15`. That tree is not the working site.
- Prefer workspace files and already-accepted reconnaissance reports over repeated extraction.

## No secrets, data, or generated artifacts

- Do not commit secrets, production data, sensitive raw data, dirty diffs, database dumps, error logs, build outputs, or generated artifacts.
- Record only environment variable names, not values.
- Do not reproduce raw file paths, credentials, or private keys from the bench or application repositories.

## Git discipline

- Do not run `git add`, `git commit`, or `git push` unless explicitly asked by the user.
- Leave all changes unstaged so the user can review and commit manually.

## Verification labels

Use these labels consistently when reporting evidence:

- **present** — settings DocType or capability surface exists in source.
- **source-wired** — hooks, imports, or caller/callee relationships are evidenced in code.
- **configured-unverified** — environment/config values observed only as key names; activation not verified.
- **runtime-verified** — live traffic or provider call confirmed.

This audit runtime-verified SSH access, installed apps, versions, and CLI help; it did not verify provider traffic or production workflows.

## App placement rules

- All HR/HRMS-related custom code and customizations must be placed in the `visaguy_hrms` app. This includes hooks, doc_events, class overrides, server scripts, client scripts, and fixtures that extend or modify HRMS, Employee, Leave, Payroll, or related doctypes.

## Customizations discipline

- **Do not use fixtures for standard DocType customizations.** This includes Custom Fields, Property Setters, and Custom DocPerms.
- Always use the **Export Customizations** action from the Customize Form view (which generates JSON files in the app's `custom/` directory) for any modifications or permission changes to standard DocTypes.
- **Frappe CRM Vue overlay:** any add, edit, delete, or re-apply under `visaguy_frappe_crm/frontend` (except `node_modules` / `dist`) must follow [`.agents/rules/frappe-crm-frontend-overrides.md`](frappe-crm-frontend-overrides.md) and update [`docs/architecture/frappe-crm-frontend-overrides.md`](../../docs/architecture/frappe-crm-frontend-overrides.md) in the same task.

## Decision and planning discipline

- Record significant architecture decisions as ADRs in `decisions/`.
- Do not mark work completed without implementation and validation evidence.
- Do not assign unresolved product or architecture decisions to implementation agents.
- Mark a task `ready` only when it requires no new product or architecture decision.

## Lifecycle alignment

- Feature states: `planned`, `ongoing`, `completed`, `parked`.
- Task states: `draft`, `ready`, `in-progress`, `blocked`, `completed`.
- Keep folder status and document metadata `status` aligned.
- A parked feature must include a reason and revisit condition.

## Scope discipline

- Do not invent product decisions or features not supported by accepted evidence.
- Do not claim the consumer website calls `visaguy_business.create_process_file`; that join is unresolved.
- Do not claim integrations are actively used unless runtime-verified.

## No commits or edits by agents without owner review

- Agents must not run `git commit`, `git add`, `git stash`, `git reset`, `git checkout -b`, `git merge`, `git push`, or any other git command that changes history or the index.
- Agents must not create, edit, move or delete files in this workspace or in any application repository under `/home/fasil/fasil-bench2/apps/`.
- Agents may read files and run read-only git commands (`status`, `log`, `diff`, `show`).
- When a change is needed, describe it and list the files. The owner reviews the working tree.
- When the owner asks to commit and push, the commit goes only to the `fasil` branch of `visaguy_workspace` and is pushed to `origin/fasil`. Never commit or push to `main`, a feature branch, or an application repository, and do not create branches.
- This applies to every repository in the bench, not only this workspace, which is the main record of the project.
