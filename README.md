# VisaGuy Workspace

This repository is the canonical project workspace for **VisaGuy**, a Frappe v15 multi-application platform for visa services. It records product intent, architecture, decisions, procedures, risks, and status. It does **not** contain application code, secrets, production data, or generated artifacts.

## Workspace role

- Authoritative for: product requirements, architecture understanding, decisions, procedures, risks, open questions, feature/task status.
- Not authoritative for: implementation details, tests, generated schemas, build outputs, or release versions. Those live in the application repositories.
- All implementation work must start from a task marked `ready` and follow `.agents/rules/project-rules.md`.

## Current implementation snapshot

Verified against the remote bench on 2026-08-06.

- **Runtime baseline**: Frappe 15.113.0, ERPNext 15.106.0, HRMS 15.45.2, Payments 0.0.1, Python 3.10.12.
- **Bench**: 30 app repositories available; 28 installed on site `visaguy`; 2 bench-only (`employee_self_service`, `mansico_meta_integration`). A second site, `visa-tracker-test.localhost`, carries 8 apps for FEAT-001 testing.
- **Ownership**: 19 internally maintained repositories under `tridz-dev` or `tvgglobal`; 11 external/upstream repositories.
- **Frontends**: 3 independent web frontends, plus a fourth planned:
  1. Public visa eligibility checker (React 19 + Vite 7 + FastAPI/OpenAI companion).
  2. B2B business portal (Next.js 15.2.8 + OAuth2).
  3. Consumer website/e-commerce portal (Next.js 15.3.5 + OTP login).
  4. `visa_tracker` public status SPA — **planned, not started** (FEAT-001 TASK-008).
- **Active feature work**: [FEAT-001 visa tracking and passport extraction](features/ongoing/visa-tracking/README.md). Backend complete on `feat/visa-tracker` in `the_visaguy`, `fileflo`, and `passport_extractor`; all pushed to upstream; **nothing merged or deployed**. The SPA is not started.
- **Known blockers before clean upgrades**: 5 dirty working trees (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`); several non-standard branches; overlapping CRM/helpdesk/HRMS/Raven customization layers; 3 unmerged FEAT-001 feature branches.

## Start here

1. Read `.agents/rules/project-rules.md` before any work.
2. Read `docs/index.md` for the canonical documentation map.
3. Read `docs/architecture/system-overview.md` for topology and trust boundaries.
4. Read `docs/architecture/workflows.md` for end-to-end code flows.
5. Read `docs/risks-and-open-questions.md` for the current risk register.
6. For implementation work, pick a task from `tasks/ready/` after reading the relevant feature document.

## Repository boundaries

- Workspace: this repository. Currently checked out at `/Users/shzd/Projects/tridz/workspaces/visaguy_workspace` (macOS). Earlier documentation recorded a Linux path; do not rely on absolute local paths.
- Remote bench: `/home/shahzad/bench` on `erpcode.tridz.in:2257` (SSH host alias `erpcode`). **Read-only** except where a task explicitly authorises otherwise.
- Application repositories: `tridz-dev` and `tvgglobal` on the `tridz` Git host, plus upstream Frappe projects. See `docs/architecture/repository-catalog.md`.

### Frontend repositories — not currently cloned

None of the three frontend repositories is present on the active workstation. Clone them read-only before any frontend work or design-parity assessment:

- `tvgglobal/visa_eligibility_checker`
- `tridz-dev/visaguy_business_client`
- `tvgglobal/visaguy-website-client`

`visaguy-website-client` is a hard prerequisite for FEAT-001 TASK-008.

Do not write application code, secrets, or production data into this workspace.

## Deployment authority

Merging application repositories to `develop`/`main` and deploying to staging or live are **manual, project-owner-only** actions. No agent performs them. Staging and live are separate events, confirmed separately. See `.agents/rules/project-rules.md`.
