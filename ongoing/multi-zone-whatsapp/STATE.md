# Ground facts

Verified 2026-08-06. Executors must not re-derive these.

- Task: implement [FEAT-002](../../features/planned/multi-company-whatsapp/README.md), modifications M1–M6b and M9–M16.
- **Scoped by Zone, not Company.** Zone is the customer-facing market; Company is the employing legal entity. `TVG India` is back office and serves other zones. See [ADR-006](../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) and [ADR-007](../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md).
- Repos and branches, both `feat/multi-zone-whatsapp`:
  - `waflo` @ `56899f2` — branched off `feat/waflo-correctness`, **not** off `develop`.
  - `the_visaguy` @ `e690b5b` — branched off `main`.
- Executor: Cursor CLI at `/Users/shzd/.local/bin/agent`. Invoke by absolute path; `-p -f`.
- `visaguy` on `erpcode.tridz.in` is a **development** site. Production is a separate, inaccessible server.
- No delayed-enqueue exists on this bench. `frappe.enqueue(timeout=)` is RQ `job_timeout`, not a delay; `bench worker` runs without `--with-scheduler`.
- One site per bench — no cache key prefixing.
- **No agent merges or deploys.** ADR-008.

## Deployment coupling — consequence of the branch base

`waflo`'s FEAT-002 work sits **on top of** `feat/waflo-correctness` because M1–M4 restructure the same `send_whatsapp_template` that FEAT-003 rewrote. Branching off `develop` would guarantee conflicts in `send.py`.

Consequence: **deploying FEAT-002 deploys FEAT-003 with it.** They can no longer ship independently. TASK-017's prerequisites therefore also gate FEAT-002.

## Owner decisions applied

- **M7/M8 deferred.** The extensible `Whatsapp Event Type` DocType is not needed for Qatar — Qatar uses the same six event types, only the templates differ. Dropping it removes a schema migration from this run.
- **Missing or disabled zone configuration: skip, but log a warning.** Not silent. A misconfigured zone must not look identical to a working one. Never fall back to the default account — a Qatar customer must never receive a UAE-numbered message.
- **Explicit per zone.** No template inheritance between zones. M9 validation rejects enabling a zone with gaps.

## Template naming convention (settled)

`WhatsApp Templates` is autonamed `format:{template_name}-{language_code}` and `lead_form-en` is taken by `Visaguy UAE`. Additional zones use a zone-suffixed `template_name` with an unchanged `actual_name`, which is what `send.py` puts in the Meta payload.

# Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 1 | Recon across both repos | `01-recon.md` | pending |
| 2 | Triage (orchestrator) | `02-triage.md` | pending |
| 3a | `waflo` send path — M1–M4 | `03a-waflo-routing.md` | pending |
| 3b | `the_visaguy` config model — M5, M6, M6b, M9 + migration | `03b-config-model.md` | pending |
| 3c | `the_visaguy` handlers — M10–M16 | `03c-handlers.md` | pending |
| 4 | Verify on `visaguy` | `04-verify.md` | pending |
| 5 | Final report + workspace reconciliation | — | pending |

# Decisions log

- 2026-08-06: `waflo` branched off `feat/waflo-correctness` rather than `develop`, accepting deployment coupling, because both features restructure `send_whatsapp_template`.
- 2026-08-06: `the_visaguy` branched off `main`. Its unmerged `feat/visa-tracker` adds a separate `visa_tracking/` module and does not touch `handlers/whatsapp_message.py`, so the two branches are independent.
- 2026-08-06: M7/M8 deferred; skip-with-warning on missing config; explicit per-zone configuration, no inheritance.
