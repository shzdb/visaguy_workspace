---
id: TASK-034
feature: FEAT-001
title: Roles and permissions for visa tracking
status: in-progress
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

# TASK-034: Roles and permissions for visa tracking

## Owner decisions (2026-09-28)

- D3: every role that can read `PF Process File` or `Lead` can read the
  tracking records. The permissions are defined in `the_visaguy`.
- D4: `Operations Associate` and `Operations Team Lead` can create
  tracking. `System Manager` keeps access.
- D2: verification is automatic, except that `Operations Associate` and
  `Operations Team Lead` may correct and verify a `Needs Review`
  extraction (ADR-007 amendment).

## Objective

Let everyone who works on a Lead or a Process File open its tracking, and
let operations create tracking when it is missing.

## Context (site `visaguy`, 2026-09-28, runtime-verified)

- Permission on `Visa Tracking Application`, `Visa Tracking Status`,
  `Visa Tracking Status Log` and `Visa Tracker Settings` is given only to
  `Visa Tracker Manager` and `Visa Tracker Operator`. **No user on
  `visaguy` holds either role.**
- 69 active users hold `Operations Associate` and 25 hold `Operations Team
  Lead` (107 and 36 including disabled users).
  They have no permission on any of these DocTypes. So:
  - clicking the Process File's tracking link gives a permission error;
  - the `custom_client_status` picker (TASK-027) cannot search statuses,
    so the manual status change cannot be used.
- `Passport Extraction` gives access to `Passport Extractor User` and
  `System Manager` only. `passport_extractor` is not installed on
  `visaguy` yet.

## Required behaviour

### 1. Read (D3)

Add `read` on `Visa Tracking Application`,
`Visa Tracking Status` and `Visa Tracking Status Log` for each role that
reads `PF Process File` or `Lead` on `visaguy` (Custom DocPerm,
2026-09-28):

`Lead Role`, `TVG-Lead Manager`, `Consultant Role`, `Consultant Invoice -
TVG`, `Operations Associate`, `Operations Team Lead`, `Process File
Manager`, `Business Client Consultant`, `Business Client Manager`,
`Sales User`, `Sales Manager`, `Accounts User - TVG`, `Finance Manager -
TVG`, `Agent`, `admin role`, `Desk User`.

`Desk User` is the Frappe role that every desk user has, so in practice
every desk user can read tracking. That matches D3. Keep the explicit list
anyway, so the intent is clear if `Desk User` is removed from Lead later.

### 2. Create (D4)

- `Operations Associate` and `Operations Team Lead`: `create` on `Visa
  Tracking Application`, in addition to read.
- The TASK-031 manual actions check these roles on the server and create
  the Passport Extraction with `ignore_permissions`.

### 2a. Passport Extraction (D2 exception)

- `Operations Associate` and `Operations Team Lead`: `read` and `write` at
  permlevel 0 on `Passport Extraction`, so they can open and verify a
  `Needs Review` record (TASK-033). No `create`, no `delete`, and no
  permlevel 1: the raw OCR text and MRZ lines stay hidden.
- These rows live in `the_visaguy` fixtures, not in `passport_extractor`,
  so the extractor stays free of VisaGuy roles (ADR-003).

### 3. Write

Keep `write` on the Application and on statuses with `Visa Tracker
Manager` and `System Manager`. Operations change the status through the
Process File (TASK-027).

### 4. How

- Custom DocPerm fixtures in `the_visaguy/fixtures/custom_docperm.json`,
  filtered by name. No bare-string fixture entry (risk 25).
- Both known sites already have Custom DocPerm rows for these DocTypes, so
  the new rows add to them. On a site without them, the first Custom
  DocPerm row replaces the standard permissions. Check this before migrate.

## Validation

On `visa-tracker-test.localhost`, with a test user per role:

- `Lead Role` and `Consultant Role`: open the tracking link from a Lead's
  applicant row and from a Process File; cannot edit the Application;
  cannot open `Visa Tracker Settings` or `Passport Extraction`.
- `Operations Associate`: verify a `Needs Review` extraction and cannot see
  the raw OCR fields; open the link; pick a status in
  `custom_client_status` (TASK-027); run **Generate Visa Tracking**
  (TASK-031).
- A user without any listed role gets a permission error.

## Definition of done

Validation passes, the fixture rows are listed here with the commit SHA,
and the permission rows on the production site are checked after migrate.

## Implementation (2026-09-28)

Branch `feat/visa-tracker` in `the_visaguy` on the bench (installed checkout), commits `aa94c86`, `7ecfbd3`, merged `5790c7f`. Not pushed, not deployed.
Built by Cursor executors, reviewed and merged by the orchestrator; records in
`ongoing/visa-tracking-soft-launch/`.

Evidence: Static matrix tests; on the test site Custom DocPerm rows present for all five DocTypes with the standard rows kept, including System Manager on Visa Tracker Settings (it was locked out before). Full suites on `visa-tracker-test.localhost` after all merges: `the_visaguy` 638 OK, `passport_extractor` 98 OK (`--skip-test-records`).

## What remains

1. Owner migrates and tests `visaguy` (never run by Claude; see memory rule).
2. Browser check of the desk UI.
3. Push and deploy (owner).
