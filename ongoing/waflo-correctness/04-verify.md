# Phase 4 — Verification

## Verification level: runtime-verified (tests), with limits stated below

The full `waflo` test suite was executed on the `visaguy` site on the `erpcode.tridz.in` bench, on branch `feat/waflo-correctness` @ `d057f1e`.

```
bench --site visaguy run-tests --app waflo
...............
Ran 15 tests in 0.068s

OK
```

All 15 tests pass. The count matches this branch's test files exactly — `test_outbound_rate_limit.py` (5), `test_process_whatsapp_message.py` (3), `test_rate_limiting.py` (3), `test_send_hardening.py` (4). The four pre-existing doctype test files are empty scaffolds and contribute zero tests, so nothing was silently skipped.

`allow_tests` had to be enabled on the site first (`bench --site visaguy set-config allow_tests true`). **It was left enabled.** Revert with `set-config allow_tests false` if you want the original state.

### Environment correction

An earlier draft of this document called `visaguy` the production site. **It is not.** Production is a separate server to which this project has no access. `visaguy` on `erpcode.tridz.in` is a development environment.

Two consequences:

1. Running the suite there is safe and appropriate, which is why this phase is no longer static-only.
2. **The runtime configuration read from `visaguy` says nothing about production.** See the retraction below.

### Bench state

`apps/waflo` is bench-wide, so testing required checking out the feature branch there. It has been **restored to `develop` @ `2167958`, clean** — identical to the pre-test state. The `feat/waflo-correctness` branch remains available locally on the bench and is pushed to `tridz-dev/waflo`.

## What the tests actually cover

The suite runs in 0.068s, which tells you these are **mocked unit tests**, not integration tests. `frappe.cache()`, `frappe.enqueue`, and `make_post_request` are all mocked. They verify logic and wiring; they do **not** verify behaviour against live Redis, a live queue, or the Meta API.

Covered:

- D1 — a new conversation creates exactly one `WF Active Chat Flow` and sends the initial step once
- N1 — `send_whatsapp_template` receives `button_url_map` / `ref_doctype` / `ref_name` in the correct parameters
- D2/D4/D5 — counter increments from absent to 1, TTL set exactly once, limit enforced at max, continuing-conversation sends counted
- N3 — incomplete configuration writes no key
- D3 — a rate-limited transactional send persists a retry record and makes no API call
- D7 — the account ceiling blocks when configured and is inert when blank
- D8 — a failure before the HTTP request still logs the original exception
- D9 — an unknown template raises rather than sending a null name
- D11 — `use_flow` combined with `button_url_map` is rejected
- N2 — a continuing flow with null reference doctype/name does not raise

## Severity — resolved

This document went back and forth on how urgent D1/D2/N1/N2 are. Settled position, per the project owner:

**The `waflo` conversational flow engine has never been tested and is not in use anywhere.** It is a planned capability ([FEAT-004](../../features/planned/whatsapp-flow-engine/README.md)), not a live one. `waflo`'s actual production role is a send helper plus rate limiting and retry ([ADR-009](../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md)).

So the defects split cleanly:

| Group | Defects | Reality |
|---|---|---|
| Live send path | D3, D4, D5, D8, D9, D10, D11, N3, D2's default-reply path | Runs on every message VisaGuy sends. Genuinely worth fixing. |
| Flow-engine path | D1, D2 (flow branches), N1, N2 | Cannot fire while the engine is off. **Prerequisites for FEAT-004, not live bugs.** |

Two earlier claims in this document are therefore withdrawn:

1. That D1/D2/N1/N2 were latent *because of a config value read from one site*. The real reason is stronger and site-independent: the feature they live in has never been switched on anywhere.
2. That "if production has the flow engine enabled, D1 and N1 are firing there today". That was an unfounded worry — the engine is untested by design, so it is not enabled in production either.

The operative instruction is unchanged and now has a clear owner: **do not set `enable_flow_engine = 1` on any site with real customers until this branch is deployed.** That is recorded as a prerequisite in FEAT-004.

Dev-site config, for reference: `enable_flow_engine = 0`, `enable_rate_limiting = 1`, `max_replies_per_window = 3`, `window_seconds = 30`. Production config remains unknown — that server is inaccessible to this project.

## Backward compatibility with `the_visaguy`

`the_visaguy/handlers/whatsapp_message.py` imports `send_whatsapp_template` and calls it with keyword arguments only. Final signature:

```
send_whatsapp_template(mobile, template_name, body_params=None, header_params=None,
                       button_url_map=None, ref_doctype=None, ref_name=None,
                       use_flow=False, queue=False, rate_limit=True)
```

Original parameter order unchanged; the one new parameter is appended with a default. Existing callers do not break.

The behavioural change is intentional: `rate_limit=True` by default brings `the_visaguy`'s transactional messages under the limiter, which is the point of D3.

## Static gates (also all passing)

| Gate | Result |
|---|---|
| `python3 -m compileall waflo/` | pass |
| All doctype JSON parses | pass |
| `grep -rn "limit_after" waflo/` | empty — D6 fully removed |
| `grep -rn "time.sleep\|import time" send.py` | empty — no worker-blocking backoff |
| `grep -rn "header_video" waflo/` | empty — N4 fixed |
| `grep -rn "WhatsApp API URL AND INDEX" waflo/` | empty — D10 gone |
| `grep -rn "make_key\|import redis\|redis.Redis" waflo/` | empty |
| `grep -n "window_start" rate_limiting.py` | empty — D5 resolved |

## Still not verified

- **No integration test.** Redis, the RQ queue, and the Meta API are mocked throughout. The atomic `incr`/`expire` behaviour is asserted against a mock, not against real Redis.
- **The retry path was never executed end to end.** No rate-limited message has actually been persisted and later picked up by `schedule_retry_message` on a real site.
- **Per-module runs fail on this bench**, e.g. `bench --site visaguy run-tests --module waflo.waflo.tests.test_rate_limiting`, with `MandatoryError: [Company, _Test Indian Registered Company]: custom_display_name`. This is a **pre-existing site-data problem**, not a defect in this branch: Frappe's `make_test_records` bootstrap cannot create its standard test Company because a customization added a mandatory `custom_display_name` field to Company. The app-level run does not hit this path. Worth fixing separately — it blocks module-scoped testing for every app on this bench.

## Recommended next runtime checks

1. Check `WF Settings.enable_flow_engine` on production to establish real urgency.
2. On a site with waflo, enable the flow engine and exercise a new inbound conversation end to end, asserting exactly one `WF Active Chat Flow` is created and the initial step is sent once.
3. Force a rate-limit condition and confirm the deferred message is persisted with `custom_should_retry = 1` and later sent by the hourly `schedule_retry_message`.
