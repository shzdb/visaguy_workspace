# VisaGuy Workspace

This repository is the canonical project workspace for **VisaGuy**, a Frappe v15 multi-application platform for visa services. It records product intent, architecture, decisions, procedures, risks, and status. It does **not** contain application code, secrets, production data, or generated artifacts.

## Workspace role

- Authoritative for: product requirements, architecture understanding, decisions, procedures, risks, open questions, feature/task status.
- Not authoritative for: implementation details, tests, generated schemas, build outputs, or release versions. Those live in the application repositories.
- All implementation work must start from a task marked `ready` and follow `.agents/rules/project-rules.md`.

## Current implementation snapshot

- **Runtime baseline**: Frappe 15.113.0, ERPNext 15.106.0, HRMS 15.45.2, Payments 0.0.1, Python 3.10.12.
- **Bench**: 33 app repositories available; 29 installed on site `visaguy-hrms`; 5 apps bench-only (`huf`, `gada_electronics`, `library_management`, `rehbar_crm`, `huf` ).
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

- Workspace: `/home/fasil/Tridz/`
- Remote bench: `/home/fasil/fasil-bench-v15` on `erpcode.tridz.in:2257`

Do not write application code, secrets, or production data into this workspace.
