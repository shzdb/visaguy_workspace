---
id: FEAT-003
title: Waflo flow engine and rate limiting correctness
status: planned
priority: high
repositories:
  - waflo
owners: []
depends_on: []
created: 2026-08-06
updated: 2026-08-06
---

# Waflo flow engine and rate limiting correctness

## Summary

Fix a set of defects in `waflo` found while assessing whether the WhatsApp stack can safely serve more than one company. The rate limiter is not merely incomplete — it is **inert whenever the flow engine is enabled**, because the counter is never incremented on the flow paths. The same defect also breaks conversation state for new chats.

This feature is a **prerequisite for [FEAT-002](../multi-company-whatsapp/README.md)**. Fanning WhatsApp traffic out to additional companies while the limiter does not count is an avoidable risk to the Meta account.

## Evidence

All findings verified against `waflo` branch `develop` @ `2167958` on the remote bench, 2026-08-06. `waflo` currently has a **dirty working tree**; the diff was not inspected, so confirm these line references still hold before editing.

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

`frappe.cache().get_value` / `set_value` cannot express this safely. Use an atomic Redis `INCR` with `EXPIRE` on first write.

### D5 — Window TTL is extended on every increment

`increment_rate_limit` calls `set_value(..., expires_in_sec=window_seconds)` on each increment, resetting the key's TTL. The key therefore outlives its window under sustained traffic. The explicit `window_start` comparison currently compensates, so this is latent rather than active — but it makes the two mechanisms redundant and the behaviour hard to reason about. Pick one: a fixed window keyed by timestamp bucket, or a TTL-driven window. Not both.

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
- Reconciling waflo's dirty working tree. That is a prerequisite, not part of this feature.

## Proposed task order

| # | Task | Repository | Notes |
|---|---|---|---|
| 1 | Reconcile the dirty `waflo` tree; branch `feat/waflo-correctness`; confirm line references | `waflo` | Blocking prerequisite |
| 2 | Fix D1 and add a regression test proving `WF Active Chat Flow` is created | `waflo` | Highest severity; ship independently if needed |
| 3 | Rewrite the limiter on atomic Redis `INCR`/`EXPIRE` — fixes D2, D4, D5 | `waflo` | |
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
- `waflo` has a dirty working tree; edits risk entangling unrelated changes.
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
