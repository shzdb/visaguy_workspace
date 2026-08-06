# Decisions

This directory is the durable record of VisaGuy's architecture and process decisions. It is authoritative — a decision that exists only in chat history, in an agent's memory, or in someone's head is not a decision this project has made.

## Index

| ADR | Title | Status | Scope |
|---|---|---|---|
| [ADR-001](ADR-001-workspace-and-repository-authority.md) | Workspace and repository authority | Accepted | Process |
| [ADR-002](ADR-002-app-ownership-classification.md) | App ownership classification | Accepted | Repositories |
| [ADR-003](ADR-003-fileflo-consumer-agnostic-extension-point.md) | FileFlo consumer-agnostic post-persistence extension point | Accepted | `fileflo` |
| [ADR-004](ADR-004-passport-extraction-as-standalone-reusable-app.md) | Passport extraction as a standalone reusable app | Accepted | `passport_extractor` |
| [ADR-005](ADR-005-visa-tracker-public-exposure-boundary.md) | Visa tracker status ownership and public exposure boundary | Accepted | `the_visaguy` |
| [ADR-006](ADR-006-zone-and-company-as-distinct-domain-axes.md) | **Zone and Company are distinct domain axes** | Accepted | **Foundational — read first** |
| [ADR-007](ADR-007-whatsapp-configuration-keyed-on-zone.md) | WhatsApp configuration is keyed on Zone | Accepted | `the_visaguy`, `waflo` |
| [ADR-008](ADR-008-deployment-authority-and-completion-gates.md) | Deployment authority and completion gates | Accepted | Process |
| [ADR-009](ADR-009-waflo-as-maintained-whatsapp-extension-layer.md) | Waflo is the maintained WhatsApp extension layer | Accepted | `waflo`, `frappe_whatsapp` |

## Read these first

Two decisions constrain almost everything else:

- **[ADR-006](ADR-006-zone-and-company-as-distinct-domain-axes.md)** — Zone is the customer-facing market, Company is the employing legal entity, and neither derives from the other. Three of the four names coincide, so code that keys the wrong axis **looks correct until a back-office record passes through it**. Read before designing anything that scopes data.
- **[ADR-008](ADR-008-deployment-authority-and-completion-gates.md)** — no agent merges or deploys. Staging and live are separate gates, confirmed separately, before any feature is marked completed.

## Conventions

- One decision per ADR. Use `.agents/templates/decision.md`.
- Status is `Proposed`, `Accepted`, `Superseded`, or `Rejected`.
- Superseded ADRs stay here with their status changed, and name the ADR that replaced them. Never delete or rewrite history — a wrong decision that was acted on is part of the record.
- Number sequentially. Do not reuse a number even if an ADR is rejected.
- An ADR records **why**, not just what. A decision without its rejected alternatives cannot be safely revisited.
- Every ADR carries a **Revisit when** condition.
- A feature may declare an ADR in `depends_on`. If that ADR is `Proposed`, the dependent tasks are not implementation-ready.

## Decision log

Smaller decisions that shape the project but do not warrant a full ADR. Newest first. When an entry grows into a real architectural constraint, promote it to an ADR and link it here.

### 2026-08-06

