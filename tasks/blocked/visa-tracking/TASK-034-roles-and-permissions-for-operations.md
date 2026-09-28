---
id: TASK-034
feature: FEAT-001
title: Roles and permissions for operations users
status: blocked
repository: the_visaguy
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - TASK-027
expected_files:
  - the_visaguy/fixtures/custom_docperm.json
created: 2026-09-28
updated: 2026-09-28
---

# TASK-034: Roles and permissions for operations users

## Blocked on

Owner decisions D2 and D3 in
`features/ongoing/visa-tracking/07-soft-launch-plan.md`.

## Objective

Let the people who work on Process Files open the tracking records the form
links to, and let the chosen reviewers verify passports.

## Context (site `visaguy`, 2026-09-28, runtime-verified)

- Permission on `Visa Tracking Application`, `Visa Tracking Status`,
  `Visa Tracking Status Log` and `Visa Tracker Settings` is given only to
  `Visa Tracker Manager` and `Visa Tracker Operator`. **No user on
  `visaguy` holds either role.**
- 107 users hold `Operations Associate` and 36 hold `Operations Team Lead`.
  They have no permission on any of these DocTypes. So:
  - clicking the Process File's tracking link gives a permission error;
  - the `custom_client_status` picker (TASK-027) cannot search statuses,
    so the manual status change cannot be used.
- `Passport Extraction` gives access to `Passport Extractor User` and
  `System Manager` only. `passport_extractor` is not installed on
  `visaguy` yet.

## Required behaviour (proposed; confirm with D3)

| Role | Application | Status | Status Log | Settings | Passport Extraction |
|---|---|---|---|---|---|
| Operations Associate | read | read | read | – | – |
| Operations Team Lead | read | read | read | – | read |
| Reviewers (D2) | read | read | read | – | read, write (permlevel 0 and 1) |
| Visa Tracker Manager | full | full | full | full | read |

- Keep Application writes to `Visa Tracker Manager`. Status changes by
  operations go through the Process File (TASK-027).
- Add the rows as Custom DocPerm fixtures by name. Both known sites already
  have Custom DocPerm rows for these DocTypes, so rows add to the existing
  ones. On a site without them, the first Custom DocPerm row replaces the
  standard permissions; check this before migrate.
- Assign `Visa Tracker Manager` to the named owners (D3).

## Validation

- As an Operations Associate on `visa-tracker-test.localhost`: open the
  link from a Process File; pick a status in `custom_client_status`; cannot
  open Settings.
- As a reviewer: verify a `Needs Review` extraction (needs TASK-033).

## Definition of done

Validation passes and the role holders on the production site are recorded
here.
