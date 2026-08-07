# Waflo Correctness Manual Test Plan — `visaguy` dev site

For manually validating [FEAT-003](../../features/ongoing/waflo-correctness/README.md) — rate limiting, retry, and send hardening — on a Meta **test number**.

## The constraint, and why it barely matters

A Meta test number allows only ~5 pre-registered recipients and cannot sustain production-like volume. FEAT-003 is largely about rate limiting, which naively needs volume.

**It doesn't.** Nearly every FEAT-003 behaviour fires **before** the Meta API call:

- The rate limiter checks, and on a hit persists a retry record and returns — **no API call**.
- D9 (unknown template) and D11 (`use_flow` + `button_url_map`) **throw** before the payload is built.
- D8 (error handler) is best tested by forcing a failure, which never reaches Meta.
- D6 (`limit_after` removed) is a schema check.

So the organising principle here is **message cost**. Of 26 cases below, **18 cost zero real messages.**

Two levers replace volume:

1. **Lower the limit instead of raising the traffic.** Set `max_replies_per_window = 1`. Now the *second* message in a window defers — one send proves the limiter.
2. **Seed the counter directly.** The limiter uses a plain Redis key, so you can pre-load it and make the *very first* message defer.

```bash
bench --site visaguy execute frappe.client.set_value --kwargs '{"doctype":"WF Account Settings","name":"Visaguy UAE","fieldname":"max_replies_per_window","value":1}'
```

```bash
redis-cli -p 13008 set "waflo:rl:Visaguy UAE:<your-number>" 99 EX 300
```

```bash
redis-cli -p 13008 --scan --pattern "waflo:rl:*"
```

Restore afterwards: `max_replies_per_window = 3`, `window_seconds = 30`.

## Baseline configuration

| Setting | Current |
|---|---|
| `WF Account Settings` → `Visaguy UAE` | rate limiting **on**, **3 per 30s**, default template `default_reply-en` |
| `max_sends_per_window` (account ceiling) | **blank — disabled** |
| `WF Settings.enable_flow_engine` | **0 — off** |
| `WF Settings.inactive_timeout` | 0 |

**A worker must be running.** Most sends are `enqueue_after_commit=True`. Without `bench worker`, nothing happens and nothing is logged.

---

## Group 1 — Rate limiter core (zero messages)

Seed the counter so nothing reaches Meta.

| # | Test | Setup | Expected |
|---|---|---|---|
| **W-1** | Counter starts absent | `redis-cli -p 13008 del "waflo:rl:Visaguy UAE:<num>"` then trigger one send | Key created with value `1` and a TTL. `redis-cli ttl <key>` returns ≤ `window_seconds` |
| **W-2** | TTL set once, not extended (D5) | Trigger 2 sends within the window; check `ttl` after each | TTL **counts down** across both. It must not reset — that was D5 |
| **W-3** | Limit blocks (D3) | Seed key to `99`, trigger one outbound | **No API call.** A `WhatsApp Message` appears with `custom_should_retry = 1`, `custom_rate_limited = 1`, **no `message_id`** |
| **W-4** | Never dropped | Same as W-3 | The record exists and is selectable by `{"custom_should_retry": 1, "custom_retried_message": None}`. **Nothing is silently discarded** |
| **W-5** | Window expiry | After W-3, `redis-cli del` the key, trigger again | Sends normally. Counter restarts at 1 |
| **W-6** | Per-recipient isolation | Seed number A to `99`; send to number B | B sends. Key is `(account, mobile)` |
| **W-7** | Incomplete config writes nothing (N3) | Set `max_replies_per_window` blank, trigger a send | Send proceeds and **no `waflo:rl:` key is created**. Check/increment agree |
| **W-8** | Rate limiting off | Untick `enable_rate_limiting`, trigger sends | No keys created, no deferrals |

## Group 2 — Account ceiling (D7, zero messages)

