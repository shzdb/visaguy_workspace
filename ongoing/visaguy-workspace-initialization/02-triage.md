# Phase 2 — Orchestrator triage and documentation map

Date: 2026-07-20

## Evidence accepted

- Local frontends: 3 clean repositories, exact HEADs recorded in `01a-local-frontends.md`.
- Remote bench: 29 app repositories inventoried; 27 installed on site `visaguy` and 2 bench-only.
- Ownership: 18 internally maintained repositories under `tridz-dev`/`tvgglobal`; 11 external/upstream repositories.
- Runtime baseline: Frappe 15.113.0, ERPNext 15.106.0, HRMS 15.45.2, Python 3.10.12; system Node 12.22.9 while Socket.IO explicitly uses Node 18.20.8.
- Highest-impact customizations verified directly in `hooks.py`: business permission hooks and document events, CRM overrides/events/permission conditions, HRMS class/method/permission overrides.
- All three frontends call Frappe surfaces; two keep long-lived credentials/tokens in browser local storage and the eligibility checker performs unauthenticated direct lead writes.

## Corrections and evidence cautions

- `sites/apps.txt` represents bench app availability/order. Site installation is authoritative from `bench --site visaguy list-apps`: 27 apps.
- `employee_self_service` and `mansico_meta_integration` exist on the bench but are not installed on site `visaguy`.
- Integration settings DocType presence proves capability/configuration surface, not that a provider is configured or actively used. Canonical docs must distinguish present, source-wired, configured, and runtime-verified.
- The five dirty repositories predate this work. Their diffs were intentionally not read; runtime/source conclusions involving them are statically verified at current checkout only.
- Generated recon import samples and some normalized integration paths are discovery aids, not canonical citations. Canonical docs should cite repository files/symbols or stable report sections.

## Architecture synthesis

VisaGuy is a Frappe v15 multi-application platform with three independent web frontends:

1. A public visa eligibility experience with a small FastAPI/OpenAI companion backend plus direct Frappe CRM writes.
2. A Next.js business/B2B portal using OAuth tokens and custom Frappe business APIs.
3. A Next.js consumer/e-commerce portal using OTP login and Frappe API-key authentication.

The Frappe site combines upstream ERP/HR/CRM/Helpdesk/chat/payment capabilities with internally maintained domain apps. The dominant internal capability layers are:

- core VisaGuy domain and communication: `the_visaguy`;
- legacy operational CRM: `visaguy_crm`;
- Frappe CRM fork and migration/customization: `crm` + `visaguy_frappe_crm`;
- business/B2B ordering and wallet: `visaguy_business`;
- consumer website/e-commerce APIs: `visaguy_website`;
- case/process/document workflows: `processflo` + `fileflo`;
- HR, helpdesk, and Raven custom layers: `visaguy_hrms`, `visaguy_helpdesk`, `visaguy_raven` over their corresponding base apps;
- messaging and automation: `waflo`, `frappe_whatsapp`, `frappe_notifier`, `otp_authentication`;
- payments and attribution: `payments`, `payment_integrations`, `frappe_conversions_api`.

## Risk triage

### Blockers to claiming a fully runtime-verified architecture

- Five remote working trees are dirty: `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`.
- No production configuration values, database records, queues, or live external-provider calls were inspected; active configuration and runtime traffic remain intentionally unverified.
- Responsibility/precedence among the three CRM layers must be documented from hook/import/interface evidence and confirmed by maintainers.

### High-priority documentation risks

- Browser token/API-secret storage in both Next.js frontends.
- Guest-style direct Frappe writes by the eligibility checker.
- System Node 12 versus Socket.IO Node 18 runtime split.
- Non-standard deployment branches (`fix/mandatory-file`, `modification_develop_branch`, `tridz-dev`, `email`).
- Sparse automated tests in several internal customization apps.

### Non-blocking limitations

- External apps need role/provenance/version documentation, not exhaustive upstream internals.
- Settings DocTypes should be cataloged without claiming provider activation.
- Application build/deployment commands can be documented as evidenced procedures without executing production mutations.

## Canonical documentation map

- `README.md`: project purpose, workspace role, quick navigation.
- `AGENTS.md` and `.agents/`: discovery, rules, templates, repository boundaries.
- `docs/product/overview.md`: users, surfaces, capability map.
- `docs/architecture/system-overview.md`: end-to-end topology and trust boundaries.
- `docs/architecture/repository-catalog.md`: all 32 repositories (29 bench apps + 3 frontends), ownership, installed status, role, source evidence.
- `docs/architecture/frappe-apps.md`: maintained app responsibilities, fork/wrapper relationships, dependencies, hooks, DocTypes, APIs.
- `docs/architecture/frontends.md`: routes, data/auth models, backend contracts, builds.
- `docs/architecture/customizations.md`: overrides, fixtures, workflows, permissions, events, schedulers, patches.
- `docs/architecture/integrations.md`: service/provider surfaces and verification levels.
- `docs/operations/local-development.md`: safe local setup/build/test commands by repository.
- `docs/operations/bench-operations.md`: site inspection, migrate/build/restart/update/backup procedures with safety gates.
- `docs/operations/deployment.md`: evidenced topology, release sequence, rollback/validation checkpoints; unresolved production details labeled.
- `docs/security-and-privacy.md`: credentials, auth, PII/lead flows, CORS/guest API risks, secret handling.
- `docs/risks-and-open-questions.md`: dirty trees, branch drift, overlaps, missing runtime facts.
- `decisions/ADR-001-workspace-and-repository-authority.md`: workspace versus application authority.
- `decisions/ADR-002-app-ownership-classification.md`: maintained organization rule and fork treatment.

## Execution phases

- Phase 3a: deepen the 18 maintained Frappe apps and map exact responsibilities/interfaces.
- Phase 3b: produce a concise external app/version/install-role catalog and note local deviations only.
- Phase 3c: transform the accepted frontend recon into reader-focused architecture/procedure material.
- Phase 3d: reconcile customizations, integrations, security boundaries, and operations across backend/frontends.
- Phase 4: initialize the canonical workspace using the supplied templates and phase outputs.
- Phase 5: verify links, ownership/install counts, source citations, status folders, secret exclusions, and checklist completeness.
