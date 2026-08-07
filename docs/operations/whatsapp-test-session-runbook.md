# WhatsApp Test Session Runbook

The single execution sequence for manually testing FEAT-002 and FEAT-003 on `visaguy`. Run this top to bottom in one session.

Case detail lives in the two plans; this runbook is the **order, the setup, and the commands**:

- [FEAT-002 multi-zone routing](whatsapp-manual-test-plan.md) — cases `T-*`
- [FEAT-003 waflo correctness](waflo-correctness-test-plan.md) — cases `W-*`

## Why the order matters

**Run FEAT-002 routing first, FEAT-003 limiter second.**

FEAT-003's tests deliberately break the rate-limit configuration — dropping the limit to 1, or seeding the counter to 99. If you do that first, FEAT-002 routing tests will defer messages instead of sending them, and a deferral looks exactly like a routing failure. You would be debugging the wrong thing.

Routing tests need the limiter behaving normally. Limiter tests don't care about routing.

---

## Phase 0 — Environment readiness

**Do not skip this.** As of the last check the environment was **not** ready to run a single test.

### 0.1 — Current state

| Check | Status | Consequence |
|---|---|---|
| Redis (13008 / 12008 / 11008) | ✅ running | — |
| **Workers online** | ❌ **0** | **Nothing enqueued ever runs.** Every send is `enqueue_after_commit=True` — you would see no message, no error, nothing |
| Scheduler | ❌ disabled | Hourly retry won't self-fire. Fine — we invoke it manually |
| `default` queue backlog | ⚠️ **995 jobs** | Mostly `delete_dynamic_links`. A general worker chews these first |
| `short` queue | ✅ **empty** | This is where WhatsApp sends go |

### 0.2 — Start a worker scoped to `short`

Because `short` is empty and `default` has 995 backlogged jobs, scope the worker. You get immediate feedback and don't churn the backlog.

```bash
cd ~/bench && bench worker --queue short
```

Leave it running in its own SSH session for the whole test session. You will watch it.

### 0.3 — Confirm it registered

```bash
cd ~/bench && bench --site visaguy doctor 2>&1 | grep -i "workers online"
```

Must report **1** or more. If it still says 0, nothing below will work.

### 0.4 — Second window for logs

```bash
tail -f ~/bench/logs/worker.error.log
```

### 0.5 — Confirm the code under test

```bash
cd ~/bench/apps && for a in waflo the_visaguy; do printf "%-14s %s @ %s\n" "$a" "$(git -C $a rev-parse --abbrev-ref HEAD)" "$(git -C $a rev-parse --short HEAD)"; done
```

Expect `waflo feat/multi-zone-whatsapp @ f81fe81` and `the_visaguy feat/multi-zone-whatsapp @ aa3ef89`.

---

## Phase 1 — Baseline capture

Record what you are starting from, so restore is unambiguous.

```bash
cd ~/bench && bench --site visaguy execute frappe.client.get_list --kwargs '{"doctype":"WF Account Settings","fields":["name","whatsapp_account","enable_rate_limiting","max_replies_per_window","window_seconds","max_sends_per_window","header_type"],"limit_page_length":0}'
```

```bash
cd ~/bench && bench --site visaguy execute frappe.client.get_list --kwargs '{"doctype":"Whatsapp Default","fields":["name","zone","whatsapp_account","enabled"],"limit_page_length":0}'
```

Expected baseline: rate limiting **on**, **3 per 30s**, `max_sends_per_window` **blank**, one `Whatsapp Default` for zone `TVG` bound to `Visaguy UAE`.

---

## Phase 2 — Test data

### 2.1 — Second account for routing (no Meta account needed)

Create a `WhatsApp Account` reusing `Visaguy UAE`'s credentials:

- `account_name` = `Test Zone B`
- `phone_id`, `token`, `url`, `version` — **copy from `Visaguy UAE`**
- `is_default_outgoing` / `is_default_incoming` — **leave unticked**
- `status` = Active

Messages still leave from the same physical number, but `WhatsApp Message.whatsapp_account` will record `Test Zone B`. That is the assertion that proves routing.

### 2.2 — Second zone configuration

Create a `Whatsapp Default`:

- `zone` = `TVG Saudi`, `whatsapp_account` = `Test Zone B`
- Five event templates (reuse the existing `*-en` records)
- Both feedback defaults with header images
- Tick `enabled` **last** — this also exercises M9 validation

### 2.3 — Test lead

A CRM Lead with `custom_zone`, `custom_customer_id`, `mobile_no` = **a number registered on your Meta test account**, and `first_name`. The Customer needs `custom_enable_whatsapp_notifications` ticked.

---

## Phase 3 — FEAT-002 routing (normal limits)

Rate limiting stays at 3/30s. Full detail in the [FEAT-002 plan](whatsapp-manual-test-plan.md).

| Order | Cases | Focus |
|---|---|---|
| 3.1 | **T-B1 – T-B6** | Config validation. Zero messages — do these while creating 2.2 |
| 3.2 | **T-A1** | TVG lead → `whatsapp_account = Visaguy UAE` |
| 3.3 | **T-A2** | TVG Saudi lead → `whatsapp_account = Test Zone B` ← **headline assertion** |
| 3.4 | **T-A4** | Back-office: `custom_zone = TVG` + `custom_company = TVG India` → **UAE** |
| 3.5 | **T-A5** | `TVG Qatar` lead (unconfigured) → no message, warning, **no fallback** |
| 3.6 | **T-A3** | Repeat T-A1 — no regression |
| 3.7 | **T-C1 – T-C9** | Edge cases. Mostly zero messages |
| 3.8 | **T-F1 – T-F7** | Regression on existing message types |

