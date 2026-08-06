---
id: TASK-016
feature: FEAT-003
title: Verify the waflo correctness branch
status: completed
repository: waflo
owners: []
depends_on:
  - TASK-015
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Verify the waflo correctness branch

## Objective

Establish, honestly, what the branch has and has not been proven to do.

## What was run

```bash
bench --site visaguy run-tests --app waflo
```

Branch `feat/waflo-correctness` @ `56899f2`, on the `visaguy` **development** site (production is a separate, inaccessible server).

```
....................
Ran 20 tests in 0.389s

OK
```

**20/20 pass.** The count matches the branch's test files exactly — `test_outbound_rate_limit.py` (5), `test_process_whatsapp_message.py` (3), `test_rate_limiting.py` (3), `test_retry_message.py` (5), `test_send_hardening.py` (4). The four pre-existing doctype test files are empty scaffolds contributing zero, so nothing was silently skipped — this was checked rather than assumed.

`allow_tests` was enabled on the site and **left enabled**. Revert with `bench --site visaguy set-config allow_tests false` if the original state is wanted.

## Bench state

`apps/waflo` is bench-wide, so verification required checking the branch out there. It was **restored to `develop` @ `2167958`, clean** — identical to the pre-test state. The `feat/waflo-correctness` branch remains available locally on the bench and is pushed to `tridz-dev/waflo`.

## Verification level: statically-verified plus mocked unit tests

The suite runs in 0.389s, which tells you these are **mocked unit tests**. `frappe.cache()`, `frappe.enqueue`, `make_post_request`, and `get_whatsapp_account` are all mocked. They verify logic and wiring, not behaviour against real infrastructure.

Static gates, all passing across the branch: `python3 -m compileall`, all doctype JSON parses, and empty results for `limit_after`, `header_video`, `time.sleep`, `WhatsApp API URL AND INDEX`, `make_key`, `import redis`, and `window_start`.

## Backward compatibility

`the_visaguy` imports `send_whatsapp_template` and calls it with keyword arguments only. Original parameter order is unchanged; `rate_limit=True` is appended with a default. **Existing callers do not break.** The behavioural change — transactional messages now subject to the limiter — is the intent of TASK-014.

## Not verified

- **No integration test.** Real Redis, the real queue, and the Meta API are all mocked.
- **No deferred-then-retried message has been delivered end to end.** This is the most important gap: TASK-014's second defect lived precisely in that seam and was found by code reading, not by a test.
- The D6 removal patch has not been run via `bench migrate`.
- The account-level ceiling has never run with a real configured value.

## Pre-existing problem found, not caused by this branch

Per-module test runs fail on this bench:

```bash
bench --site visaguy run-tests --module waflo.waflo.tests.test_rate_limiting
```

→ `MandatoryError: [Company, _Test Indian Registered Company]: custom_display_name`

Frappe's `make_test_records` bootstrap cannot create its standard test Company because a customization made `custom_display_name` mandatory on Company. This blocks module-scoped testing for **every app on this bench** and is worth fixing separately. The app-level run does not hit this path.

## Recommended before deployment

1. Run an end-to-end retry test on a site: force a rate limit, confirm the deferred message is persisted with `custom_should_retry = 1` and later sent by `schedule_retry_message` with its FLOW button and URL buttons intact.
2. Run `bench migrate` to exercise the D6 removal patch.
3. Decide on `max_replies_per_window` — see the follow-up note in FEAT-003.
