---
id: TASK-009
feature: FEAT-001
title: Tracker verification form, status view, timeline, and error states
status: blocked
repository: visa_tracker
owners: []
depends_on:
  - TASK-008
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Tracker verification form, status view, timeline, and error states

## Objective

Implement the public tracking flow in the `visa_tracker` SPA: passport and DOB verification, current status, status timeline, and error handling.

## Blocked by

**TASK-008.** The SPA does not exist yet. This task cannot start until the scaffold and design parity are in place.

## Inputs

- The verification and status endpoints delivered by TASK-007 (`the_visaguy.visa_tracking.api.verification`, `.api.status`).
- The approved public information boundary.

## Required behaviour

- A React Hook Form + Zod verification form taking passport number and date of birth.
- Exchange of a successful verification for the short-lived opaque session token.
- Display of masked applicant name, masked passport number, destination and visa type when approved, current public status, configured public message, last-updated timestamp, and the public status timeline.
- A single generic error state for every failed verification — the UI must not distinguish "wrong passport" from "wrong DOB" from "not found".
- Explicit handling of rate-limited and locked-out responses.
- Loading and empty states consistent with the consumer website treatment.

## Constraints

- Passport number and DOB must never appear in a URL, query string, `localStorage`, `sessionStorage`, analytics payload, or console output.
- The session token is opaque and short-lived; do not persist it beyond the session.
- Render only fields inside the approved public boundary, even if the API were to return more.

## Validation

- Manual walkthrough of a successful verification against the test site.
- Manual walkthrough of invalid input, rate limiting, and lockout.
- Browser devtools inspection confirming no sensitive value in storage, network URLs, or logs.

## Definition of done

The full public flow works end to end against a real backend, with no PII leakage observable in the browser.
