# Ground facts

Verified 2026-08-06. Executors must not re-derive these.

- Task: implement [FEAT-002](../../features/ongoing/multi-zone-whatsapp/README.md), modifications M1–M6b and M9–M16.
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

The coupling is **one-way**. `feat/multi-zone-whatsapp` contains all six FEAT-003 commits, so merging it into `develop` ships both features — FEAT-003 needs no separate merge. FEAT-002 cannot ship without FEAT-003. But `feat/waflo-correctness` remains a clean fast-forward from `develop` with no FEAT-002 code, so FEAT-003 can still ship alone if the risk is to be staged. TASK-017's prerequisites gate FEAT-002 either way.

## Owner decisions applied

- **M7/M8 deferred.** The extensible `Whatsapp Event Type` DocType is not needed for Qatar — Qatar uses the same six event types, only the templates differ. Dropping it removes a schema migration from this run.
- **Missing or disabled zone configuration: skip, but log a warning.** Not silent. A misconfigured zone must not look identical to a working one. Never fall back to the default account — a Qatar customer must never receive a UAE-numbered message.
- **Explicit per zone.** No template inheritance between zones. M9 validation rejects enabling a zone with gaps.

## Template naming convention (settled)

`WhatsApp Templates` is autonamed `format:{template_name}-{language_code}` and `lead_form-en` is taken by `Visaguy UAE`. Additional zones use a zone-suffixed `template_name` with an unchanged `actual_name`, which is what `send.py` puts in the Meta payload.

# Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 1 | Recon across both repos | `01-recon.md` | done |
| 2 | Triage (orchestrator) | `02-triage.md` | done |
| 3a | `waflo` send path — M1–M4, F2, F3 | `03a-waflo-routing.md` | done — `f81fe81` |
| 3b | `the_visaguy` config model — M5, M6, M6b, M9 + migration | `03b-config-model.md` | done — `7ffaa26` |
| 3c | `the_visaguy` handlers — M10–M16, F1 | `03c-handlers.md` | done — `280ec5e` |
| 3d | Corrective — test mocks, account backfill | `03d-corrective.md` | done — `aa3ef89` |
| 4 | Verify on `visaguy` | `04-verify.md` | done — 28/28 + 13/13, migrate verified |
| 5 | Final report + workspace reconciliation | `tasks/*/multi-zone-whatsapp/` | done |

# Decisions log

- 2026-08-06: `waflo` branched off `feat/waflo-correctness` rather than `develop`, accepting deployment coupling, because both features restructure `send_whatsapp_template`.
- 2026-08-06: `the_visaguy` branched off `main`. Its unmerged `feat/visa-tracker` adds a separate `visa_tracking/` module and does not touch `handlers/whatsapp_message.py`, so the two branches are independent.
- 2026-08-06: M7/M8 deferred; skip-with-warning on missing config; explicit per-zone configuration, no inheritance.
- 2026-08-06: `bench migrate` on `visaguy` exposed a defect no unit test could: the first backfill left `whatsapp_account` NULL on an enabled row, which the new M9 validation requires, making live configuration unsaveable. Patch extended to backfill the default outgoing account and renamed so it re-executes. Verified by a successful save cycle.
- 2026-08-06: First `the_visaguy` suite run failed on test mocks using `types.SimpleNamespace` (no `.get()`). Corrective explicitly forbade weakening `receive_feedback.py` to accommodate the bad mock. Nine mocks corrected.
- 2026-08-06: `--skip-test-records` is required to run `the_visaguy` tests on this bench, due to a pre-existing mandatory `custom_display_name` on Company.
