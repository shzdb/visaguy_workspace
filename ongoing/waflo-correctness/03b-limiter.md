# Phase 3b — Atomic rate limiter (D2 / D4 / D5 / N3)

Branch: `feat/waflo-correctness`  
Built on: `3e2428a` (phase 3a — `whatsapp_account` threaded into `process_whatsapp_message`)

---

## New `rate_limiting.py` design

Replaced the compound dict `{"count": N, "window_start": T}` read-modify-write with a
fixed-window atomic counter on `frappe.cache()` (RedisWrapper → redis.Redis):

```
key = f"waflo:rl:{account}:{mobile_no}"
count = frappe.cache().incr(key)
if count == 1:
    frappe.cache().expire(key, window_seconds)
```

- **D4:** `INCR` is atomic; concurrent workers serialize without a Python RMW race.
- **D5:** TTL is set only when `incr` returns `1` (first hit opens the window). Mid-window
  increments no longer refresh expiry. `window_start` is gone — Redis TTL is the window.
- **Read path:** `is_rate_limited` uses `cache.get(key)` → `int(raw)` and compares to
  `max_replies`. Absent key → allow. No `get_value` / pickle path (incompatible with raw INCR).
- **No** site prefixing, `make_key`, or separate redis-py connection (settled VisaGuy
  one-site-per-bench decision).
- Public names/signatures unchanged: `is_rate_limited`, `increment_rate_limit`,
  `set_message_rate_limited`.

Shared helper `_rate_limit_configured(settings)` gates both check and increment.

---

## B3 — Continuing-conversation increment (D2)

**Location:** `waflo/waflo/flow/processor.py:125`

**Placement reasoning:**

The continuing path (after `active_doc = frappe.get_doc(...)`) has two mutually exclusive
send branches:

1. `matched_step.message_template` truthy → one `send_whatsapp_template`
2. else → optionally jump to `next_step_name` and send if that step has a template

Never both. A step may also send nothing (no template on matched or next).

Therefore a `sent` flag is set only inside a branch that actually called
`send_whatsapp_template`, then a single:

```python
if sent:
    increment_rate_limit(whatsapp_account, mobile_no)
```

runs at line 125.

- Step that sends nothing → `sent` stays False → no increment.
- Step that sends once (either branch) → one increment.
- Cannot double-count: only one branch executes per turn.

Left alone (per policies): new-conversation increment at line 74, and
`send_default_message` increment at line 185.

---

## N3 — Incomplete configuration

Both `is_rate_limited` and `increment_rate_limit` now share `_rate_limit_configured`:

- `enable_rate_limiting` must be on
- `max_replies_per_window` and `window_seconds` must be truthy
- both must convert to `int` ≥ 1

If incomplete: check returns False (allow); increment returns without writing.
A key is never written without a positive TTL.

---

## Tests added

| Test | Asserts |
|------|---------|
| `test_first_increment_sets_ttl_once` | three `incr` calls; `expire` called exactly once with `(key, 60)` on first; no `set_value` |
| `test_is_rate_limited_at_and_below_max` | count 2 / max 3 → False; count 3 → True; absent key → False |
| `test_incomplete_config_never_writes_key` | None/0/"" for max or window → neither check nor increment touches cache |
| `test_continuing_conversation_send_increments_rate_limit` | existing active flow + template send → `increment_rate_limit(account, mobile)` once (D2 regression) |

All mock `frappe.cache()` / `frappe.get_cached_doc` (or processor collaborators). No live Redis.
`FrappeTestCase`. **Not executed** — no site available for `bench run-tests` (static only).

Files: `waflo/waflo/tests/test_rate_limiting.py` (new), plus D2 case in
`test_process_whatsapp_message.py`.

---

## Gates

- `python -m py_compile` on all modified `.py` → pass
- `window_start` absent from `rate_limiting.py`
- no `make_key` / `redis.Redis` / `import redis` under `waflo/`
- diff limited to rate_limiting.py, processor.py, test files
- no conflict markers

---

## Uncertainties

- Whether Frappe's RedisWrapper `get()` always returns `bytes` vs already-decoded `str` for
  INCR keys — tests cover `b"N"`; `int(raw)` accepts both. If a site somehow still had a
  pickled dict under the same key from the old design, `int()` would fail-closed to allow
  (`except` → False) until the old key TTL expires; no migration helper was added (tight scope).
