# ADR-008: CORS Header Emission Delegated to Frappe

## Status

Accepted

Narrows ADR-005 ("Wildcard or overly permissive CORS is prohibited"). ADR-005
otherwise remains in force.

## Context

The public tracking endpoints returned a **duplicated**
`Access-Control-Allow-Origin` header. Two layers set it independently:

- `visa_tracking/services/response_service.to_http_response` set it for an
  already-validated origin;
- Frappe sets it in `frappe/app.py:299` via `response.headers.extend(...)`
  whenever `allow_cors` is configured — and `extend` **appends** rather than
  replaces.

Site `visaguy` has `allow_cors: "*"` in `site_config.json`, serving the other
VisaGuy frontends. Browsers reject a response carrying two
`Access-Control-Allow-Origin` headers even when both values are identical and
correct, so the local frontend could not call the API. `curl` does not enforce
this, which is why the endpoint appeared healthy from the terminal — the
preflight was always clean, and only the actual request failed in a browser.

Removing the app's origin validation entirely was proposed. It was not adopted:
the header duplication was the whole defect, and dropping the gate is a separate
security change that interacts badly with the unresolved rate-limit finding
(see risk 18) by widening who can drive enumeration from real users' browsers.

## Decision

- `to_http_response` **no longer sets CORS headers.** Frappe is the single
  emitter.
- **Origin authorisation is retained in the API layer.** `verification.py` and
  `status.py` call `security.validate_cors(origin)` and return the constant
  generic failure for a non-approved origin before doing any work. The control
  moved from the response header to the request path; it was not removed.
- `Visa Tracker Settings.frontend_base_url` remains the single approved origin
  and continues to govern that check.
- The wildcard is therefore **transport-level only**: any origin may receive a
  response, but only the approved origin receives a functional one.

## Consequences

### Positive

- Browsers accept the response; the local frontend works against the remote
  bench.
- One emitter means the bug cannot recur from the app side.
- The strict-origin control survives, in the layer where it is actually
  enforceable.

### Negative

- The emitted header is now `*`-derived rather than an explicit allowlist, which
  is weaker than ADR-005's literal wording.
- The app's behaviour now depends on site configuration it does not own: if
  `allow_cors` were removed from `site_config.json`, **no** CORS header would be
  emitted and every browser client would break. This coupling is invisible from
  the application code.

### Honest limitation

`Origin` is set by browsers and trivially forged by any script, so this check
was never a meaningful control against a determined attacker. These endpoints
use a bearer token in the JSON body rather than cookies, so CSRF does not apply
either. Its real value is limiting casual browser-based abuse and embedding —
worth keeping, not worth over-claiming.

## Revisit when

`allow_cors` changes on any site serving the tracker, additional frontends need
access (the single `frontend_base_url` does not model multiple environments), or
the rate-limit enumeration finding is closed and the gate's blast-radius role
can be re-evaluated.
