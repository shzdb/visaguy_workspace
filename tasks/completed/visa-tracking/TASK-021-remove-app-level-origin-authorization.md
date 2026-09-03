---
id: TASK-021
feature: FEAT-001
title: Remove the app-level origin authorization gate from the public API
status: completed
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-013
created: 2026-09-03
updated: 2026-09-03
---

# TASK-021: Remove the app-level origin authorization gate

## Objective

Stop treating the `Origin` header as an authorization input on the public
tracking API. See ADR-013 for the decision and its consequences.

## Context

Owner decision, 2026-09-03: CORS is Frappe's concern via `allow_cors`, and
ADR-008 had already made Frappe the sole emitter of CORS headers. What
remained in the app was an authorization gate on a forgeable header — it
blocked honest non-browser callers, including direct API testing, while a
scripted attacker need only send the approved value.

Surfaced while diagnosing TASK-020: a direct `POST` to `verify_identity`
was rejected at step 1 for having no `Origin` header, and because every
failure returns the same constant body, the result was indistinguishable
from wrong credentials.

## Changes

- `visa_tracking/utils/security.py` — removed `validate_cors`,
  `get_approved_origin`, `_is_localhost_origin`, and the constants and
  imports used only by them (`_WILDCARD_ORIGINS`, `_LOCALHOST_HOSTNAMES`,
  `DEV_CORS_ALLOW_LOCALHOST_CONFIG_KEY`, `get_visa_tracker_settings`).
  `get_request_origin` and `get_origin_scope` remain.
- `visa_tracking/api/verification.py` — gate removed, step numbering
  corrected, module docstring records the decision.
- `visa_tracking/api/status.py` — gate removed from `_request_context`,
  `get_tracking_status`, and `logout`.
- `visa_tracking/services/response_service.py` — corrected the comment that
  claimed origin authorization was still enforced in the API layer.
- `visa_tracking/tests/test_public_api.py` — removed the four gate-rejection
  tests; kept the assertion that no `Access-Control-Allow-Origin` is emitted
  (ADR-008); added `test_request_without_origin_header_succeeds` and
  `test_wildcard_origin_is_no_longer_rejected`.
- `visa_tracking/tests/test_security_utils.py` — removed `TestValidateCors`,
  its base class, and the site-bound CORS integration class.

`DEV_CORS_ALLOW_LOCALHOST_CONFIG_KEY` still exists in `utils/constants.py`
and is now unreferenced; the site-config key
`visa_tracker_allow_localhost_origins` it named no longer does anything.

## Validation

- Full `visa_tracking` discovery: 268 tests, 2 errors, both pre-existing in
  `TestProcessFileHandler` and unrelated (verified against the pristine
  source).
- `test_public_api.py` alone: 36 tests, 2 skipped, pass.
- Grep confirms no remaining references to the removed functions outside
  `constants.py`.

## Completion evidence

- `the_visaguy` `1a7af2e` on `feat/visa-tracker`, committed locally, not
  pushed or deployed.

## Follow-up worth considering

`visaguy` has `allow_cors: "*"` in `site_config.json` (recorded in ADR-008),
so with the gate gone any web page can call these endpoints from a browser.
If that is not wanted, set `allow_cors` to the specific frontend origin —
that is where the browser actually enforces it. This is a deployment
configuration decision, not a code change, and was not made as part of this
task.
