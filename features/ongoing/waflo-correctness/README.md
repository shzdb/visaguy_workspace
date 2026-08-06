---
id: FEAT-003
title: Waflo flow engine and rate limiting correctness
status: ongoing
priority: high
repositories:
  - waflo
owners: []
depends_on:
  - ADR-009
created: 2026-08-06
updated: 2026-08-06
---

# Waflo flow engine and rate limiting correctness

## Current status

**Implemented and verified. Not merged, not deployed.**

All 11 spec defects fixed, plus 4 found during implementation recon. Branch `feat/waflo-correctness` @ `56899f2`, pushed to `tridz-dev/waflo`.

| Task | State |
|---|---|
| [TASK-012](../../../tasks/completed/waflo-correctness/TASK-012-flow-nameerror-and-argument-binding.md) — D1, N1 | completed — `3e2428a` |
| [TASK-013](../../../tasks/completed/waflo-correctness/TASK-013-atomic-rate-limiter.md) — D2, D4, D5, N3 | completed — `31da123` |
| [TASK-014](../../../tasks/completed/waflo-correctness/TASK-014-outbound-limiting-and-retry-integrity.md) — D3, D7 | completed — `1ab527f`, `de72ec5`, `56899f2` |
| [TASK-015](../../../tasks/completed/waflo-correctness/TASK-015-send-hardening-and-dead-config-removal.md) — D8–D11, N2, N4, D6 | completed — `d057f1e` |
| [TASK-016](../../../tasks/completed/waflo-correctness/TASK-016-verification.md) — verification | completed — 20/20 pass |
| [TASK-017](../../../tasks/blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md) — merge and deploy | blocked — **manual, owner only** |

Test suite: `bench --site visaguy run-tests --app waflo` → **20/20 pass** on the `visaguy` dev site.

### Three blocking prerequisites before deployment

Recorded honestly rather than glossed over. All are in TASK-017.

1. **No end-to-end retry test has ever run.** The most serious defect found — silent message loss on a deferred retry — lived exactly in that seam and was caught by code reading, not by a test. All tests mock Redis, the queue, and the Meta API.
2. **`bench migrate` has not been run**, so the D6 `limit_after` removal patch is unexercised.
3. **`max_replies_per_window` needs a decision.** Dev is 3 per 30s; with outbound now limited, `_send_payment_received` alone sends two messages back to back, and anything deferred waits up to an hour.

### Defects found beyond the original spec

Recon and re-verification found four the spec missed. N1 and the retry message-loss defect were the most serious:

- **N1** — every flow-driven `send_whatsapp_template` call passed arguments positionally against a signature whose 4th parameter is `header_params`, so most flow sends raised rather than sending.
- **Retry message loss** — `send_whatsapp_template` returning `None` on deferral caused `retry_message` to match an arbitrary NULL-`message_id` row and permanently exclude the original from the retry pool. Introduced by this feature's own D3 fix; found only after [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md) reframed the send path as the live path.
- **N2**, **N3**, **N4** — null-reference assumption, check/increment disagreement on incomplete config, and a nonexistent `header_video` field.

### Completion gate

Moves to `features/completed/` only when TASK-017 Gate 1 (**staging**) and Gate 2 (**live**) are both confirmed by the project owner, as two separate events. See [ADR-008](../../../decisions/ADR-008-deployment-authority-and-completion-gates.md).

## Summary

Fix a set of defects in `waflo` found while assessing whether the WhatsApp stack can safely serve more than one zone.

This feature is a **prerequisite for [FEAT-002](../../planned/multi-company-whatsapp/README.md)** and for [FEAT-004](../../planned/whatsapp-flow-engine/README.md).

## Read this before ranking the defects

`waflo`'s production role today is a **send helper** — template sends with dynamic URL buttons and FLOW buttons that `frappe_whatsapp` does not support — plus rate limiting and retry. See [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md).

The conversational flow engine that gives the app its name **has never been tested and is switched off** (`WF Settings.enable_flow_engine = 0`). It is planned work, tracked as [FEAT-004](../../planned/whatsapp-flow-engine/README.md).

That splits these defects into two very different groups:

| Group | Defects | Status |
|---|---|---|
| **Live send path** — runs on every message VisaGuy sends today | D3, D4, D5, D8, D9, D10, D11, N3, and D2's default-reply path | Real, affecting production now |
| **Flow-engine path** — dormant while the engine is off | D1, D2 (flow branches), N1, N2 | Prerequisites for FEAT-004, not live bugs |

D1 and N1 are described below as critical, and they are — **but only once the flow engine is enabled.** They are blockers for FEAT-004, not fires to put out today. Do not set `enable_flow_engine = 1` on a site with real customers until this branch is deployed.

## Evidence

