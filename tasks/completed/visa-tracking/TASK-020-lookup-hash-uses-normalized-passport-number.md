---
id: TASK-020
feature: FEAT-001
title: Lookup hash must use the normalized passport number, not the raw MRZ field
status: completed
repository: the_visaguy, passport_extractor
app_path: /home/shahzad/bench/apps/the_visaguy
owners: []
depends_on:
  - ADR-011
  - TASK-006
created: 2026-09-03
updated: 2026-09-03
---

# TASK-020: Lookup hash must use the normalized passport number

## Objective

Public verification failed for any passport whose number is shorter than the
9-character MRZ slot. Make the lookup hash agree across all three code paths
that compute it, and stop storing MRZ padding in `passport_number`.

## Context

Reported 2026-09-03: a `POST` to `verify_identity` with
`{"passport_number": "G2746747", "date_of_birth": "1994-10-11"}` returned the
generic failure, despite a Verified `Passport Extraction` (`PEX-2026-00012`)
and an open, tracking-enabled `Visa Tracking Application` (`VTA-2026-00756`)
existing for that passport.

Two defects, one behind the other.

**Padding stored as data.** `parse_td3_mrz` assigned
`passport_number = line2[0:9]`, the fixed-width MRZ slot. ICAO pads it with
`<`, so an 8-character Ghanaian number was stored as `G2746747<`.

**Three paths, two inputs.** `lifecycle_service.create_tracking_application`
hashed `passport_number` (padded), while
`patches/recompute_lookup_hash_unkeyed.py` hashes
`passport_number_normalized` (clean) and `verify_identity` hashes what the
user types (clean). Creation therefore wrote a hash no client could ever
reproduce.

Measured on the dev site:

```
'G2746747'   -> 57c365e2f614f9...   matched no application
'G2746747<'  -> 5f8fe6c3be70fe...   matched VTA-2026-00739, VTA-2026-00756
```

Any 9-character passport number leaves no filler and hides the defect
completely, which is why the `M00381296` test passport always verified.

## Changes

- `the_visaguy/visa_tracking/services/lifecycle_service.py` — hash
  `passport_number_normalized`, falling back to `passport_number`.
- `passport_extractor/passport_extractor/ocr/mrz_parser.py` — strip `<`
  padding from the stored `passport_number`. The padded field is retained
  for check-digit and composite arithmetic, which are defined over the
  fixed-width slot; only the stored value changes.

## Validation

- `passport_extractor`: 34 pure tests pass, including three new ones covering
  a short number, a full-length number, and stripping after OCR correction.
- `the_visaguy`: full `visa_tracking` discovery, 268 tests, 2 errors — both
  pre-existing in `TestProcessFileHandler` (missing site context in an
  enqueue path), confirmed by re-running with the pristine
  `lifecycle_service.py` and observing the identical two errors.
- Verified against the real MRZ locally: `passport_number` now reads
  `G2746747` with all five check digits still valid. No real MRZ data was
  written to either repository, per TASK-003 §9.4.

## Completion evidence

- `passport_extractor` `5f2403e` (with the TASK-019 fix in the same commit).
- `the_visaguy` `53ed207`.
- Both on `feat/visa-tracker`, committed locally, not pushed or deployed.

## Not done

**Existing rows still carry the old hash.** The recompute patch was not run —
the command was refused by host permission policy:

```
bench --site visaguy execute the_visaguy.patches.recompute_lookup_hash_unkeyed.execute
```

Until it runs, `VTA-2026-00756` keeps hash `5f8fe6c3be70fe...` and
verification for that passport still fails despite the corrected code. The
patch is idempotent and derives from `passport_number_normalized`, so it will
write `57c365e2f614f9...`.

**Existing `Passport Extraction` rows keep the padded value.** `PEX-2026-00012`
still stores `passport_number` as `G2746747<`. Nothing depends on it now that
hashing uses the normalized field, but it displays wrongly in the desk UI.
Cleaning it is a separate data fix and was not attempted.