> **Watch for T-C1:** a lead with no `custom_zone` produces an **Error Log entry** (`Zone is required`), not a warning. That is FIND-1 — a known inconsistency, not a new bug.
>
> **Pace T-F3/T-F4:** the payment event sends **two** messages back to back, consuming 2 of your 3-per-30s budget. Leave 30 seconds either side or the next test will defer unexpectedly.

---

## Phase 4 — FEAT-003 limiter (deliberately broken config)

Now break the limits. Full detail in the [FEAT-003 plan](waflo-correctness-test-plan.md).

### 4.1 — Seeding and inspection

```bash
redis-cli -p 13008 --scan --pattern "waflo:rl:*"
```

```bash
redis-cli -p 13008 set "waflo:rl:Visaguy UAE:<your-number>" 99 EX 300
```

```bash
redis-cli -p 13008 ttl "waflo:rl:Visaguy UAE:<your-number>"
```

```bash
redis-cli -p 13008 --scan --pattern "waflo:rl:*" | xargs -r redis-cli -p 13008 del
```

### 4.2 — Execution order

| Order | Cases | Cost |
|---|---|---|
| 4.2.1 | **W-1, W-2, W-5, W-6, W-7, W-8** | Limiter mechanics. Zero messages — seed the counter |
| 4.2.2 | **W-3, W-4** | Deferral creates a retry record, no API call. Zero messages |
| 4.2.3 | **W-12 – W-17** | Retry pipeline. **~1 real message.** Run **W-16** most carefully |
| 4.2.4 | **W-9, W-10, W-11** | Account ceiling. Zero messages |
| 4.2.5 | **W-18 – W-23** | Send hardening. Zero messages — all throw before the API |
| 4.2.6 | **W-24, W-25** | Schema. Zero messages |
| 4.2.7 | **W-26 – W-28** | Inbound. 1–2 messages, needs your test number |
| 4.2.8 | **W-29 – W-33** | Flow engine — **optional, and I suggest skipping** |

### 4.3 — Manual retry drain

```bash
cd ~/bench && bench --site visaguy execute waflo.waflo.doctype.wf_settings.wf_settings.schedule_retry_message
```

### 4.4 — Observe results

```bash
cd ~/bench && bench --site visaguy execute frappe.client.get_list --kwargs '{"doctype":"WhatsApp Message","filters":{"type":"Outgoing"},"fields":["name","to","template","whatsapp_account","message_id","custom_should_retry","custom_rate_limited","custom_is_flow","custom_retried_message"],"order_by":"creation desc","limit_page_length":15}'
```

---

## Phase 5 — Restore

Work through every line. Several tests leave config in a state that would misbehave.

```bash
cd ~/bench && bench --site visaguy execute frappe.client.set_value --kwargs '{"doctype":"WF Account Settings","name":"Visaguy UAE","fieldname":{"max_replies_per_window":3,"window_seconds":30,"max_sends_per_window":null,"enable_rate_limiting":1}}'
```

```bash
redis-cli -p 13008 --scan --pattern "waflo:rl:*" | xargs -r redis-cli -p 13008 del
```

Then by hand:

1. **`is_default_outgoing` and `is_default_incoming` re-ticked on `Visaguy UAE`** — if W-20 ran and you leave this off, **nothing sends at all**. Check this first.
2. `token` on `Visaguy UAE` restored — if W-22 ran.
3. `header_type` on `WF Account Settings` restored — if W-28 ran.
4. `WF Settings.enable_flow_engine` back to **0** — if Group 7 ran.
5. Delete the `TVG Saudi` `Whatsapp Default`.
6. Delete the `Test Zone B` `WhatsApp Account`.
7. Delete test `WhatsApp Message` and any `WF Active Chat Flow` rows.
8. Stop the worker (Ctrl-C) if it should not keep running.

### Confirm restore

```bash
cd ~/bench && bench --site visaguy execute frappe.client.get_list --kwargs '{"doctype":"WhatsApp Account","fields":["name","is_default_outgoing","is_default_incoming"],"limit_page_length":0}'
```

Must show `Visaguy UAE` with both flags = 1, and **no** `Test Zone B`.

---

## If nothing happens at all

In order of likelihood:

1. **No worker running.** Phase 0.2. This is the overwhelmingly most common cause.
2. Worker running on the wrong queue — sends go to `short`.
3. `Whatsapp Default.enabled` is 0 for that zone.
4. Customer's `custom_enable_whatsapp_notifications` unticked.
5. A stale `waflo:rl:` key is deferring silently — check `--scan`.
6. The lead's trigger field did not actually change; handlers check `has_value_changed`.

## What no amount of manual testing will prove

- **Concurrency (D4).** Sequential tests cannot distinguish an atomic counter from a racy one.
- **Real two-number isolation.** Both accounts share a `phone_id` in Phase 2.1, so messages leave from one physical number. Only a real Qatar WABA proves this.
- **Production volume and Meta tier behaviour.**
- **Whether 3-per-30s is the right production value** — a judgement call, informed by risk #41, not a test outcome.
