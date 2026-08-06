---
id: TASK-013
feature: FEAT-003
title: Rewrite the rate limiter on an atomic counter
status: completed
repository: waflo
owners: []
depends_on:
  - TASK-012
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Rewrite the rate limiter on an atomic counter

## Objective

Fix D2, D4, D5 and N3 — the limiter did not count on flow paths, could not count atomically, ran two competing window mechanisms, and had check/increment disagreeing on incomplete configuration.

## Required behaviour

- Atomic fixed-window counter using `frappe.cache().incr()` / `.expire()`, with the TTL set only when the counter returns 1.
- Every send path increments: new flow, continuing flow, default reply.
- Check and increment agree on what "incompletely configured" means; no key is written without a positive TTL.
- Public function names and signatures preserved — other modules import them.

## Constraints

`frappe.cache()` is a Redis client (`RedisWrapper(redis.Redis)`), so no separate connection is needed. VisaGuy runs one site per bench, so no key prefixing.

## Implementation evidence

`tridz-dev/waflo`, branch `feat/waflo-correctness`, commit **`31da123`** — *fix(rate-limit): atomic fixed-window counter and count continuing sends*.

- `rate_limiting.py` rewritten: scalar counter at `waflo:rl:{account}:{mobile_no}`, shared `_rate_limit_configured(settings)` guard used by both check and increment, `window_start` removed entirely.
- D2 fixed in `processor.py` with a `sent` flag so the continuing-conversation branch increments exactly once per inbound turn regardless of which branch sent.
- Files: `rate_limiting.py`, `processor.py`, `tests/test_rate_limiting.py`.

## Validation

`test_rate_limiting.py` (3 tests). Full suite 20/20 on the `visaguy` dev site.

Orchestrator checks: `cache.get()` and `cache.incr()` are both raw Redis calls on the same plain key, so they cannot disagree — a mismatch here (prefixed write, unprefixed read) would have made the limiter silently inert. `int()` accepts both `bytes` and `str`, so the decode path is safe either way.

## Deviations

An earlier draft of FEAT-003 D4 called for `frappe.cache().make_key()` prefixing plus a two-site isolation test. Both were removed as scope creep after the owner confirmed **one site per bench, always**. See the decision log for 2026-08-06.

## Known limitations

Tests mock `frappe.cache()`. Atomicity under real concurrent workers against live Redis is **not** proven — `INCR` is atomic by definition, but the surrounding logic has not been exercised under real contention.
