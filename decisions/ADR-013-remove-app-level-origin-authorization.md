# ADR-013: The Public API Does Not Authorize on the Origin Header

## Status

Accepted (2026-09-03)

Supersedes the origin-authorization half of ADR-005's "CORS restriction"
subsection. Extends ADR-008, which had already delegated CORS *header
emission* to Frappe; this ADR removes the remaining *authorization* use of
the Origin header. ADR-005 otherwise remains in force in full, including
rate limiting, passport-number masking, opaque session tokens, the generic
failure shape, and the API access boundary.

## Context

ADR-005 required public endpoints to "restrict allowed origins to the
approved frontend base URL". That was implemented as
`security.validate_cors`, called first in `verify_identity`,
`get_tracking_status`, and `logout`: a request whose `Origin` header was
missing or did not match `Visa Tracker Settings.frontend_base_url` returned
the generic failure before any other work.

Two things were wrong with it.

**It was not CORS.** CORS is enforced by the browser, using response headers
the server emits. ADR-008 already established that Frappe is the sole emitter
of those headers on this deployment. What `validate_cors` added was a
server-side authorization gate that happened to read the same header.

**It did not protect anything.** The `Origin` header is set by the browser
for browser callers, and is freely chosen by everyone else. An attacker
using curl or any HTTP library simply sends the approved value. The gate
therefore stopped exactly the callers who were being honest about not being
a browser — including the project's own direct API testing — while a
scripted attacker passed through untouched.

The failure that surfaced this: a direct `POST` to
`verify_identity` with valid credentials returned
`"Unable to verify. Please check your details and try again."` The request
carried no `Origin` header, so it was rejected at step 1 and never reached a
lookup. Because every failure mode returns the same constant body by design,
the response was indistinguishable from wrong credentials.

## Decision

The public tracking API does not make authorization decisions based on the
`Origin` header.

- `security.validate_cors`, `get_approved_origin` and `_is_localhost_origin`
  are removed, along with the constants and imports they alone used.
- `get_request_origin` remains. The header is recorded as audit context and
  feeds `get_origin_scope` for rate-limit bucketing, but never gates a
  request.
- CORS headers remain entirely Frappe's responsibility per ADR-008, via
  `allow_cors` in `site_config.json`.
- `Visa Tracker Settings.frontend_base_url` is no longer read by the security
  layer. It keeps whatever other uses it has; it is simply not an
  authorization input.

## Consequences

**A caller sending no `Origin` is served normally.** This is the point of the
change: direct API calls, server-to-server integrations, and testing all work
without pretending to be a browser.

**Cross-origin browser access is governed solely by `allow_cors`.** On
`visaguy` that value is `"*"`, so any web page can now call these endpoints
from a browser. Previously the app-level gate would have refused such a
request even though Frappe's headers permitted it. Anyone who wants that
restriction back should configure `allow_cors` to a specific origin — the
control belongs there, where the browser actually enforces it, not in an
application-level check on a forgeable header.

**The remaining protections are unchanged and carry the weight**: verification
requires a correct passport number *and* date of birth; the two-counter rate
limiter (ADR-009) bounds enumeration; sessions are opaque tokens; every
failure returns one constant generic body; and responses expose only masked,
allowlisted fields.

**Rate-limit bucketing is coarser for non-browser callers.** `get_origin_scope`
returns an empty scope when no `Origin` is present, so those requests share a
bucket per source IP rather than per (origin, IP). The IP component still
applies, and the per-identity counter is unaffected.

## Alternatives considered

**Keep the gate but allow an empty `Origin`.** This is the smallest change
and it would have fixed the reported failure, but it makes the control
incoherent: it would reject a forged non-approved origin while accepting the
absence of one, so any caller wanting through would simply omit the header.
A control that is bypassed by sending less information is not a control.

**Require a shared secret or API key for non-browser callers.** A real
control, and a reasonable future step if server-to-server access needs
authentication. It is a different decision from this one, which is about not
mistaking a forgeable browser hint for authorization; introducing an
authentication scheme was out of scope.
