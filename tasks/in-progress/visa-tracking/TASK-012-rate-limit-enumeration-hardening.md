---
id: TASK-012
feature: FEAT-001
title: Constrain credential enumeration in public verification rate limiting
status: in-progress
repository: the_visaguy
owners: []
depends_on:
  - ADR-005
  - ADR-009
  - TASK-007
created: 2026-07-23
updated: 2026-09-01
---

# TASK-012: Constrain credential enumeration in public verification rate limiting

## Decision (owner, 2026-09-01)

The product decision that previously blocked this task has been made:

- Add a **complementary coarser per-IP failure counter** alongside the existing
  per-identity one.
- Per-IP threshold: **20 failed attempts per IP per hour**, with a **60-minute
  lockout**.
- The existing per-credential limit is **explicitly unchanged**: 5 failures /
  15-minute lockout.
- The per-identity bucket must **not** be removed — it is what prevents an
  attacker locking a legitimate applicant out of their own record.

**Rationale accepted by the owner:** 20/hour cuts DOB enumeration from ~36,500
candidates to roughly 480/day from a single IP, which kills it as a practical
attack, while leaving headroom for a shared office, hotel, agency, or
mobile-carrier NAT where several genuine applicants may check status from one
address in a given hour.

No per-origin counter was requested; this task implements the per-IP counter
only, in addition to the existing per-identity counter.

## Severity

Medium-high, and **live**. Public tracking is enabled on `visaguy`, so this is
currently reachable rather than theoretical. Recorded as risk 18 in
`docs/risks-and-open-questions.md`. Risk 18 stays open until this task lands
and is proven at runtime — do not close it as part of this task's paperwork;
close it only after the live-HTTP validation below is actually run and
passes.

## Problem

`visa_tracking/api/verification.py:102` sets `target_bucket = candidates[0][0]`
— the passport+DOB lookup hash — so
`rate_limit_service.build_client_key(origin_scope, source_ip, target_bucket)`
scopes the failure counter to an **exact credential pair**.

Proven empirically over real HTTP against real Redis:

- 7x the **identical** wrong pair -> locks out at attempt 6, `Retry-After: 900`.
  Works as designed.
- 7x the same passport with an **incrementing DOB** -> **never locks out (0/7)**.

An attacker who knows a passport number can therefore enumerate dates of birth
(~36,500 candidates for an adult) from a single IP, unthrottled. Because every
failure returns a byte-identical HTTP 200, there is **no client-visible signal**
that throttling is absent — which is why both the 248-test suite and a passing
live lockout probe missed it.

## Required behaviour

This is the settled design. Implement it as specified below; do not redesign
the approach or thresholds.

**Do not remove the per-identity bucket.** It is deliberate: it prevents an
attacker locking a legitimate applicant out of their own record by repeatedly
failing against their credentials. The new counter is additive.

1. **New coarse key.** Add
   `build_client_scope_key(origin_scope, source_ip)` to
   `visa_tracking/services/rate_limit_service.py`, using the same keyed-HMAC
   bucket construction as the existing `build_client_key`, but **without** the
   target bucket component, so a varying DOB no longer yields a fresh counter.
   It must use its own distinct cache-key prefix constant so it can never
   collide with the per-identity key.

2. **Same fixed-window semantics as today.** The existing counter sets its TTL
   on first failure and preserves it across increments (fixed window, not
   sliding — this is a deliberate documented choice in the service's own
   module docstring). The new counter follows the identical pattern, so a
   60-minute window and a 60-minute lockout are one and the same TTL, and
   `Retry-After` remains the remaining TTL.

3. **Two new `Visa Tracker Settings` fields**: `scope_maximum_failed_attempts`
   (default 20) and `scope_lockout_minutes` (default 60), each clamped between
   MIN/MAX bounds exactly as `maximum_failed_attempts` and `lockout_minutes`
   already are, with defaults in `visa_tracking/utils/constants.py` so an
   unconfigured or empty Single still fails safe.

4. **Both counters consulted.** In `visa_tracking/api/verification.py`, build
   both keys and refuse the request when **either** counter has tripped.
   `Retry-After` is the greater of the two remaining lockout values.

5. **Increment site unchanged.** Only a genuine `not_found` result increments
   either counter — not CORS rejections, malformed request bodies, or the
   feature-disabled path. Enumeration inherently produces `not_found`, and
   restricting increments this way stops a malformed-request flood from
   locking out a shared IP.

6. **Byte-identical generic failure body.** The generic failure response body
   must stay byte-identical across every failure mode. Only the `Retry-After`
   **header** may vary. This property is load-bearing for the privacy design
   and for the frontend wire contract — treat it as a hard constraint, not a
   nice-to-have.

## Schema and deployment impact

- This needs a `Visa Tracker Settings` DocType JSON schema change (two new
  fields) and therefore requires a migration on any site where it is
  deployed.
- The settings loader's expectations must be updated to include the two new
  fields, with safe fallback defaults if the Single record has never been
  saved with them populated.

## Constraints

- Synthetic data only: `P0000000`, `1990-01-01`, `203.0.113.x` range.
- Do not push to any Git remote.
- Site `visaguy` is the owner's live development bench and must **not** be
  used for this testing. Use a dedicated test site,
  `visa-tracker-test.localhost`.

## Validation

- **Regression test (the one that matters most):** the same passport with an
  incrementing DOB must now lock out on the 21st attempt, where today it never
  locks out (proven empirically at 0/7). This is the exact case that proved
  the defect.
- **Existing behaviour preserved:** an identical wrong pair still locks out at
  attempt 6 (unchanged 5/15 semantics).
- The scope key genuinely excludes the target bucket: varying the DOB across
  calls yields the same scope key for a fixed origin/IP.
