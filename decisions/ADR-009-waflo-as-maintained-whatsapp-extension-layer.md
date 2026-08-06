# ADR-009: Waflo Is the Maintained WhatsApp Extension Layer

## Status

Accepted

Records existing architecture and the reasoning behind it. Written down because the app's name and its module layout both suggest a different purpose than the one it actually serves today.

## Context

VisaGuy sends WhatsApp messages through `frappe_whatsapp` (`shridarpatil/frappe_whatsapp`), an **external, upstream app we do not maintain**, currently on branch `master` @ `27f3438`.

Two capabilities `the_visaguy` depends on are absent from it:

| Capability | `frappe_whatsapp.send_template` | Needed for |
|---|---|---|
| Dynamic URL button parameters | **Absent** — no button components with `sub_type: "url"` | Form links: `/form/{form_id}` appended to a template's button |
| WhatsApp Flows button | **Absent** — no `sub_type: "FLOW"` | Feedback collection (Payment Feedback, Completion Feedback) |
| Caller-supplied header params | Partial — only builds a header from `self.attach`, driven by `template.header_type` | Invoice PDF as a document header, feedback header images |
| Caller-supplied body params | Indirect — derives values from `template.sample_values` / `field_names` against a reference doc | Explicit control over parameter values |

The natural home for these is `frappe_whatsapp` itself. But we do not maintain it, and carrying a fork or upstreaming on someone else's release cadence would put a hard dependency on an external maintainer for our own product roadmap.

`waflo` (`tridz-dev/waflo`) is ours.

## Decision

**`waflo` is the maintained extension layer for WhatsApp capabilities that `frappe_whatsapp` does not provide.**

- `frappe_whatsapp` remains the provider integration: credentials, `WhatsApp Account`, `WhatsApp Templates`, the inbound webhook, and the `WhatsApp Message` record.
- `waflo` owns everything we need to add on top: `send_whatsapp_template` with explicit body/header parameters, dynamic URL buttons, FLOW buttons, message logging, retry, and rate limiting.
- Cross-cutting policy that belongs to us — **rate limiting in particular** — lives in `waflo`, not in `frappe_whatsapp`, even though architecturally it would be better placed at the provider layer.
- `the_visaguy` calls `waflo`, not `frappe_whatsapp`, for outbound templates.

This is a **pragmatic ownership boundary, not an architectural ideal.** Recording it so nobody later "fixes" it by moving code into an app we cannot release.

## The flow engine is a separate, dormant concern

`waflo`'s name and module layout (`flow/processor.py`, `flow/triggers.py`, `WF Message Flow`, `WF Active Chat Flow`) come from its *original* purpose: a conversational flowchart that branches on customer replies.

**That engine has never been tested and is not in use.** `WF Settings.enable_flow_engine` is `0`. It is a planned capability — see FEAT-004 — not a live one.

Anyone reading this app for the first time will assume the flow engine is its main job. It is not. Today `waflo` is, in practice, a **send helper plus rate limiting and retry**.

## Consequences

### Positive

- We can add WhatsApp capability on our own release cadence without forking or waiting on an external maintainer.
- The upstream `frappe_whatsapp` stays unmodified, so upgrading it stays cheap.
- Ownership is unambiguous: if a WhatsApp capability is missing, it goes in `waflo`.

### Negative

- Rate limiting sits above the provider layer rather than in it, so **anything that calls `frappe_whatsapp` directly bypasses our limiter entirely.** Only sends routed through `waflo` are governed.
- Two apps must be understood together to reason about one message.
- If `frappe_whatsapp` later gains these features, `waflo` will duplicate them and the overlap will need resolving.
- The app's name and structure mislead about its current role, which is exactly why this ADR exists.

## Alternatives considered

- **Contribute upstream to `frappe_whatsapp`.** Rejected for now: puts our roadmap behind an external maintainer's review and release cycle. Still the right long-term home if the project becomes responsive.
- **Fork `frappe_whatsapp`.** Rejected: we already carry two maintained forks (`crm`, `helpdesk`) and the upgrade cost is well understood. A third is not worth it for additive features that compose cleanly from outside.
- **Put the additions in `the_visaguy`.** Rejected: they are domain-free WhatsApp plumbing and would not be reusable, mirroring the reasoning in [ADR-004](ADR-004-passport-extraction-as-standalone-reusable-app.md).

## Revisit when

`frappe_whatsapp` gains dynamic URL buttons and FLOW button support, becomes actively maintained enough to accept contributions on a useful timeline, or the direct-call bypass of our rate limiter causes a real incident.
