# Ground facts

- Project: VisaGuy.
- Workspace: `/home/fasil/Tridz/visaguy_workspace`.
- Workspace role: documentation, architecture, decisions, procedures, planning, and status; it must not contain application code, secrets, or production data.
- Maintained Git organizations: `tridz-dev` and `tvgglobal`.
- Local frontend repository: `/home/fasil/Tridz/visa_eligibility_checker` (`tvgglobal/visa_eligibility_checker`).
- Local frontend repository: `/home/fasil/Tridz/visaguy_business_client` (`tridz-dev/visaguy_business_client`).
- Local frontend repository: `/home/fasil/Tridz/visaguy-website-client` (`tvgglobal/visaguy-website-client`).
- Remote environment: `ssh -p 2257 fasil@erpcode.tridz.in`; Frappe bench verified at `/home/fasil/fasil-bench-v15`.
- Executor: Kimi Code CLI (`kimi -p`).
- SSH public-key authentication and remote command execution were verified on 2026-07-20. The initial delay was caused by an overly broad home-directory scan, not authentication.
- Remote bench contains 29 app directories; all 29 are listed in `sites/apps.txt`.
- Remote site directory: `/home/fasil/fasil-bench-v15/sites/visaguy` (do not read secrets or production data from it).
- `bench --site visaguy list-apps` confirms 27 installed apps. `employee_self_service` and `mansico_meta_integration` are bench-only, not installed on this site.
- All investigation is read-only against application repositories and the remote server. Only this workspace may be edited.

# Phase table

| # | phase | output | status |
|---|---|---|---|
| 1a | Local frontend reconnaissance | `01a-local-frontends.md` | completed |
| 1b | Remote bench and app reconnaissance | `01b-remote-bench.md` | completed |
| 2 | Orchestrator triage and documentation map | `02-triage.md` | completed |
| 3a | Maintained Frappe app deep-dive | `03a-maintained-apps.md` | completed |
| 3b | External app and dependency inventory | `03b-external-apps.md` | completed |
| 3c | Frontend deep-dive | `03c-frontends.md` | completed |
| 3d | Integrations, customizations, and procedures | `03d-integrations-procedures.md` | completed |
| 4 | Workspace initialization and canonical docs | `04-initialization.md` | completed |
| 5 | Evidence verification and consistency audit | `05-verification.md` | completed |

# Decisions log

- 2026-07-20: Classify repositories owned by `tridz-dev` or `tvgglobal` as internally maintained; classify other app origins as external unless repository evidence proves otherwise.
- 2026-07-20: Keep application repositories read-only and create documentation only in the workspace.
- 2026-07-20: Split local and remote reconnaissance so an SSH authentication/connectivity issue does not block local evidence collection.
- 2026-07-20: Use Git remote `upstream` when present, otherwise `origin`, for ownership classification because most bench repositories name their primary remote `upstream`.
- 2026-07-20: Accepted phase 1a after source spot-checks confirmed the three highest-risk integration/authentication claims and all frontend repositories remained clean.
- 2026-07-20: Accepted phase 1b after targeted hook/Procfile source checks and a site-level installed-app query. Corrected bench availability (29) versus site installation (27).
- 2026-07-20: Canonical documentation will be organized by product/capability, system topology, repositories/apps, customizations, integrations, procedures, and risks. Recon reports remain evidence, not the primary reader entrypoint.
- 2026-07-20: Accepted phases 3a–3c after coverage and structure checks. Treat cross-report workflow joins as hypotheses unless both producer and consumer interfaces are evidenced; phase 3d must reconcile overclaims before canonicalization.
- 2026-07-20: Accepted phase 3d after correcting Bench commands against installed Bench 5.29.0 help. Context7 resolved `/frappe/bench` but returned no snippets, so installed CLI help is the command authority for this environment.
- 2026-07-21: Phase 4 created 38 canonical/lifecycle files, cataloged 32 repositories, and repaired all relative links found by its checker.
- 2026-07-21: Removed nine transient local extraction/helper artifacts and the two Kimi-created remote `/tmp` artifacts. Accepted reports/prompts remain as durable audit evidence.
- 2026-07-21: Phase 5 passed all 14 initializer checks with 0 broken links and 0 secret findings. The orchestrator reconciled its two minor evidence-label defects and corrected the stale Context7 path reference.

# Verified remote app inventory

Internally maintained (`tridz-dev` or `tvgglobal` remote):

- `crm`, `fileflo`, `frappe_conversions_api`, `frappe_notifier`, `helpdesk`, `otp_authentication`, `payment_integrations`, `processflo`, `quick_kanban`, `the_visaguy`, `visaguy_business`, `visaguy_crm`, `visaguy_frappe_crm`, `visaguy_helpdesk`, `visaguy_hrms`, `visaguy_raven`, `visaguy_website`, `waflo`.

External/upstream:

- `employee_self_service`, `erpnext`, `frappe`, `frappe_whatsapp`, `hrms`, `india_compliance`, `insights`, `mansico_meta_integration`, `non_profit`, `payments`, `raven`.
