# Ground facts

Verified 2026-08-06. Executors must not re-derive these.

- Task: implement [FEAT-003](../../features/ongoing/waflo-correctness/README.md) — 11 defects D1–D11 in `waflo`.
- The feature document is the specification. Read it before any phase.
- Repository: `tridz-dev/waflo`, remote alias `git@tridz:tridz-dev/waflo.git`.
- Worktree: `ongoing/waflo-correctness/worktree` (fresh clone, clean, `develop` @ `2167958`). **All edits happen here.**
- The remote bench copy at `erpcode.tridz.in:2257:/home/shahzad/bench/apps/waflo` is **read-only reference**. Never edit it.
- `waflo` working tree on the bench is **clean** (an earlier draft of FEAT-003 wrongly called it dirty).
- Branch to create: `feat/waflo-correctness` off `develop`.
- Executor: Cursor CLI at `/Users/shzd/.local/bin/agent` (symlink to `cursor-agent`, version `2026.08.04-aaa8809`). Not on the non-interactive PATH — invoke by absolute path.
- Frappe version in production: 15.113.0. `frappe/utils/redis_wrapper.py:27` declares `class RedisWrapper(redis.Redis)`, so `frappe.cache()` is a Redis client and inherits `incr`/`expire`.
- VisaGuy runs **one site per bench**. Do not add site-prefixing or cross-site isolation.
- **No agent merges, pushes to `develop`/`main`, or deploys.** ADR-008. Feature-branch pushes are permitted only with explicit user approval.

## Test environment constraint (unresolved)

`waflo` is installed only on the `visaguy` site (a **development** environment on `erpcode.tridz.in` — production is a separate server this project has no access to). The test site `visa-tracker-test.localhost` does not have it (its apps: frappe, erpnext, crm, insights, processflo, fileflo, the_visaguy, passport_extractor). The local benches at `~/Projects/tridz/bench/bench-15|16` do not have `waflo` either.

**Resolved 2026-08-06:** `visaguy` is a dev site, so the suite was run there. 15/15 pass. See `04-verify.md`.

# Phase table

| # | phase | output | status |
|---|-------|--------|--------|
| 1 | Recon: confirm defect line references against the clone | `01-recon.md` | done |
| 2 | Triage (orchestrator) | `02-triage.md` | done |
| 3a | D1 NameError + N1 arg shuffle | `03a-d1-nameerror.md` | done — `3e2428a` |
| 3b | Limiter rewrite: D2, D4, D5, N3 | `03b-limiter.md` | done — `31da123` |
| 3c | Outbound limiting D3 + ceiling D7 | `03c-outbound.md` | done — `1ab527f`, corrected by `de72ec5` |
| 3d | `send.py` hardening D8–D11, N2, N4, D6 removal | `03d-send-hardening.md` | done — `d057f1e` |
| 4 | Verify — suite run on `visaguy` | `04-verify.md` | done — 20/20 pass @ `56899f2` |
| 3e | Re-verify with waflo-role context; fix retry message loss | `03e-retry-loss-corrective.md` | done — `56899f2` |
| 5 | Final report (orchestrator) | — | done |
| 6 | Workspace reconciliation (maintainer) | `tasks/*/waflo-correctness/` | done — TASK-012..017 |

D6 was unblocked mid-run by an owner decision (remove the field) and folded into phase 3d.

# Decisions log

- 2026-08-06: Work in a fresh local clone rather than the bench checkout, per the orchestrator-executor safety rail. The bench copy stays read-only.
- 2026-08-06: D6 deferred — unresolved product decision, so it cannot be assigned to an executor.
- 2026-08-06: Phases 3a–3d sequenced so the limiter rewrite (3b) lands before outbound limiting (3c) consumes it, and `send.py` hardening (3d) comes last because 3c also edits that file.
- 2026-08-06: Test-site availability unresolved; phases 1–3 proceed without it, phase 4 gated on a user decision.

- 2026-08-06: Owner decisions unblocked D3 (queue with backoff, never drop), D7 (build mechanism, default disabled), D6 (remove `limit_after`), and set verification to static-only.
- 2026-08-06: Executor's first D3 backoff used `time.sleep()` in the worker. Rejected and corrected — a sleeping RQ worker starves the `short` queue. `frappe.enqueue(timeout=)` is a job kill-switch, not a delay (`background_jobs.py:160`), and `bench worker` runs without `--with-scheduler`, so RQ `enqueue_in` would never fire. Corrected to reuse waflo's existing hourly `schedule_retry_message` pipeline.
- 2026-08-06: **Retracted.** An earlier entry read `enable_flow_engine=0` from `visaguy` and concluded D1/D2/N1/N2 were latent. `visaguy` is a DEV site; production is a separate inaccessible server, so its config is unknown. If production has the flow engine enabled, D1 and N1 are firing there today.
- 2026-08-06: Test suite executed on `visaguy` @ `d057f1e`: 15/15 pass. Bench `apps/waflo` restored to `develop` @ `2167958`, clean. `allow_tests` left enabled on the site.
- 2026-08-06: Re-verification after ADR-009 landed found a message-loss defect introduced by the D3 interaction with pre-existing `retry_message`: a deferred retry returned None, the `{"message_id": None}` lookup matched an arbitrary NULL-id row, and setting `custom_retried_message` excluded the original from the retry pool forever. Fixed in `56899f2`. Suite re-run on `visaguy`: 20/20 pass.
- 2026-08-06: Workspace reconciled. FEAT-003 moved `planned` -> `ongoing`; TASK-012 through TASK-016 recorded completed with commit evidence; TASK-017 created blocked (manual merge + deploy, owner only). This orchestration directory stays in `ongoing/` until TASK-017 records both deployment gates, then archives.
