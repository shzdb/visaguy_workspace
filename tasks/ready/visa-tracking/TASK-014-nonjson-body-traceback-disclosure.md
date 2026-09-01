---
id: TASK-014
feature: FEAT-001
title: Investigate and close raw-traceback disclosure on non-JSON body to public verify_identity
status: ready
repository: the_visaguy
owners: []
depends_on:
  - ADR-005
  - TASK-007
created: 2026-09-01
updated: 2026-09-01
---

# TASK-014: Investigate and close raw-traceback disclosure on non-JSON body to public verify_identity

## Objective

Close an information-disclosure gap on the public, unauthenticated
`verify_identity` endpoint: a request with a genuinely non-JSON body currently
returns a raw traceback page instead of the feature's generic, byte-identical
failure response.

## Context

Found 2026-09-01 during TASK-012's live-HTTP testing, while probing the
`verify_identity` endpoint's constant-response property with a range of
malformed inputs. **This is not caused by, or specific to, the rate-limiting
work in TASK-012** — it is a pre-existing behaviour, uncovered by that
session's unusually thorough live-HTTP probing rather than introduced by it.

Two cases were compared:

- A **valid-JSON-but-wrong-shape** body, e.g. `[]`, is handled correctly: it
  reaches the application's own `UnsafeRequestError` path in
  `visa_tracking/api/verification.py` and returns the byte-identical generic
  failure body that every other rejection path returns. This is the intended,
  designed behaviour and requires no change.
- A **genuinely non-JSON** body (malformed/unparseable as JSON at all) never
  reaches the app's handler. Frappe's own request-dict construction
  (`make_form_dict`, in Frappe core, not in this application) parses the body
  **before** dispatching to the whitelisted method, and raises there on
  malformed input. Because the failure happens before the app's code runs,
  none of `verification.py`'s generic-failure handling applies, and the
  response is a raw traceback page — on a public, unauthenticated endpoint.

**Be honest about where the defect lives:** this is in Frappe core's request
handling, not in `verification.py` or any other FEAT-001 application code.
The likely fix therefore is not a change to the whitelisted method itself —
by the time that method runs, the damage (the traceback response) has
already happened. Plausible directions, none yet evaluated in depth:

- Intercept earlier, e.g. a custom pre-parsing hook or middleware that
  validates/catches malformed bodies before Frappe's own dict construction
  raises.
- Handle it at the web-server layer (nginx/gunicorn/werkzeug config) by
  catching the resulting error class and mapping it to a generic response
  before it reaches the client.
- Check whether Frappe itself exposes a configuration point or version fix
  for this (worth checking upstream Frappe issues/changelog before building
  a local workaround).

This task is investigation-first: the right approach is not yet known and
needs to be determined before implementation.

## Inputs

- `visa_tracking/api/verification.py` — the app's own `UnsafeRequestError`
  path, for contrast with the case that already works correctly.
- Frappe core's request dispatch path (`frappe/app.py`,
  `frappe/utils/data.py` or wherever `make_form_dict` lives in the installed
  Frappe version) — read this before proposing a fix location.
- ADR-005 — the generic-failure / constant-response design this gap violates.
- `docs/risks-and-open-questions.md` risk 24 — the risk-register entry for
  this finding.

## Required behaviour

- A genuinely non-JSON request body to `verify_identity` (and ideally the
  other public endpoints sharing the same request-parsing path) must return
  the same generic, byte-identical failure response the feature already uses
  for every other failure mode — not a traceback, and not any response that
  differs in body content from the established constant response.
- No stack trace, file path, or internal exception detail may reach a public,
  unauthenticated client under any input.
- The fix must not weaken or alter the already-correct handling of
  valid-JSON-but-wrong-shape bodies.

## Constraints

- Synthetic data only in testing: `P0000000`, `1990-01-01`, `203.0.113.x`
  range.
- Test on `visa-tracker-test.localhost`, not `visaguy`.
- Do not push to any Git remote.
- This is genuinely an investigation task: do not commit to an implementation
  approach (middleware vs. web-server-layer vs. upstream fix) until the
  options above have been evaluated against how the installed Frappe version
  actually structures request parsing.

## Expected changes

- A determination of where the fix belongs (with evidence, not guesswork).
- Implementation of the chosen fix.
- A regression test proving the non-JSON case now returns the generic body,
  proven to fail without the fix (mutation-proven, per this feature's
  standing testing discipline).
- Live-HTTP reproduction of the fix, mirroring the method in
  `ongoing/visa-tracking-implementation/09j-live-wire-contract-smoke.md`.

## Validation

- A non-JSON body to `verify_identity` returns the byte-identical generic
  failure body (md5-compared against the existing failure modes), not a
  traceback.
- The valid-JSON-but-wrong-shape (`[]`) case still returns the same generic
  body via the existing `UnsafeRequestError` path, unchanged.
- No stack trace or internal detail appears in the response under any tested
  malformed-input variant.

## Definition of done

- Root cause and fix location determined and documented.
- Fix implemented and mutation-proven.
- Live-HTTP proof recorded.
- Risk 24 in `docs/risks-and-open-questions.md` updated once the fix is
  runtime-verified.