| # | Test | Setup | Expected |
|---|---|---|---|
| **W-9** | Inert when blank | Confirm `max_sends_per_window` empty; send | No `waflo:rl:acct:` key. Ceiling disabled, behaviour unchanged |
| **W-10** | Ceiling blocks | Set `max_sends_per_window = 1`; send to number A, then number B | A sends; **B defers** even though B's own counter is empty — the account ceiling is independent of per-recipient |
| **W-11** | Ceiling key separate | `redis-cli --scan --pattern "waflo:rl:*"` | Two distinct key shapes: `waflo:rl:<acct>:<mobile>` and `waflo:rl:acct:<acct>` |

Restore `max_sends_per_window` to blank afterwards.

## Group 3 — Retry pipeline (1 message)

The seam that produced the message-loss bug. **Test this most carefully.**

| # | Test | Steps | Expected |
|---|---|---|---|
| **W-12** | Manual drain works | After W-3, run the retry job (below) | The deferred message **sends** — this is the 1 real message. `message_id` populated on a *new* record; `custom_retried_message` set on the original |
| **W-13** | Original leaves the pool | Re-run the retry job | The same message is **not** re-sent. `custom_retried_message` excludes it |
| **W-14** | Retry keeps FLOW button (F2/D4) | Defer a **feedback** message (has `custom_is_flow = 1`), then drain | Retried message still carries the FLOW button. `custom_is_flow` round-trips |
| **W-15** | Retry keeps URL buttons | Defer a **lead form** message, then drain | `/form/<id>` button intact — `buttons` → `button_url_map` round-trips |
| **W-16** | **Retry that is itself limited does not orphan** | Seed the key to `99`, then drain the retry queue | The original **stays** retriable — `custom_retried_message` must remain **empty**. This is the exact message-loss defect fixed in `56899f2`. If this field gets set, the message is lost forever |
| **W-17** | Retry uses the stored account | Check the retried record | `whatsapp_account` matches the original's, not the global default |

```bash
bench --site visaguy execute waflo.waflo.doctype.wf_settings.wf_settings.schedule_retry_message
```

## Group 4 — Send hardening (zero messages — all throw before the API)

| # | Test | Steps | Expected |
|---|---|---|---|
| **W-18** | Unknown template (D9) | Call `send_whatsapp_template` with `template_name="does_not_exist"` | Throws naming the template. **No** payload with `"name": null` reaches Meta |
| **W-19** | Unknown account | Pass `whatsapp_account="No Such Account"` | Throws, explicitly refusing to fall back to the default |
| **W-20** | No default account | Untick `is_default_outgoing` on `Visaguy UAE`, send with no account | Clear error, not `AttributeError`. **Re-tick immediately afterwards** |
| **W-21** | `use_flow` + `button_url_map` (D11) | Call with both set | Throws explaining both claim button index 0 |
| **W-22** | Error handler preserves cause (D8) | Temporarily set a bad `token` on the account, trigger a send | Error Log shows the **original** exception with traceback — **not** `AttributeError` on `frappe.flags.integration_request`. Restore the token |
| **W-23** | No log spam (D10) | Trigger a send **with buttons**, then read the Error Log | **No** `WhatsApp API URL AND INDEX` entries. One send, no debug noise |

`bench --site visaguy console` is the easiest driver for W-18/19/21:

```python
from waflo.waflo.messaging.send import send_whatsapp_template
send_whatsapp_template(mobile="<num>", template_name="does_not_exist")
```

## Group 5 — Schema and config (zero messages)

| # | Test | Expected |
|---|---|---|
| **W-24** | `limit_after` is gone (D6) | The field is absent from the `WF Settings` form. `bench --site visaguy execute frappe.client.get_value --kwargs '{"doctype":"WF Settings","fieldname":"limit_after"}'` errors or returns nothing |
| **W-25** | Rate limiting tab has no dead knobs | Every field under Rate Limiting is read by code: `enable_rate_limiting`, `max_replies_per_window`, `window_seconds`, `max_sends_per_window` |

