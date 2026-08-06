---
id: FEAT-004
title: WhatsApp conversational flow engine — build and test
status: planned
priority: low
repositories:
  - waflo
owners: []
depends_on:
  - FEAT-003
  - ADR-009
created: 2026-08-06
updated: 2026-08-06
---

# WhatsApp conversational flow engine — build and test

## Summary

`waflo` contains a conversational flow engine: a flowchart of WhatsApp messages that branches on what the customer replies. The customer sends "hi", we send a message, their answer determines the next message, and so on.

**The engine exists in code but has never been tested and is not in use.** `WF Settings.enable_flow_engine` is `0`. This feature is the plan to actually build it out, test it, and turn it on.

## Current state

The scaffolding is present and non-trivial:

| Piece | Location |
|---|---|
| Flow processor | `waflo/waflo/flow/processor.py` |
| Step matching | `waflo/waflo/flow/triggers.py` — `match_step`, `get_step_by_name` |
| Step actions | `waflo/waflo/flow/actions.py` — `eval_template_params`, `eval_button_url_map`, `update_target_status` |
| Inactivity expiry | `waflo/waflo/flow/expire.py`, cron every minute |
| Flow definition | `WF Message Flow`, `WF Flow Step` |
| Live conversation state | `WF Active Chat Flow` |
| Settings | `WF Settings.enable_flow_engine`, `.inactive_timeout` |

What it can express today: a default flow, an initial step, per-step message templates with parameters and button URLs, step-to-step transitions on matched input, a target field/value status update, and inactivity timeout.

## Why this is not urgent

Per [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md), `waflo`'s actual production role today is a **send helper** — template sends with dynamic URL buttons and FLOW buttons that `frappe_whatsapp` does not support — plus rate limiting and retry. The flow engine is dormant.

This matters for reading [FEAT-003](../waflo-correctness/README.md): defects **D1, D2, N1 and N2 all sit on the flow-engine path** and therefore cannot fire while `enable_flow_engine = 0`. They are prerequisites for this feature, not live production bugs.

## Prerequisite: FEAT-003 must land first

Enabling the flow engine before FEAT-003 is deployed would produce, immediately:

- **D1** — no `WF Active Chat Flow` is ever created, so every inbound message re-sends the initial step. A message loop toward the customer.
- **N1** — arguments to `send_whatsapp_template` are shuffled by one position, so most flow sends raise (`KeyError` on header params, or `JSONDecodeError` on a doctype name passed as a button map) and never send at all.
- **N2** — a flow created without reference doctype/name raises on the next inbound message, and the conversation silently stops advancing.
- **D2** — the rate limiter stops counting entirely on flow paths.

FEAT-003 fixes all four. **Do not set `enable_flow_engine = 1` on any site with real customers until it is deployed.**

## Scope

### Included

1. Design at least one real conversational flow end to end, with the business.
2. Exercise every branch of the step machine against a test WhatsApp number.
3. Establish what happens on unmatched input — today `match_step` behaviour under a reply that matches nothing is unverified.
4. Verify inactivity expiry actually closes flows and that `inactive_timeout` is honoured (it is currently `0` on the dev site).
5. Verify one flow per number: concurrent or overlapping flows for the same customer.
6. Decide and test interaction with transactional messages — what happens when a payment confirmation arrives mid-flow.
7. Integration tests against real Redis and a real queue, not mocks.
8. A staged rollout: dev site → limited real numbers → general.

### Excluded

- WhatsApp Flows (Meta's native form product, `sub_type: "FLOW"`). That is already used for feedback collection and is a different mechanism from this step machine, despite the overlapping name.
- Replacing transactional auto messages with flows.

## Open questions

None of these have been established, because the engine has never run:

1. What is the intended behaviour on unmatched input — reprompt, fall through to a default reply, escalate to a human, or end the flow?
2. Should a flow be interruptible by a transactional message, or queued behind it?
3. What is a sensible `inactive_timeout`? It is `0` today, which likely means expiry is inert.
4. Who authors flows — engineering, or operations through the `WF Message Flow` UI? That determines how much validation the DocType needs.
5. How does a customer exit a flow deliberately?
6. Does a flow need to be zone-aware, given [ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md)? A UAE customer and a Qatar customer may need different flows and different sending numbers.

## Risks

- The engine is untested code that has been carried for a long time; treat all of it as unverified, not just the parts FEAT-003 names.
- A flow bug is customer-visible and repeats — the D1 loop is the illustration.
- Interaction with rate limiting is unexplored: a flow that sends several steps quickly could trip the limiter and stall mid-conversation.
- Flow state lives in a DocType, so an abandoned flow leaves rows behind; expiry must genuinely work.

## Dependencies

- [FEAT-003](../waflo-correctness/README.md) deployed.
- A test WhatsApp number and approved templates.
- Business input on the actual conversation design.

## Completion notes

Not started. Recorded 2026-08-06 so the intent is not lost, and so that the dormant-by-design status of the flow engine is discoverable rather than looking like an accident.
