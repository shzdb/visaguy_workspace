# Phase 4 — Workspace Initialization

Date: 2026-07-20
Status: completed

## Created files

### Root

- `README.md`
- `AGENTS.md`

### `.agents/`

- `.agents/README.md`
- `.agents/rules/project-rules.md`
- `.agents/skills/implementation-audit.md`
- `.agents/templates/feature.md`
- `.agents/templates/task.md`
- `.agents/templates/decision.md`
- `.agents/templates/completion-report.md`

### `docs/`

- `docs/index.md`
- `docs/product/overview.md`
- `docs/product/capabilities.md`
- `docs/architecture/system-overview.md`
- `docs/architecture/repository-catalog.md`
- `docs/architecture/frappe-apps.md`
- `docs/architecture/frontends.md`
- `docs/architecture/customizations.md`
- `docs/architecture/integrations.md`
- `docs/operations/local-development.md`
- `docs/operations/bench-operations.md`
- `docs/operations/deployment.md`
- `docs/security-and-privacy.md`
- `docs/risks-and-open-questions.md`

### `decisions/`

- `decisions/ADR-001-workspace-and-repository-authority.md` (Accepted)
- `decisions/ADR-002-app-ownership-classification.md` (Accepted)

### Lifecycle folders

- `features/README.md`
- `features/planned/.gitkeep`
- `features/ongoing/.gitkeep`
- `features/completed/.gitkeep`
- `features/parked/.gitkeep`
- `tasks/README.md`
- `tasks/ready/.gitkeep`
- `tasks/in-progress/.gitkeep`
- `tasks/blocked/.gitkeep`
- `tasks/completed/.gitkeep`
- `research/README.md`
- `archive/README.md`

Total created files: 30 content files + 8 `.gitkeep` files = 38 files.

## Assumptions

- The accepted evidence from phases 1a, 1b, 2, 3a, 3b, 3c, and 3d is accurate and complete enough for canonicalization.
- Repository ownership follows the rule in `ADR-002`: `tridz-dev` or `tvgglobal` remotes are internally maintained; all others are external.
- `crm` and `helpdesk` are maintained forks and are counted as internally maintained.
- `sites/apps.txt` (29 apps) represents bench availability; `bench --site visaguy list-apps` (27 apps) represents site installation.
- No application code, secrets, production data, dirty diffs, or generated artifacts were added to the workspace.

## Unresolved questions

See `docs/risks-and-open-questions.md` for the full register. Key unresolved items include:

- Runtime precedence among the three CRM layers (`crm`, `visaguy_crm`, `visaguy_frappe_crm`).
- Runtime precedence among helpdesk layers (`helpdesk`, `visaguy_helpdesk`).
- Runtime precedence among Raven layers (`raven`, `visaguy_raven`).
- Whether the consumer website calls `visaguy_business.create_process_file` (no frontend evidence).
- Exact backend owners of `Raw Lead`, `Lead`, `Applicant Type`, `Destination`, `Destination Mode`, `Destination Region`, and `FF File Collection` from the frontend perspective.
- Active configuration and traffic for all external-provider integrations (WhatsApp, Twilio/Exotel, FCM, Meta/Google, MyFatoorah/TotalPay, OTP gateway, backups).

## Verification gates checked

- [x] All listed files exist.
- [x] Template copies preserve template fields/headings.
- [x] Repository counts: 32 total, 29 bench apps, 18 maintained, 11 external, 27 site-installed, 2 bench-only, 3 frontends.
- [x] No feature/task document invented; lifecycle folders exist and READMEs explain entry criteria.
- [x] Operational commands match corrected phase 3d (`bench doctor --site visaguy`, `bench --site visaguy backup --with-files`, explicit restore archive flags).
- [x] No application code, secrets, config values, production data, raw logs, dirty filenames/diffs, or generated artifacts included.

## Next actions

1. Phase 5: evidence verification and consistency audit (`05-verification.md`).
2. Reconcile dirty working trees before any upgrade or production deployment.
3. Resolve runtime precedence questions for CRM, helpdesk, and Raven layers with maintainers.
4. Conduct a follow-up audit of active external-provider configurations and traffic.
5. Populate `tasks/ready/` with the first implementation tasks derived from accepted features.
