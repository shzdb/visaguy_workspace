# ADR-011: Public Lookup Hash Is Unkeyed

## Status

Accepted

Narrows ADR-005's "HMAC lookup" subsection only. ADR-005 otherwise remains
in force, including its opaque-session, generic-failure, abuse-control,
CORS, masking, and API-access-boundary sections.

## Context

`verification_lookup_hash` was originally specified (ADR-005) and built as
HMAC-SHA256 over a canonical passport-number + date-of-birth input, keyed by
server-side configuration (`visa_tracker_lookup_hmac_key`). The stated
reason was that passport number and DOB have low input entropy, so an
unkeyed hash would be vulnerable to offline brute-forcing if the hash column
were ever exposed (e.g. a database leak).

**That threat model was wrong, and the error is corrected here.** `Passport
Extraction` already stores, in the same database, in plaintext:
`passport_number`, `passport_number_normalized`, `date_of_birth`, `surname`,
`given_names`, `mrz_line_1`, and `mrz_line_2`, plus a pointer to the
underlying passport file. Anyone in a position to read the
`verification_lookup_hash` column off a leaked `Visa Tracking Application`
table is, by construction of the same leak, in a position to read the
plaintext passport number and DOB off `Passport Extraction` directly — no
brute-forcing of the hash is needed or adds any resistance. The HMAC key
never protected against a database leak. Earlier documentation (ADR-005's
"HMAC lookup" subsection, and the corresponding passages in
`features/ongoing/visa-tracking/README.md` and
`features/ongoing/visa-tracking/01-architecture-and-data-model.md`) implied
otherwise; that implication was incorrect and should be read in light of
this ADR wherever it appears.

What the key did buy, genuinely: `Visa Tracking Application` is readable by
more people than `Passport Extraction`, whose raw fields sit behind
permlevel 1. Keeping `verification_lookup_hash` non-reversible to a raw
passport number meant a wider audience with access to `Visa Tracking
Application` still could not recover the passport number from the hash
alone. That property does not depend on the hash being *keyed* — it depends
on the hash being a one-way function at all, which an unkeyed SHA-256 over
the same canonical input still is.

What the key cost, recurring and operational: `visa_tracker_lookup_hmac_key`
had to be configured on every site **before** any tracking application was
created there. When it was missing, `verification_lookup_hash` was never
computed, `tracking_enabled` was forced to `0`, and the resulting
application could never be looked up publicly — silently, with no error and
no log. This is exactly the failure mode that broke `VTA-2026-00575` in
practice, and the same gap that risk 22 and the runbook's "Required
server-side configuration" section previously warned every deploy and
rebuild about.

The owner reviewed this on 2026-09-03 and decided: since the secret bought
no resistance to the leak scenario it was justified by, and did buy a
recurring, silently-failing operational cost, drop the key requirement for
the lookup hash.

## Decision

- `verification_lookup_hash` is now an **unkeyed** hash (SHA-256) over the
  same canonical passport-number + date-of-birth input previously used for
  the HMAC. The input canonicalisation is unchanged; only the presence of a
  key is removed.
- `visa_tracker_lookup_hmac_key` is **no longer required for the public
  lookup** and no longer needs to be configured on any site before creating
  tracking applications there. `Visa Tracker Settings` and the lifecycle
  service no longer gate `tracking_enabled` on this key's presence.
- The one-way property is retained: the public lookup still cannot be
  reversed to a raw passport number from the stored hash alone, preserving
  the genuine benefit described above (no second plaintext copy of the
  passport number on the more widely readable `Visa Tracking Application`).
- **A migration patch**, `the_visaguy/patches/recompute_lookup_hash_unkeyed.py`
  (registered in `patches.txt`), recomputes `verification_lookup_hash` for
  every existing `Visa Tracking Application` from its linked `Passport
  Extraction`. It handles both rows written under the old keyed scheme and
  rows left with a NULL hash by a previously-missing key (the
  `VTA-2026-00575`-style failure). The patch is idempotent, and any row with
  no resolvable linked extraction is counted and skipped rather than guessed
  at or left to error.

### What is unaffected

`visa_tracker_lookup_hmac_key` is still consulted by two other, unrelated
consumers, both already tolerant of its absence and unchanged by this
decision:

- `rate_limit_service`, for cache-key bucketing.
- The audit path, for hashing client IPs before they are written to `Visa
  Tracker Audit Log`.

Both already fell back to a default when the key was absent before this
change; that fallback behaviour is unchanged. Removing a previously-present
key from a site does change the derived bucketing/hash values these two
consumers produce going forward — this harmlessly resets in-flight
rate-limit counters (they simply start over under the new derived key) and
means any audit rows written under the old value are no longer matched by a
teardown/cleanup filter keyed on the old derived value. Neither consequence
affects correctness of the public lookup or of rate limiting itself.

## Runtime proof

With `visa_tracker_lookup_hmac_key` removed entirely from
`site_config.json`, the full verify -> status round trip (`verify_identity`
-> session token -> status lookup) passes end to end. Committed in
`the_visaguy` on `feat/visa-tracker` as `219907d`; full suite 358/358.

## Consequences

### Positive

- Removes a recurring, silently-failing per-site prerequisite. A site can
  have tracking applications created on it without anyone having first
  generated and configured a secret — closing the exact class of failure
  that produced the `VTA-2026-00575` incident.
- The recompute patch also repairs pre-existing NULL-hash rows from that
  same failure mode, not only rows migrating off the old keyed scheme.
- The genuine benefit of the original design — no second plaintext passport
  number on the more widely readable `Visa Tracking Application` — is fully
  retained.
- Simplifies the "Required server-side configuration" surface for every
  future site rebuild and rollout (see the corresponding runbook and
  rollout-plan corrections made alongside this ADR).

### Negative

- The honest security property of `verification_lookup_hash` was always
  "opaque, one-way identifier," never "resistant to a targeted attacker who
  already has database access" — moving to unkeyed makes that property no
  weaker in practice than it already was, but it is a smaller, more
  defensible claim than ADR-005 originally implied, and anyone who
  internalised the original (incorrect) "protects against a DB leak" framing
  needs to update that understanding.
- `lookup_hash_version` (present in the data model since ADR-005) is the
  seam that distinguishes old keyed-scheme rows from new unkeyed rows during
  and after migration; any future change to the lookup hash's construction
  should continue to use it rather than relying on implicit row age.

## Alternatives considered

- **Keep the HMAC key, fix only the silent-failure behaviour** (e.g. fail
  loudly at site setup, or refuse to create a tracking application with a
  clear error instead of a forced `tracking_enabled = 0`). Rejected: this
  would have removed the silent-failure symptom while leaving the
  underlying cost (a secret that must be generated and configured on every
  site before first use, for no real security benefit against the leak
  scenario) fully in place.
- **Move the key into `Visa Tracker Settings` instead of `site_config.json`**
  to make it configurable without shell access. Not adopted: it does not
  address the root issue (the key defends nothing that plaintext
  `Passport Extraction` does not already expose under the same leak) and
  would have moved a secret into a DocType, which
  `01-architecture-and-data-model.md` already prohibits for HMAC keys.

## Revisit when

A future design genuinely separates the trust boundary between `Passport
Extraction` and `Visa Tracking Application` (for example, if raw passport
fields are ever removed from `Passport Extraction` or moved further behind
permission boundaries such that they are no longer effectively co-exposed
with `verification_lookup_hash` in a leak scenario) — at that point a keyed
scheme would again buy real resistance and should be reconsidered.
