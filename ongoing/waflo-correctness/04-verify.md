# Phase 4 — Verification

## Honest verification level

**statically-verified.** No test in this branch has been executed.

`waflo` is installed only on the production site `visaguy`. `visa-tracker-test.localhost` does not have it, and neither local bench has it. Per the owner's decision, this run ships static verification only. Nothing below claims a passing test suite.

## Gates run by the orchestrator against the full branch

| Gate | Result |
|---|---|
| `python3 -m compileall waflo/` | pass, no errors |
| All doctype JSON files parse | pass |
| `grep -rn "limit_after" waflo/` | empty — D6 fully removed from JSON, Python, and field_order |
| `grep -rn "time.sleep\|import time" send.py` | empty — worker-blocking backoff gone |
| `grep -rn "header_video" waflo/` | empty — N4 fixed |
| `grep -rn "WhatsApp API URL AND INDEX" waflo/` | empty — D10 log spam gone |
| `grep -rn "make_key\|import redis\|redis.Redis" waflo/` | empty — no site-prefixing, no separate Redis client |
| `grep -n "window_start" rate_limiting.py` | empty — D5 dual-mechanism resolved |

## Backward compatibility with `the_visaguy`

`the_visaguy/handlers/whatsapp_message.py` imports `send_whatsapp_template` from
`waflo.waflo.messaging.send` and calls it with keyword arguments only.

Final signature:

```
send_whatsapp_template(mobile, template_name, body_params=None, header_params=None,
                       button_url_map=None, ref_doctype=None, ref_name=None,
                       use_flow=False, queue=False, rate_limit=True)
```

The original parameter order is unchanged and the one new parameter is appended with a default. **Existing callers do not break.**

The behavioural change is intentional: `rate_limit=True` by default means `the_visaguy`'s transactional messages are now subject to the limiter, which is the point of D3.

## Runtime configuration — blast radius

Read from the production site, read-only:

| Setting | Value |
|---|---|
| `WF Account Settings` (`Visaguy UAE`) `enable_rate_limiting` | **1 (on)** |
| `max_replies_per_window` | **3** |
| `window_seconds` | **30** |
| `WF Settings.enable_flow_engine` | **0 (off)** |

### This corrects a claim in FEAT-003

FEAT-003 states the limiter "is inert whenever the flow engine is enabled". That is accurate as written, but the feature document did not establish that **the flow engine is currently off in production**.

Consequences of that, which change the urgency assessment:

- `process_whatsapp_message` is only reached when `enable_flow_engine` is on. **D1's `NameError` is therefore not currently firing in production.** It is dormant.
- With the flow engine off, inbound messages go to `send_default_message`, which calls `increment_rate_limit` correctly. **The limiter does work today.**
- D1, D2, N1, and N2 are all latent defects on the flow-engine path. They detonate the moment someone enables `enable_flow_engine`.

**Do not enable `WF Settings.enable_flow_engine` on production until this branch is deployed.** Before this branch, enabling it would produce a customer-visible message loop (D1) and mangled button/reference arguments on every send (N1).

### New behaviour to watch on deployment

With `enable_rate_limiting = 1`, `max = 3`, `window = 30s`, and D3 now applying the limiter to outbound transactional messages:

- A 4th message to the same recipient inside 30 seconds is no longer sent immediately. It is persisted with `custom_should_retry = 1` and picked up by the existing **hourly** `schedule_retry_message`.
- Worst case, that message arrives up to an hour late. It is never dropped, which is the owner's stated requirement.
- `_send_payment_received` in `the_visaguy` sends **two** messages back to back (invoice PDF, then payment feedback). Combined with a form link, a single customer can legitimately approach 3 messages in one burst.

Recommendation before deploying: either raise `max_replies_per_window` for the account, or add a more frequent retry cron. Hourly retry granularity was appropriate when retries were rare error-recovery; it is coarse for routine rate-limit deferral. Flagged, not fixed — changing the cron was explicitly out of scope.

## What was NOT verified

- No test executed. All test files are new and unrun.
- No live WhatsApp API interaction.
- The retry path's `WhatsApp Message` insert was reasoned about, not executed. Supporting evidence: production rows created by the pre-existing `log_whatsapp_message` — which likewise never sets the mandatory `content_type` — exist with `content_type = "text"`, so Frappe supplies the Select default on insert. The new sibling uses an identical construction.
- `before_insert` on `WhatsApp Message` was confirmed by source reading to skip its send branch when `message_type == "Template"`, which the retry record sets. So persisting the record does not trigger an immediate send. Source-verified, not runtime-verified.

## Recommended first runtime checks after deployment to a test site

```bash
bench --site <site> run-tests --app waflo
```

Then, with the flow engine still off, confirm no regression in default replies. Only then enable `enable_flow_engine` on the test site and exercise a new conversation end to end, asserting exactly one `WF Active Chat Flow` is created.
