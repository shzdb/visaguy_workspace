---
id: TASK-002
feature: FEAT-001
title: Passport extractor app scaffold and extraction-history data model
status: completed
repository: passport_extractor
owners: []
depends_on:
  - TASK-001
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Passport extractor app scaffold and extraction-history data model

## Objective

Create a new, reusable `passport_extractor` Frappe app owning a `Passport Extraction` history DocType, with no knowledge of VisaGuy domain concepts.

## Required behaviour

- A `Passport Extraction` DocType storing source, processing state, MRZ data, extracted values, verification state, duplicate detection, and supersession.
- No imports from `fileflo`, `processflo`, `Lead`, `Customer`, or `Visa Tracking Application`.
- A new or corrected upload creates a new record; prior history is never overwritten or deleted.
- The original file and raw extraction result remain private and internal.

## Constraints

The app must be independently installable and must not depend on any VisaGuy app.

## Validation

- `bench --site <site> install-app passport_extractor` succeeds.
- The DocType migrates cleanly.
- No VisaGuy identifier appears anywhere in the app source.

## Definition of done

The app installs, the DocType exists, and the reusability boundary holds.

## Implementation evidence

Repository `tridz-dev/passport_extractor`, branch `feat/visa-tracker`:

| Commit | Date | Subject |
|---|---|---|
| `07b8cab` | 2026-07-21 | feat: Initialize App |
| `6746d04` | 2026-07-21 | feat: add passport extraction data model |
| `2f25c0d` | 2026-07-21 | fix: enforce passport extraction invariants |

Files: `passport_extractor/passport_extractor/doctype/passport_extraction/` (`.json`, `.py`, `test_*.py`), `role/passport_extractor_user/passport_extractor_user.json`, `utils.py`.

Installed on site `visaguy` (`bench --site visaguy list-apps` reports `passport_extractor 0.0.1`) and on the test site `visa-tracker-test.localhost`.

Reusability boundary verified: the app declares no `required_apps` and its `hooks.py` contains no VisaGuy references.
