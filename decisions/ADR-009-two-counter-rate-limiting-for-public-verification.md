# ADR-009: Two-Counter Rate Limiting for Public Verification

## Status

Accepted

Supersedes the rate-limiting portion of ADR-005's "Abuse controls" section
only (the per-identity failure counter and its suggested 5/15 thresholds).
ADR-005 otherwise remains in force, including its HMAC lookup, opaque
session, generic-failure, CORS, and masking sections.

## Context

`verification.py` scopes its failure counter to
`build_client_key(origin_scope, source_ip, target_bucket)`, where
`target_bucket = candidates[0][0]` is the passport+DOB lookup hash itself.
That is an exact-credential-pair counter: it does exactly what ADR-005 asked
for (a legitimate applicant who mistypes their own DOB a few times is
throttled against their own record) but nothing else, because varying the DOB
produces a fresh counter on every attempt.

Proven empirically over real HTTP against real Redis (risk 18;
`ongoing/visa-tracking-implementation/09j-live-wire-contract-smoke.md`,
Appendix C): 7x an identical wrong pair locks out at attempt 6
(`Retry-After: 900`) — the existing control works as designed — but 7x the
same passport number with an incrementing DOB never locks out (0/7). An
attacker who knows a passport number can enumerate DOBs (roughly 36,500
candidates for an adult) from a single IP, unthrottled, and every failure
returns a byte-identical HTTP 200, so there is no client-visible signal that
throttling is absent. This is recorded as risk 18.

The owner reviewed this on 2026-09-01 and decided the fix: add a
complementary, coarser per-IP counter alongside the existing per-identity one,
rather than replacing it.

## Decision

### Two independent counters, both consulted

1. **Per-identity** (existing, unchanged): keyed on
   `(origin_scope, source_ip, target_bucket)` where `target_bucket` is the
   passport+DOB lookup hash. Threshold **5 failed attempts**, **15-minute**
   lockout. Cache prefix `visa_tracker:failed:`.
2. **Per-IP scope** (new): keyed on `(origin_scope, source_ip)` only — the
   same construction, with the target bucket omitted, via
   `build_client_scope_key`. Threshold **20 failed attempts per IP per
   hour**, **60-minute** lockout. Its own distinct cache prefix,
   `visa_tracker:failed_scope:`, so it can never collide with the
   per-identity key.

Both counters use the same fixed-window semantics already established by the
per-identity counter (TTL set on first failure, preserved across increments —
a deliberate documented choice, not a sliding window). A request is refused
when **either** counter has tripped; `Retry-After` is the greater of the two
remaining values. Only a genuine `not_found` result increments either
counter — CORS rejections, malformed bodies, and the feature-disabled path do
not, so a malformed-request flood cannot itself lock out a shared IP.

### Thresholds and the owner's rationale

20 failed attempts per IP per hour cuts DOB enumeration from roughly 36,500
candidates to roughly 480 per day from a single IP — killing it as a
practical attack — while leaving headroom for a shared office, hotel, travel
agency, or mobile-carrier NAT, where several genuine applicants may
legitimately check status from one address within the same hour. A tighter
threshold would more aggressively suppress enumeration but would start
throttling exactly that shared-NAT population; 20/hour was chosen as the
point that stops the attack without materially affecting real users behind
common NAT scenarios.

### Why the per-identity counter is deliberately kept, not replaced

The per-identity counter is not redundant with the new per-IP one. It exists
to prevent a different attack: an attacker who knows (or guesses) a specific
applicant's passport+DOB pair could otherwise repeatedly submit it wrong on
purpose to lock that applicant out of checking their own status, without
needing to enumerate anything. A pure per-IP counter would not catch this,
because a single attacker only needs one failing pair, not many, to grief one
victim. Both counters stay in force, independently keyed, evaluated together.

## Consequences

### Positive

- Closes the practical DOB-enumeration path described in risk 18 without
  weakening the existing per-identity protection.
- Shared-NAT users get meaningful headroom (20/hour, not 5/hour) before being
  throttled by the new counter.
- The generic-failure, byte-identical-response property from ADR-005 is
  preserved; only the `Retry-After` header varies across failure modes.

### Negative

- **Shared-NAT trade-off.** A genuinely malicious actor sharing an IP with
  many legitimate applicants (a large office, a call center, a busy travel
  agency) can still exhaust the 20/hour budget faster than a lone user would,
  degrading service for everyone behind that IP for up to 60 minutes. This is
  an accepted cost of the chosen threshold, not an oversight.
- Redis now carries a second counter family per abusive client, doubling the
  abuse-tracking key volume during an active attack.
- Adding the two settings fields to an already-installed `Visa Tracker
  Settings` Single required a schema migration and surfaced a real Frappe
  behaviour (a newly added `Int` field on an existing Single record reads
  back as `0`, not `None`); this is now handled explicitly but is a
  configuration-migration hazard worth remembering for any future field added
  to this Single.

### Honest limitation

An attacker who can originate requests from many distinct IPs — a botnet, a
proxy pool, a large NAT-diverse network — is only **linearly** constrained by
this fix: each IP still gets its own 20/hour (480/day) budget, so N
distributed IPs yield roughly N times that enumeration rate. This ADR does
not add a per-origin or global counter, and no per-origin counter was
requested by the owner. Distributed enumeration remains possible; it is
merely made expensive and slow rather than free, and it no longer works from
a single IP with an unbounded budget.

## Alternatives considered

- **Replace the per-identity counter with the per-IP one.** Rejected: it
  would remove the control that stops an attacker from locking a legitimate
  applicant out of their own record.
- **A single merged counter keyed on IP only.** Rejected for the same reason
  as above, and because it would conflate two different threat models (credential
  guessing against one victim vs. enumeration across many candidates) into one
  threshold that cannot serve both well.
- **A per-origin counter in addition to per-IP.** Not requested by the owner;
  out of scope for this decision. `frontend_base_url` already restricts which
  origins receive a functional response (ADR-008), which is a coarser and
  differently-shaped control.
- **A sliding-window counter instead of fixed-window.** Rejected as
  unnecessary additional complexity; the existing per-identity counter's
  fixed-window choice is already documented and accepted, and consistency
  between the two counters was preferred.

## Revisit when

Distributed (multi-IP) enumeration is observed in practice, the shared-NAT
threshold proves too tight or too loose against real traffic, or a per-origin
control is separately requested.
