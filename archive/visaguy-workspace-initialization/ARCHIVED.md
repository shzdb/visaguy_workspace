# Archived: workspace initialization effort

**Archived:** 2026-08-06
**Reason:** All nine phases (1a, 1b, 2, 3a–3d, 4, 5) are recorded `completed` in `STATE.md`. The effort produced the canonical documentation now living in `docs/`, `decisions/`, and the lifecycle folders. It no longer represents active work and was incorrectly sitting in `ongoing/`.

## What this directory is

Frozen reconnaissance evidence, captured 2026-07-20 and 2026-07-21. It is the source record behind the canonical documentation and remains useful for tracing why a claim was made.

## Do not update these files

The facts here are deliberately **not** maintained. They describe the bench as it was in July 2026 and several are now stale by design:

- 29 bench apps / 27 site-installed — now 30 / 28 (`passport_extractor` added).
- `fileflo` on `fix/mandatory-file` — now `feat/visa-tracker`.
- `visaguy_crm` HEAD `b59c3ef` — now `1b28a82`.
- Local frontend paths under `/home/shzd/...` — those clones no longer exist on the active workstation.
- 32 repositories — now 33.

For current facts use `docs/architecture/repository-catalog.md`, which is verified against the live bench.

## Where its content went

| Recon report | Canonical destination |
|---|---|
| `01a-local-frontends.md` | `docs/architecture/frontends.md` |
| `01b-remote-bench.md` | `docs/architecture/repository-catalog.md` |
| `03a-maintained-apps.md` §3 workflows W1–W5 | `docs/architecture/workflows.md` (canonicalized 2026-08-06) |
| `03a-maintained-apps.md` §4 interface tables | `docs/architecture/frappe-apps.md`, `docs/architecture/workflows.md` |
| `03b-external-apps.md` | `docs/architecture/frappe-apps.md` |
| `03c-frontends.md` | `docs/architecture/frontends.md`, `docs/product/capabilities.md` |
| `03d-integrations-procedures.md` | `docs/architecture/integrations.md`, `docs/architecture/customizations.md`, `docs/operations/*` |

The W1–W5 workflows were the one substantial body of content that phase 4 left behind in evidence rather than promoting into `docs/`. That gap was closed on 2026-08-06.
