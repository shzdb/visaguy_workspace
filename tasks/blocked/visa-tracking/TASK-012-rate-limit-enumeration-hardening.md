---
id: TASK-012
feature: FEAT-001
title: Constrain credential enumeration in public verification rate limiting
status: blocked
repository: the_visaguy
owners: []
depends_on:
  - ADR-005
  - TASK-007
blocked_by: product sign-off on per-IP and per-origin thresholds
created: 2026-07-23
updated: 2026-07-23
---

# TASK-012: Constrain credential enumeration in public verification rate limiting

## Blocker

Requires a **product decision** on thresholds before implementation. Per
`.agents/rules/project-rules.md`, a task carrying an unresolved product decision
must not be marked `ready`. See "Decisions required" below.

## Severity

Medium-high, and **live**. Public tracking is enabled on `visaguy`, so this is
currently reachable rather than theoretical. Recorded as risk 18.

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

**Do not "fix" this by removing the per-identity bucket.** That bucket is
deliberate: it prevents an attacker locking a legitimate applicant out of their
own record by repeatedly failing against their credentials.

Add a **complementary coarser counter** evaluated alongside the existing one:

1. A per-IP failure counter with a higher threshold and its own window.
2. Optionally a per-origin counter.
3. Both evaluated in addition to, not instead of, the per-identity bucket.
4. Preserve the constant generic response — the new limit must not become an
   oracle that reveals whether throttling applied.

## Decisions required before implementation

1. Per-IP failure threshold and window.
2. Whether a per-origin counter is also required.
3. Behaviour behind shared egress IPs (offices, mobile carriers, NAT), where a
   per-IP counter can lock out legitimate applicants — the same failure mode the
   per-identity bucket exists to avoid.
4. Whether ADR-005 needs amending, or this is an implementation detail beneath it.

## Validation

- A regression test asserting the **varying-DOB** case now locks out. This is
  the specific case the existing suite could not see.
- The identical-pair lockout must continue to work unchanged.
- Re-run the live HTTP probe with synthetic data (`P0000000`, `203.0.113.x`),
  not only in-process tests — an in-process test is what missed this originally.

## Evidence

Full write-up: `ongoing/visa-tracking-implementation/09j-live-wire-contract-smoke.md`,
Appendix C.