- The two counters use independent, non-colliding cache keys.
- `Retry-After` reflects the greater of the two remaining lockout values when
  both counters are active.
- Settings clamping at both MIN and MAX bounds for
  `scope_maximum_failed_attempts` and `scope_lockout_minutes`, and safe
  defaults (20 / 60) when the `Visa Tracker Settings` Single is empty or
  unconfigured.
- **Live-HTTP proof is required, not just the in-process suite.** This defect
  was invisible to a fully green 248-test in-process suite and was only ever
  caught over real HTTP against real Redis. Reproduce that discipline here:
  run a loopback werkzeug server plus `curl` with an explicit
  `Host: visa-tracker-test.localhost` header, mirroring what phase 09j did.
  See `ongoing/visa-tracking-implementation/09j-live-wire-contract-smoke.md`,
  Appendix C, for the original write-up of this finding and the method used
  to catch it.

## Definition of done

- Both counters implemented, consulted, and independently keyed as specified
  above.
- New settings fields present, clamped, migrated, and defaulted safely.
- All validation items above pass, including the live-HTTP reproduction.
- Risk 18 in `docs/risks-and-open-questions.md` updated to reflect the fix
  only after runtime proof lands — not as part of this task's own edits.

## Evidence

Full write-up: `ongoing/visa-tracking-implementation/09j-live-wire-contract-smoke.md`,
Appendix C.

## Completion evidence (2026-09-01)

**Status is `in-progress`, not `completed`. The fix is implemented and
runtime-proven on the test site, but it is uncommitted in `the_visaguy` and
not deployed to `visaguy`.** Risk 18 is updated to reflect the fix but stays
open per this task's own "Severity" section, which requires the live-HTTP
validation to actually pass before the risk closes — that validation has now
passed, but only on the test site, and the vulnerable code is still what runs
on `visaguy`.

### What is done, exactly as specified

- `build_client_scope_key(origin_scope, source_ip)` added to
  `visa_tracking/services/rate_limit_service.py`, same keyed-HMAC bucket
  construction as `build_client_key` but without the target-bucket component,
  under its own cache-key prefix (`visa_tracker:failed_scope:`, distinct from
  the existing `visa_tracker:failed:`).
- Two new `Visa Tracker Settings` Int fields, `scope_maximum_failed_attempts`
  (default 20) and `scope_lockout_minutes` (default 60), added to
  `the_visa_guy/doctype/visa_tracker_settings/visa_tracker_settings.json`,
  clamped MIN/MAX the same way as the existing per-identity fields, with
  constants in `visa_tracking/utils/constants.py` so an unconfigured Single
  fails safe.
- `verification.py` now consults both counters, refuses the request when
  either has tripped, sets `Retry-After` to the greater of the two remaining
  values, and increments both only in the `not_found` branch (not on CORS
  rejection, malformed body, or the feature-disabled path).
- The generic failure response body is confirmed byte-identical (md5) across
  every reachable failure mode.

### Runtime proof (test site only)

Live-HTTP proof over real HTTP against real Redis (werkzeug on a loopback
port, `curl` with explicit `Host: visa-tracker-test.localhost` header),
mirroring the method of `09j-live-wire-contract-smoke.md` Appendix C:

- The exact regression this task exists to fix: the same passport with an
  incrementing DOB, previously 0/7 (never locked out), now returns
  `Retry-After: 3597` at attempt 21.
- Existing per-identity behaviour is unchanged: an identical wrong pair still
  locks out at attempt 6 with `Retry-After: 900`.
- Response body md5 identical across `not_found`, both rate-limited paths, and
  CORS rejection.
- Suite: **298 green** on `visa-tracker-test.localhost` (up from 276 green
  after TASK-011's own suite run — see the session report referenced below for
  the full day's progression).

### A real secondary bug found and fixed during this work

Adding an `Int` column to an **already-installed** Single DocType means the
new column reads back as `0`, not `None`, on a record saved before the column
existed. The pre-existing guard in `validate_public_tracking_bounds`
(`if value is None: continue`) therefore let `0` reach the bound check for the
two new fields, throwing "must be between 1 and 100" on **every** save of
`Visa Tracker Settings` and breaking 14 unrelated tests. Fixed by treating
falsy as "unset -> use default" for `scope_maximum_failed_attempts` and
`scope_lockout_minutes` only; every pre-existing field keeps its strict
`is None` semantics. Since both new bounds start at 1, `0` was never a legal
configured value, so nothing was loosened by this change. Worth recording
because the same failure mode will recur on the next Int field added to this
Single.

### What remains, in order

1. **Commit** the implementation in `the_visaguy` on `feat/visa-tracker`
   (currently uncommitted on top of local HEAD `4192e36`).
2. **Deploy to `visaguy`**, including the settings-schema migration for the
   two new fields, per the deploy procedure in
   `docs/operations/visa-tracking-runbook.md`.
3. **Only then** close risk 18 — its own text requires the live-HTTP
   validation to be run and pass on the environment that matters, and today's
   validation was deliberately run on the test site per this task's own
   constraint ("Site `visaguy` ... must not be used for this testing").
   Runtime-verified-on-test-site is not the same claim as fixed-in-reality;
   see `docs/risks-and-open-questions.md` risk 18 for the precise wording.

Full session narrative: `ongoing/visa-tracking-implementation/12-session-2026-09-01-task-011-012.md`.

### Update (2026-09-13)

Step 1 is done: `the_visaguy` `53b0f28` ("feat(TASK-012): constrain
credential enumeration in public verification"), and the branch equals
`upstream/feat/visa-tracker` as of the last fetch. Steps 2 and 3 remain.
