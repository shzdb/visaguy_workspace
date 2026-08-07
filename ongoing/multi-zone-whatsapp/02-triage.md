# Phase 2 — Triage (orchestrator)

## Spec corrections

| Spec claim | Code |
|---|---|
| 5 `Whatsapp Default` lookup sites | **4** live `get_doc` (a 5th is inside dead commented code) |
| 6 `[...][0]` index sites | **7** — 5 over `event_template`, 2 over `feedback_defaults`. The payment path alone has three. |
| `send.py` line refs in M1–M4 | Pre-FEAT-003; the file has since been restructured |

M10 and M11 must be sized to 7 and 4 respectively, not 6 and 5.

## New findings — three of these break Qatar

Recon surfaced four issues absent from M1–M19. Three are in scope; one is a product gap.

### F1 — `receive_feedback.py` hardcodes `COMPANY = "TVG"` — **in scope**

It resolves `Whatsapp Feedback Defaults` with `parent = COMPANY`. A Qatar customer replying to a feedback message would have their reply matched against **TVG's** feedback configuration.

This is the inbound half of the feature the owner explicitly asked for — "auto messages and feedback messages as well". The spec covers only the outbound half. Without this, Qatar feedback collection silently uses the wrong zone's config.

### F2 — `retry_message` drops `whatsapp_account` — **in scope**

The `WhatsApp Message` record stores `whatsapp_account`, but `retry_message` never reads it and lets `send_whatsapp_template` re-resolve the default outgoing account.

Consequence once a second account exists: a Qatar message deferred by FEAT-003's rate limiter is **retried from the UAE number** — where Qatar's template does not exist, so Meta rejects it. This is a direct interaction between FEAT-003's deferral and multi-account, exactly the class of defect that produced the message-loss bug in FEAT-003.

### F3 — `processor.py` replies leave from the wrong account — **in scope**

Inbound handling reads `doc.whatsapp_account` for rate-limit accounting and for `WF Account Settings`, but every send goes through the default outgoing account.

**This path is live.** With the flow engine off, `send_default_message` handles inbound messages. So a Qatar customer messaging the Qatar number would receive their default reply **from the UAE number**. Not dormant like D1/N1 — this breaks the moment a second account exists.

### F4 — `Visa Completion` — **resolved by the owner, not a gap**

Recon flagged `Visa Completion` as an `event_type` option with no handler, and therefore a possible hole in the acceptance criteria.

**Owner confirmed it is not required**: the visa completion message goes out together with the completion feedback message, so there is no separate send. The Select option stays; nothing demands it.

This defined the required-configuration list that M9 validation enforces — five event templates (Lead Form, Process Form, Payment Success, Payment Feedback, Completion Feedback), two feedback defaults (Payment Feedback, Completion Feedback), and a bound account.

## Execution order

Sequenced so `the_visaguy` consumes a `waflo` that already accepts an account, and so the two `the_visaguy` phases do not collide on the same file.

| Phase | Scope | Repo | Rationale |
|---|---|---|---|
| 3a | M1–M4 account threading, plus F2 and F3 | `waflo` | Nothing downstream can route until the send path accepts an account |
| 3b | M5, M6, M6b, M9 + migration | `the_visaguy` | Config model and the Company→Zone rekey |
| 3c | M10–M16 (7 index sites, 4 lookups), plus F1 | `the_visaguy` | Handler robustness; last because 3b changes the lookup key |
| 4 | Verify on `visaguy` | both | |

## Policies for executors

1. **Zone, not Company.** `Whatsapp Default` is keyed on Zone per ADR-007. Callers already pass a zone under a misnamed `company=` kwarg — the callers are right, the field and parameter names are wrong.
2. **Never fall back to the default account.** A Qatar customer must never receive a UAE-numbered message. Missing configuration means skip and log, not substitute.
3. **Skip with a logged warning**, never a silent skip. A misconfigured zone must not look identical to a working one.
4. New parameters go at the **end** of existing signatures with defaults — `the_visaguy` and `retry_message` both import `send_whatsapp_template`.
5. Do not implement M7/M8 (extensible event types) — deferred.
6. Do not implement `Visa Completion` (F4) — product gap, not ours to invent.
7. `the_visaguy` patches are flat under `the_visaguy/the_visaguy/patches/`; `waflo` uses a versioned `patches/v1_0/` package. Follow each app's own convention.

## Verification reality

`the_visaguy` has **six test files, all empty `FrappeTestCase` stubs**. Nothing exercises the WhatsApp handlers or the send path. Any test coverage for 3b and 3c is being written from zero, and the Company→Zone migration will land with no pre-existing regression net.

`waflo` does have real tests (20 passing from FEAT-003), so 3a can be regression-checked properly.