All findings verified against `waflo` branch `develop` @ `2167958` on the remote bench, 2026-08-06. The working tree is **clean** — an earlier draft of this document wrongly listed `waflo` among the dirty repositories; the five dirty trees are `insights`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`, and `mansico_meta_integration`.

## Defects

### D1 — `NameError` kills conversation creation (critical)

`waflo/waflo/flow/processor.py:61`

```
def process_whatsapp_message(mobile_no, message_text, ref_doctype=None, ref_name=None):
    ...
            send_whatsapp_template(...)
            increment_rate_limit(doc.whatsapp_account, mobile_no)   # <-- `doc` is not in scope
            create_active_flow(flow, mobile_no, step, ref_doctype, ref_name)
            return
```

`doc` is not a parameter of `process_whatsapp_message` and is not otherwise bound. The call raises `NameError`, which is swallowed by the broad `except Exception` at line 106 and logged as "WF Flow Error".

Consequences, in order of severity:

1. `create_active_flow(...)` on the next line **never executes**. A new conversation never gets a `WF Active Chat Flow` record.
2. Because no active flow exists, the next inbound message from the same number takes the same branch again — sending the initial step repeatedly. This is a **message loop toward the customer**, bounded only by inbound volume.
3. The rate limit counter never increments on this path.

The same call at `processor.py:151` is **correct** — it sits inside `send_default_message(doc)`, where `doc` is a parameter. Do not "fix" that one.

### D2 — Rate limiter never counts on flow paths (critical)

`increment_rate_limit` is called in exactly two places: line 61 (broken, D1) and line 151 (`send_default_message`, only reached when `enable_flow_engine` is **off**).

The continuing-conversation path — an existing `WF Active Chat Flow` advancing a step — never increments at all.

Net effect with the flow engine enabled: the counter stays absent, `is_rate_limited` finds no cache entry, returns `False` on line 32, and every message is allowed. The limiter is decorative.

### D3 — Outbound template sends are not rate limited at all

`waflo/waflo/messaging/send.py:send_whatsapp_template` performs no rate-limit check. Every auto message and feedback message from `the_visaguy` (see [`workflows.md`](../../../docs/architecture/workflows.md) W9b) goes through this function and bypasses the limiter entirely.

The current design only ever contemplated limiting *replies to inbound messages*. Business-event-driven outbound messaging — which is the bulk of the traffic — has no ceiling.

### D4 — Check-then-act race

`is_rate_limited` reads the counter; `increment_rate_limit` later performs a separate read-modify-write. Two workers processing concurrent inbound messages can both read `count = max - 1`, both pass, and both write. The limit is exceeded under exactly the burst conditions it exists to control.

**The transport is not the problem — the value shape is.** Keep using `frappe.cache()`. Verified against Frappe 15.113.0: `frappe/utils/redis_wrapper.py:27` declares `class RedisWrapper(redis.Redis)`, so `frappe.cache()` *is* a Redis client and already exposes the atomic primitives by inheritance. A separate Redis connection would duplicate the connection pool that bench already manages, for no benefit.

The defect is that the counter is stored as a **compound dict** `{"count": N, "window_start": T}` via `set_value`, which serializes it. Reading it back, incrementing in Python, and writing it again is a read-modify-write that no transport can make atomic.

Fix: store a **scalar** and let Redis do the arithmetic.

```
count = frappe.cache().incr(key)
if count == 1:
    frappe.cache().expire(key, window_seconds)
```

`INCR` is atomic, so concurrent workers serialise correctly, and setting the TTL only when the counter returns 1 gives a fixed window that starts at the first request. This also removes the need for a separate `window_start` field, which resolves D5 at the same time.

Keep the plain key. VisaGuy runs **one site per bench**, so cross-site key collision is not a concern here and no site prefixing is required — see the decision log entry for 2026-08-06.

### D5 — Window TTL is extended on every increment

`increment_rate_limit` calls `set_value(..., expires_in_sec=window_seconds)` on each increment, resetting the key's TTL. The key therefore outlives its window under sustained traffic. The explicit `window_start` comparison currently compensates, so this is latent rather than active — but it makes the two mechanisms redundant and the behaviour hard to reason about.

There are two windowing mechanisms fighting each other: a TTL and a stored `window_start`. Pick one. The D4 fix picks the TTL — set once when `INCR` returns 1 — and drops `window_start` entirely, which resolves this defect as a side effect.

### D6 — `WF Settings.limit_after` is an orphaned field

Declared in `wf_settings.json` under `rate_limiting_tab`, never read anywhere in Python (`grep` over the app finds no consumer). It presents a configuration surface that does nothing. Either implement it or remove it — a dead knob under a "Rate Limiting" tab actively misleads whoever configures this next.

### D7 — No account-level or global ceiling

The limiter is scoped per `(account, mobile_no)`. There is no cap on total sends per account per window. Meta enforces per-number throughput and quality-rating limits; a fan-out to many recipients — the exact pattern FEAT-002 introduces — is unbounded today.

### D8 — Error handler can mask the original error

`send.py:112`

```
except Exception as e:
    frappe.log_error("send_whatsapp_template", f"WhatsApp Send Error: {str(e)}")
    frappe.get_doc({
        "doctype": "WhatsApp Notification Log",
        "meta_data": frappe.flags.integration_request.json(),   # <-- may not exist
    }).insert(...)
