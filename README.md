# VisaGuy Workspace

This repository is the canonical project workspace for **VisaGuy**, a Frappe v15 multi-application platform for visa services. It records product intent, architecture, decisions, procedures, risks, and status. It does **not** contain application code, secrets, production data, or generated artifacts.

## Workspace role

- Authoritative for: product requirements, architecture understanding, decisions, procedures, risks, open questions, feature/task status.
- Not authoritative for: implementation details, tests, generated schemas, build outputs, or release versions. Those live in the application repositories.
- All implementation work must start from a task marked `ready` and follow `.agents/rules/project-rules.md`.

## Current implementation snapshot

- **Runtime baseline** (bench `fasil-bench2`, checked 2026-11-12): Frappe 15.124.0, ERPNext 15.124.1, HRMS 15.64.6, Payments 0.0.1, Python 3.11.17.
- **Bench**: 32 app directories in `apps/`; 29 installed on site `visaguy`; 3 bench-only (`agentflo`, `frappe_messenger`, `seller`).
- **Ownership**: 18 internally maintained repositories under `tridz-dev` or `tvgglobal`; 11 external/upstream repositories.
- **Frontends**: 3 independent web frontends:
  1. Public visa eligibility checker (React 19 + Vite 7 + FastAPI/OpenAI companion).
  2. B2B business portal (Next.js 15.2.8 + OAuth2).
  3. Consumer website/e-commerce portal (Next.js 15.3.5 + OTP login).
- **Known blockers before clean upgrades**: 5 dirty working trees (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`); several non-standard branches; overlapping CRM/helpdesk/HRMS/Raven customization layers.

## Start here

1. Read `.agents/rules/project-rules.md` before any work.
2. Read `docs/index.md` for the canonical documentation map.
3. Read `docs/architecture/system-overview.md` for topology and trust boundaries.
4. Read `docs/risks-and-open-questions.md` for the current risk register.
5. For implementation work, pick a task from `tasks/ready/` after reading the relevant feature document.

## Repository boundaries

- Workspace: `/home/fasil/fasil-bench2/visaguy_workspace/`, inside the bench folder on `code.tridz.in`. It moved here from `/home/fasil/Tridz/visaguy_workspace/`.
- Working bench: `/home/fasil/fasil-bench2` on `code.tridz.in` (SSH: `ssh -p 2203 fasil@code.tridz.in`; user `fasil`; site `visaguy`). App code is in `/home/fasil/fasil-bench2/apps/`.

Do not write application code, secrets, or production data into this workspace. The old local bench `/home/fasil/Tridz/bench_v15` is not the working site.
