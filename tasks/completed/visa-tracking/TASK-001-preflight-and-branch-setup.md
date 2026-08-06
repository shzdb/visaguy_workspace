---
id: TASK-001
feature: FEAT-001
title: Preflight, local repository setup, and exact integration evidence
status: completed
repository: multiple
owners: []
depends_on: []
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# Preflight, local repository setup, and exact integration evidence

## Objective

Replace the planning assumptions in FEAT-001 with source evidence, and create the `feat/visa-tracker` branch in every repository that the feature will change.

## Context

FEAT-001 was written before the FileFlo persistence path, the field-ID property, and the Lead-to-Process-File relationship had been read at source level. The feature document explicitly required this task to confirm those joins before any code was written.

## Required behaviour

Evidence the exact FileFlo persisted record and post-save location; the exact stable field-ID property; the File Collection to Lead relationship; the Lead to `PF Process File` creation path; and whether both ERPNext `Lead` and `CRM Lead` require tracking links.

Create `feat/visa-tracker` in `the_visaguy`, `fileflo`, and `passport_extractor` before any change lands.

## Constraints

- No application repository may be modified from its default branch.
- `processflo` must not be branched or edited unless a direct change proves unavoidable.

## Validation

- `git branch -a` in each repository shows `feat/visa-tracker`.
- The architecture specification records the confirmed integration points.

## Definition of done

Branches exist and the architecture document reflects evidenced integration points rather than assumptions.

## Implementation evidence

Verified on the remote bench `/home/shahzad/bench` on 2026-08-06:

| Repository | Branch | Status |
|---|---|---|
| `the_visaguy` | `feat/visa-tracker` @ `8254f93` | exists, pushed to upstream |
| `fileflo` | `feat/visa-tracker` @ `c7244a4` | exists, pushed to upstream 2026-08-06 |
| `passport_extractor` | `feat/visa-tracker` @ `0216829` | exists, pushed to upstream 2026-08-06 |
| `processflo` | `develop` | not branched — no direct change was required, as planned |

Confirmed integration points, as evidenced by the shipped implementation:

- FileFlo persists submitted data in `fileflo/data_collection.py`; the post-persistence extension point is `fileflo/events.py:dispatch_after_commit_extension_event`.
- The stable field identifier is `field_id`, carried onto rows created by both the single- and multi-upload paths (`fileflo` `c7244a4`).
- `PF Process File` remains owned by `processflo`; `the_visaguy` subscribes through `doc_events` rather than editing `processflo`.
- Both ERPNext `Lead` and `Customer` receive tracking wiring (`the_visaguy.visa_tracking.handlers.lead_handlers`); `CRM Lead` was not required.

## Deviations

`processflo` was left untouched, which matches the preferred path in the feature document. `Customer` was wired in addition to `Lead`, which the feature document anticipated in its passport ownership rules.