```

`frappe.flags.integration_request` is only set once a request has been issued. When the failure occurs earlier — missing token, unresolved template, malformed payload — this raises `AttributeError` inside the handler and the original exception is lost.

### D9 — Missing template is not guarded

`send.py:30` — `template_actual_name = frappe.db.get_value("WhatsApp Templates", template_name, "actual_name")` returns `None` for an unknown template, and the payload is sent with `"name": null`. Fails at the provider with a poor error.

### D10 — Log spam in the button loop

`send.py:62` calls `frappe.log_error` inside the per-button loop on **every** send that has buttons. This is debug output left in a production path; it fills the Error Log and obscures real failures.

### D11 — `use_flow` collides with `button_url_map`

`send.py:71` appends a flow button at `index "0"`. When `button_url_map` is also supplied, its first entry is already `index "0"`. The two cannot currently be combined. Either reject the combination explicitly or offset the index.

## Scope

### Included

- D1–D11 above.
- Regression tests covering: new-conversation flow creation, counter increment on both flow paths, limit enforcement under concurrency, and outbound send limiting.
- A short runbook note on choosing `max_replies_per_window` / `window_seconds` values.

### Excluded

- Redesigning the flow engine itself.
- Per-company rate limit policy — that arrives with FEAT-002 and should build on the corrected primitives, not precede them.
- Deployment. Merging to `develop`/`main` and deploying are manual and owner-only per [ADR-008](../../../decisions/ADR-008-deployment-authority-and-completion-gates.md).

## Proposed task order

| # | Task | Repository | Notes |
|---|---|---|---|
| 1 | Branch `feat/waflo-correctness` off `develop`; confirm line references | `waflo` | |
| 2 | Fix D1 and add a regression test proving `WF Active Chat Flow` is created | `waflo` | Highest severity; ship independently if needed |
| 3 | Rewrite the limiter on `frappe.cache().incr()` / `.expire()` — fixes D2, D4, D5 | `waflo` | |
| 4 | Add rate limiting to the outbound send path — D3 | `waflo` | Coordinate with FEAT-002 account routing |
| 5 | Add account-level ceiling — D7 | `waflo` | |
| 6 | Resolve or remove `limit_after` — D6 | `waflo` | Needs a product decision; see open questions |
| 7 | Harden `send.py`: D8, D9, D10, D11 | `waflo` | |
| 8 | Verification: concurrency test, loop-regression test, staging soak | `waflo` | |

## Acceptance criteria

- A new inbound conversation creates exactly one `WF Active Chat Flow`, and the initial step is sent exactly once.
- The rate limit counter increments on every send path: new flow, continuing flow, default reply, and outbound template.
- With `max_replies_per_window = N`, a concurrent burst of `N + M` messages results in exactly `N` sends.
- An account-level ceiling is enforced independently of the per-recipient one.
- No configuration field under the Rate Limiting tabs is unread by code.
- A send failure occurring before the HTTP request is issued is logged with its original exception.
- An unknown template name fails fast with a clear error rather than a null payload.
- The Error Log contains no per-button debug entries after a normal send.

## Risks

- **D1 may be masking real production behaviour.** Before fixing, check the Error Log for "WF Flow Error" volume and check whether customers have been receiving repeated initial-step messages. The fix will change live behaviour immediately.
- Turning a decorative limiter into a real one **will start blocking messages** that currently go out. Values must be chosen deliberately before enabling, or legitimate traffic will be dropped.
- No existing test coverage for the flow engine, so regressions are hard to detect by running the suite alone.
- No existing test coverage for the flow engine, so regressions are hard to detect.

## Open questions

These need a decision before the affected tasks are implementation-ready:

1. **`limit_after`** — what was it intended to do? If nobody recalls, remove it rather than guessing a meaning.
2. **Behaviour when rate limited** — currently the inbound message is marked `custom_rate_limited` and dropped silently. Should the customer receive a "we'll get back to you" reply, should it queue for later delivery, or is silent drop correct?
3. **Outbound limiting policy** — should a business-event message (payment success, visa completion) ever be dropped for rate limiting, or must it queue and retry? These are transactional messages; dropping them has real customer impact. Recommendation: queue with backoff, never drop, and cap only conversational replies.
4. **Account-level ceiling values** — needs Meta tier and quality-rating information for the account.

## Dependencies

- Reconciled `waflo` working tree.
- Redis (already a bench dependency).
- Meta account tier limits, for D7 values.
