---
id: TASK-017
feature: FEAT-003
title: Merge waflo correctness and deploy to staging, then live
status: blocked
repository: waflo
owners:
  - project-owner
depends_on:
  - TASK-016
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Merge waflo correctness and deploy to staging, then live

## Objective

Promote `feat/waflo-correctness` into `develop` and then `main`, and deploy to staging and live as two separate, independently confirmed events.

## Ownership — manual, project owner only

**Performed manually by the project owner. No agent may merge, deploy, tag, or change branch checkout state for this task.** See [ADR-008](../../../decisions/ADR-008-deployment-authority-and-completion-gates.md).

## Scope

| Repository | Branch | Head | Target |
|---|---|---|---|
| `waflo` | `feat/waflo-correctness` | `56899f2` | `develop` → `main` |

Pushed to `tridz-dev/waflo` as of 2026-08-06. Single repository — no cross-app merge ordering required, unlike FEAT-001.

### Two ways to land this

FEAT-002's `waflo` branch, `feat/multi-zone-whatsapp` @ `f81fe81`, was created off this branch and **contains all six of its commits**.

| Option | What lands | Trade-off |
|---|---|---|
| Merge `feat/waflo-correctness` alone | FEAT-003 only | Smaller blast radius. A regression is unambiguously attributable. FEAT-002 merges later. |
| Merge `feat/multi-zone-whatsapp` | FEAT-003 **and** FEAT-002 | One merge instead of two. **No separate FEAT-003 merge is needed.** A regression could come from either feature. |

`feat/waflo-correctness` remains a clean fast-forward from `develop` carrying no FEAT-002 code, so both options stay open.

**Recommended: land FEAT-003 alone first.** Its changes sit on the live send path for every message VisaGuy sends, and its riskiest gap — no end-to-end retry test — is easier to diagnose without multi-zone changes layered on top. FEAT-002 cannot go live before its own blocker anyway: no second `WhatsApp Account` exists yet ([TASK-018](../multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md)).

## Blocking prerequisites

These are not optional. Each is a gap TASK-016 recorded honestly rather than papering over.

1. **End-to-end retry test on a real site.** No deferred-then-retried message has ever been delivered. TASK-014's most serious defect — silent message loss — lived in exactly this seam and was found by reading code, not by a test. Force a rate limit, confirm the message is persisted with `custom_should_retry = 1`, and confirm `schedule_retry_message` later delivers it **with its FLOW button and URL buttons intact**.
2. **Run `bench migrate`** to exercise the D6 `limit_after` removal patch against a site where the field exists.
3. **Decide `max_replies_per_window`.** The dev site is `3` per `30s`. With outbound sends now subject to the limiter, `the_visaguy`'s `_send_payment_received` alone sends two messages back to back; adding a form link can approach the cap, and anything deferred waits up to an hour. Either raise the limit or accept the latency deliberately.

## Behavioural changes to expect on deployment

- Transactional outbound messages are now rate limited. Previously they bypassed the limiter entirely.
- A limited message is deferred to the hourly retry rather than sent immediately — **never dropped**, but potentially up to an hour late.
- Sending a template with both a FLOW button and dynamic URL buttons now raises instead of sending a malformed payload. No current caller does this.
- An unknown template name now raises instead of sending a null template name.
- `WF Settings.limit_after` disappears from the UI.

## Do not enable the flow engine yet

This branch fixes the flow-path defects (D1, D2, N1, N2), but the engine itself remains **untested**. Deploying this branch does not make `enable_flow_engine = 1` safe — that is [FEAT-004](../../../features/planned/whatsapp-flow-engine/README.md), which has its own testing scope.

## Gate 1 — staging deployment

- Date staged:
- Merged to `develop` at:
- Staging site:
- `bench migrate` result:
- End-to-end retry test result:
- Confirmed by:

## Gate 2 — live deployment

- Date deployed live:
- Merged to `main` at:
- Live site:
- `bench migrate` result:
- Rollback point (pre-deploy backup / tag):
- Post-deploy validation:
- Confirmed by:

## Definition of done

Both gates recorded above with the project owner's explicit confirmation.

**FEAT-003 must not move to `features/completed/` until both gates are confirmed.** Staging alone is not sufficient. Any agent asked to mark it complete must ask the owner two distinct questions: is it deployed to **staging**, and is it deployed **live**.
