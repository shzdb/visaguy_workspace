---
id: TASK-014
feature: FEAT-003
title: Outbound rate limiting, account ceiling, and retry integrity
status: completed
repository: waflo
owners: []
depends_on:
  - TASK-013
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Outbound rate limiting, account ceiling, and retry integrity

## Objective

Fix D3 and D7 — outbound transactional sends bypassed the limiter entirely, and there was no cap on total sends per account per window.

This is the **highest-risk task in FEAT-003**: it changes behaviour on the live send path, which per [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md) is what `waflo` actually does in production.

## Owner decisions applied

- A transactional message must **never** be dropped. When rate limited it is deferred and retried, never discarded.
- Conversational replies remain the only thing that may be dropped, and that already happens at the inbound gate.
- The account-level ceiling is **built but disabled by default** — blank/zero means inert, so behaviour is unchanged until an operator sets a value.

## Required behaviour

- `send_whatsapp_template` gains `rate_limit=True`; callers already gated and counted (the flow processor) pass `rate_limit=False` to avoid double counting.
- A rate-limited transactional send persists a `WhatsApp Message` with `custom_should_retry = 1` and no `message_id`, picked up by the existing hourly `schedule_retry_message`.
- An account-level ceiling enforced on a separate key, inert when unset.

## Implementation evidence

`tridz-dev/waflo`, branch `feat/waflo-correctness`:

| Commit | Subject |
|---|---|
| `1ab527f` | feat(rate-limit): requeue transactional outbound sends and add account ceiling |
| `de72ec5` | fix(rate-limit): use existing hourly WhatsApp Message retry instead of worker sleep |
| `56899f2` | fix(retry): stop deferred retries from orphaning messages via null message_id lookup |

Files: `send.py`, `logs.py`, `retry_message.py`, `rate_limiting.py`, `processor.py`, `wf_account_settings.json`, `tests/test_outbound_rate_limit.py`, `tests/test_retry_message.py`.

## Deviations from plan — two corrections during implementation

### 1. Worker-blocking backoff, rejected (`de72ec5`)

The first implementation used `time.sleep()` inside the worker. A sleeping RQ worker is a blocked worker; a handful of deferred messages would starve the `short` queue.

Investigation established that **no delayed-enqueue primitive is available on this bench**: `frappe.enqueue(timeout=)` is passed to RQ as `job_timeout`, a maximum-execution kill-switch (`frappe/utils/background_jobs.py:160`), not a schedule; and `bench worker` runs without `--with-scheduler`, so RQ's `enqueue_in` would never fire.

Corrected to reuse `waflo`'s **existing production retry pipeline** — `custom_should_retry` plus the hourly `schedule_retry_message` — rather than inventing a mechanism.

### 2. Message loss on a deferred retry, found in re-verification (`56899f2`)

`send_whatsapp_template` returns `None` when it defers, having persisted a pending record with no `message_id`. `retry_message` then ran `get_value("WhatsApp Message", {"message_id": None})`, which matches NULL-id rows — and pending records are exactly that, by design of this task's own fix. It selected an arbitrary unrelated record and set `custom_retried_message` on the original, permanently excluding it from `schedule_retry_message`. **The transactional message was silently lost**, violating the never-drop requirement.

Fixed by tracking the pending row in `frappe.flags.waflo_deferred_pending_message`; on a deferred result the original stays eligible and the sibling just created is neutralised, keeping exactly one row in the retry pool. If neutralisation fails the original still stays retriable — deliberately preferring duplication over loss.

This defect existed only in the seam between the new deferral and pre-existing retry code, and was found only after ADR-009 established that the send path is the live path.

## Validation

`test_outbound_rate_limit.py` (5 tests), `test_retry_message.py` (5 tests). Full suite 20/20 on the `visaguy` dev site @ `56899f2`.

Round-trip fidelity verified — a deferred message preserves the two capabilities `waflo` exists to provide:

| Value | Written as | Read back as |
|---|---|---|
| dynamic URL buttons | `buttons` | `button_url_map` |
| FLOW button | `custom_is_flow` | `use_flow` |
| header params | `template_header_parameters` | same |
| body params | `body_param` | same |
| reference | `reference_doctype` / `reference_name` | same |

Also guarded: `get_whatsapp_account` returning `None` (no default outgoing account) previously raised `AttributeError` inside the new rate-limit branch.

## Known limitations

- **Retry granularity is hourly.** A deferred transactional message can arrive up to an hour late. Acceptable per the never-drop decision, but coarse — see the follow-up note in FEAT-003.
- Redis, the queue, and the Meta API are mocked in all tests. **No deferred-then-retried message has been delivered end to end on a real site.** Given this task's second deviation was a defect in exactly that seam, an end-to-end retry test is strongly recommended before deployment.
- The account ceiling has never been exercised with a real value, only with blank/zero and with a mocked configured value.
