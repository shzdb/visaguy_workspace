# Phase 3c — Outbound rate limiting (D3) + account ceiling (D7)

Branch: `feat/waflo-correctness`  
Built on: `31da123` (phase 3b — atomic limiter)

---

## Backoff design and bound

Transactional outbound sends (`send_whatsapp_template` with `rate_limit=True`, the default)
must never be dropped. When per-recipient or account ceiling is hit:

1. Do **not** call the WhatsApp API.
2. Re-enqueue `_send_whatsapp_template` on the **`long`** queue via `frappe.enqueue`.
3. Pass `_rate_limit_delay = window_seconds` (fallback **60** if unset) and
   `_rate_limit_attempt` incremented by one.
4. The worker `time.sleep`s that delay before re-checking. Frappe’s public `frappe.enqueue`
   has no portable delay/schedule API (RQ `enqueue_in` needs a scheduler process Frappe
   does not enable by default), so sleep-in-worker is the delay mechanism. Timeout is
   `max(delay + 300, 600)`.
5. Logging uses `frappe.logger("waflo").info` — not `log_error`.

**Retry bound: `RATE_LIMIT_MAX_RETRIES = 5`.**

After five failed re-queues the send is abandoned (returns `None`, info log). This stops a
permanently-limited recipient or saturated account from looping forever. Operators can
still use the existing manual `retry_message` path.

On a successful send with `rate_limit=True`, both `increment_rate_limit` and
`increment_account_rate_limit` run (account increment is a no-op when the ceiling is off).

---

## C3 — `retry_message` decision

**Decision: keep rate limiting on (`rate_limit=True`, made explicit at the call site).**

Reasoning:

- Manual/admin retries are outbound re-attempts, often of transactional templates that
  previously failed. They are **not** gated by the inbound conversational check in
  `_process_incoming_whatsapp_message`.
- Passing `rate_limit=False` would let retries bypass both per-recipient and account
  ceilings and could worsen Meta-tier pressure.
- With `rate_limit=True`, a retry under load re-queues with the same backoff instead of
  being dropped or slamming the API.

No other behavioural change in `retry_message.py`.

---

## Account-ceiling key design (D7)

| Item | Value |
|------|-------|
| Field | `WF Account Settings.max_sends_per_window` (Int), rate-limiting tab |
| Disable | blank / zero / falsy → **DISABLED** (no key read/write) |
| Also requires | `enable_rate_limiting` and `window_seconds >= 1` |
| Key | `waflo:rl:acct:{account}` |
| Ops | same atomic `frappe.cache().incr()` + `expire` on first hit as per-recipient |
| Window | same `window_seconds` as per-recipient |

APIs: `is_account_rate_limited(account)`, `increment_account_rate_limit(account)`.

Enforced only on the C1 outbound path (`rate_limit=True`), alongside `is_rate_limited`.
Default blank field → behaviour unchanged until an operator sets a positive ceiling.

---

## Avoiding double-counting

Flow-driven sends are already:

1. Gated inbound via `is_rate_limited` in `_process_incoming_whatsapp_message`.
2. Counted via explicit `increment_rate_limit(...)` after send in `processor.py`.

All four `send_whatsapp_template` call sites in `processor.py` now pass
`rate_limit=False`. The send path therefore neither checks nor increments for those
calls — flow increments remain sole, single counters. Explicit `increment_rate_limit`
calls in processor are unchanged.

External callers (`the_visaguy`, etc.) keep the default `rate_limit=True` and get
check + requeue + increment. New parameter is at the **end** with a default so existing
positional/keyword calls do not break.

---

## Tests added (`waflo/waflo/tests/test_outbound_rate_limit.py`)

| Test | Asserts |
|------|---------|
| `test_rate_limited_transactional_send_is_reenqueued_not_dropped` | when limited: `frappe.enqueue` once with attempt/delay/long queue; `make_post_request` never called; returns `None` |
| `test_retry_bound_is_respected` | at `RATE_LIMIT_MAX_RETRIES`: no enqueue, no send, info log |
| `test_flow_path_rate_limit_false_does_not_double_increment` | `rate_limit=False`: send proceeds; `is_rate_limited` / increments not called from send path |
| `test_account_ceiling_blocks_when_configured` | count at max → limited; `incr`/`expire` on `waflo:rl:acct:{account}` |
| `test_account_ceiling_inert_when_blank_or_zero` | None/0/""/False → no cache touch |
| `test_outbound_path_enforces_account_ceiling` | account limited alone → re-enqueue, no send |

Mocks: `frappe.cache()`, `frappe.enqueue`, `make_post_request`, `get_whatsapp_account`,
limit helpers. `FrappeTestCase`. **Not executed** — no site for `bench run-tests`.

---

## Gates

- `python -m py_compile` on all modified `.py` → pass
- DocType JSON parses → yes
- no `make_key` / `import redis` / `redis.Redis` under `waflo/`
- all four processor `send_whatsapp_template` calls pass `rate_limit=False`
- no conflict markers
- D8–D11 / `WF Settings.limit_after` untouched

---

## Uncertainties

- Sleep-in-worker for backoff holds a `long` queue worker for up to `window_seconds`.
  Acceptable for VisaGuy’s volume; a durable delayed-job table would be better if windows
  grow large (hours). Documented trade-off vs unavailable RQ scheduler.
- Account ceiling is **not** incremented on flow-path sends (`rate_limit=False`). Per owner
  scope (enforce on C1 outbound only). Conversational volume therefore does not consume the
  account ceiling counter until a later decision expands it.