- **FEAT-003 implemented and verified, not deployed.** Branch `feat/waflo-correctness` @ `56899f2`, 20/20 tests pass on the `visaguy` dev site. Moved `planned` → `ongoing`; TASK-012–016 completed, TASK-017 (merge and deploy) blocked as owner-only. Three prerequisites recorded before deployment: no end-to-end retry test has run, `bench migrate` has not exercised the `limit_after` removal patch, and `max_replies_per_window` needs a deliberate value.
- **Re-verifying after a context change found a real bug.** Once ADR-009 established the send path as `waflo`'s live path, re-reading the branch surfaced silent message loss: a deferred retry returned `None`, `retry_message` matched an arbitrary NULL-`message_id` row, and setting `custom_retried_message` permanently excluded the original from the retry pool. Introduced by FEAT-003's own D3 fix. Fixed in `56899f2`. Lesson recorded deliberately: **re-verify implementation work when the surrounding understanding changes**, not only when the code changes.
- **No delayed-enqueue primitive exists on this bench.** `frappe.enqueue(timeout=)` is RQ's `job_timeout`, a maximum-execution kill-switch (`frappe/utils/background_jobs.py:160`), not a schedule. `bench worker` runs without `--with-scheduler`, so RQ's `enqueue_in` never fires. Deferred work must reuse an existing scheduler-driven pipeline — for WhatsApp that is `custom_should_retry` plus the hourly `schedule_retry_message`. Do not add `time.sleep` in a worker; a sleeping RQ worker starves its queue.
- **`waflo`'s conversational flow engine has never been tested and is not in use.** It is planned work ([FEAT-004](../features/planned/whatsapp-flow-engine/README.md)), not a live capability. `waflo`'s real role today is a send helper for template features `frappe_whatsapp` lacks — dynamic URL buttons, FLOW buttons, caller-supplied header/body params — plus rate limiting and retry. Promoted to [ADR-009](ADR-009-waflo-as-maintained-whatsapp-extension-layer.md). Consequence: FEAT-003 defects D1, D2, N1 and N2 sit on the dormant flow path and are prerequisites for FEAT-004, **not live production bugs**. Do not enable `WF Settings.enable_flow_engine` on a site with real customers until FEAT-003 is deployed.
- **Rate limiting lives in `waflo`, not `frappe_whatsapp`, because we maintain `waflo` and do not maintain `frappe_whatsapp`.** Architecturally it belongs at the provider layer; this is a deliberate ownership tradeoff, not an oversight. Known cost: anything calling `frappe_whatsapp` directly bypasses the limiter. See ADR-009.
- The `visaguy` site on `erpcode.tridz.in` is a **development** environment. Production is a separate server this project has no access to. Do not describe `visaguy` as production, and do not infer production configuration from it.
- **One site per bench, always.** VisaGuy does not run multiple production sites on a shared bench. Therefore: do not design for cross-site isolation in Redis keys, caches, or any other bench-shared resource. Plain cache keys are correct; `frappe.cache().make_key()` prefixing is unnecessary ceremony. If a second site exists transiently for testing, that is not a reason to add isolation machinery to production code. This constraint exists to stop over-engineering — an earlier draft of FEAT-003 D4 added site-prefixing and a two-site isolation test, both of which were removed as scope creep.
- **Corrected:** WhatsApp configuration is keyed on **Zone**, not Company. An earlier draft recommended Company; the project owner corrected it. Keying on Company would have sent a UAE customer messages from the `TVG India` back-office number. Promoted to [ADR-006](ADR-006-zone-and-company-as-distinct-domain-axes.md) and [ADR-007](ADR-007-whatsapp-configuration-keyed-on-zone.md).
- The four-companies / three-zones asymmetry is **correct by design**. `TVG India` is a back office with no customers of its own, so it needs no zone and no WhatsApp configuration. A prior audit wrongly flagged this as a data gap; that finding is retracted.
- [FEAT-003](../features/ongoing/waflo-correctness/README.md) is sequenced **before** [FEAT-002](../features/planned/multi-company-whatsapp/README.md). Fanning WhatsApp traffic out to more numbers while the rate limiter does not count is an avoidable risk to the Meta account, and both features edit `waflo/messaging/send.py`.
- `the_visaguy` is intentionally checked out on `main` on the bench while unrelated work proceeds, leaving the bench in a mixed branch state. Not a defect; re-check every branch before the TASK-011 merge rather than trusting a recorded table.
- End-to-end code flows are canonical in [`docs/architecture/workflows.md`](../docs/architecture/workflows.md). W1–W5 previously existed only in reconnaissance evidence that no reader was routed to.
- The workspace-initialization effort is archived and its facts are **deliberately frozen**. Do not update them; use `docs/architecture/repository-catalog.md` for current state.
- FEAT-001 moved `planned` → `ongoing` after an audit found TASK-001 through TASK-007 already implemented and pushed while the feature still claimed it was unstarted.
- Remote bench worktrees and loose `task004` patch files were deleted after verifying every commit in them was superseded by a pushed upstream branch.

### 2026-07-21

- Canonical documentation is organised by product/capability, topology, repositories, customizations, integrations, procedures, and risks. Reconnaissance reports remain evidence, not the reader entrypoint.

### 2026-07-20

- Repositories owned by `tridz-dev` or `tvgglobal` are internally maintained; other origins are external unless repository evidence proves otherwise. Promoted to [ADR-002](ADR-002-app-ownership-classification.md).
- Application repositories and the remote bench are read-only sources of evidence. Documentation is created only in this workspace.
- Ownership classification uses the Git remote `upstream` when present, otherwise `origin`, because most bench repositories name their primary remote `upstream`.

Entries before 2026-07-22 are reproduced from the archived initialization `STATE.md`, which is no longer maintained.