## Group 6 — Inbound (1–2 messages, needs your test number)

| # | Test | Expected |
|---|---|---|
| **W-26** | Inbound gets a default reply | Message the test number → reply using `default_reply-en`, sent **from the account the message arrived on** |
| **W-27** | Inbound rate limited is dropped, not deferred | Seed the key to `99`, send inbound | Inbound message marked `custom_rate_limited = 1`, **no reply**. Inbound *is* dropped — this differs from outbound deliberately |
| **W-28** | Video header (N4) | Set `header_type = Video` on `WF Account Settings`, send inbound | No `AttributeError` on a non-existent `header_video` field. Restore `header_type` afterwards |

> Meta test numbers open a 24-hour session on an inbound message. `default_reply` is a **template**, so it sends regardless — but keep the window in mind if you experiment with free-form replies.

---

## Optional Group 7 — Flow engine (D1, D2, N1, N2)

**These four defects are dormant.** `enable_flow_engine = 0`, and the engine has never been tested ([FEAT-004](../../features/planned/whatsapp-flow-engine/README.md)).

Testing them means switching the engine on. On `visaguy` with a test number that is defensible — no real customers — but it is genuinely untested code, and FEAT-003 fixed only the four defects it names, not the engine as a whole.

**If you skip this group, FEAT-003's live-path value is still fully covered by Groups 1–6.** D1/D2/N1/N2 are prerequisites for FEAT-004, not for shipping FEAT-003.

If you do proceed: set `enable_flow_engine = 1`, create a minimal `WF Message Flow` with a default flow and an initial step, then:

| # | Test | Expected |
|---|---|---|
| **W-29** | New conversation creates a flow (D1) | Message the number from a new sender | **Exactly one** `WF Active Chat Flow` created. Before the fix, none was created |
| **W-30** | No message loop (D1) | Send a second inbound from the same number | The flow **advances**. The initial step is **not** re-sent. A repeat means D1 regressed |
| **W-31** | Flow sends have correct arguments (N1) | Inspect the outgoing record | Buttons in buttons, not in the header. `reference_name` populated, not dropped |
| **W-32** | Continuing flow counts (D2) | Advance a flow twice, watch the Redis key | Counter increments on continuing sends, not only the first |
| **W-33** | Null reference doesn't stall (N2) | Create an active flow with no `reference_doctype`/`reference_name`, send inbound | Advances without raising |

**Set `enable_flow_engine` back to `0` when done.**

---

## What this plan cannot prove

- **Concurrency (D4).** The atomic `INCR` fix is the whole point, but proving it needs parallel workers hitting the same key simultaneously. Sequential manual tests cannot distinguish atomic from non-atomic. `INCR` is atomic by definition, so the risk is in the surrounding logic, not the primitive.
- **Production volume.** A test number cannot show behaviour under real load, quality-rating effects, or Meta tier throttling.
- **Real hourly cadence.** W-12 invokes the retry job manually. The actual hourly scheduler is not exercised.
- **`max_replies_per_window` sizing.** Whether 3-per-30s is right for production is a judgement call, not a test outcome. See risk #41 — `_send_payment_received` alone sends two messages back to back.

## Restore checklist

1. `max_replies_per_window` → **3**, `window_seconds` → **30**
2. `max_sends_per_window` → **blank**
3. `enable_rate_limiting` → **ticked**
4. `enable_flow_engine` → **0** (if Group 7 was run)
5. `header_type` on `WF Account Settings` → original (if W-28 was run)
6. `token` on `Visaguy UAE` → original (if W-22 was run)
7. `is_default_outgoing` on `Visaguy UAE` → **ticked** (if W-20 was run)
8. `redis-cli -p 13008 --scan --pattern "waflo:rl:*" | xargs -r redis-cli -p 13008 del`
9. Delete test `WhatsApp Message` rows and any `WF Active Chat Flow` rows created
