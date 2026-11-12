---
id: TASK-duplicate-leads-insight-update
feature: null
title: Update Duplicate Leads Insight Report — Zone Filter + Owner/Status Columns
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: ["TASK-duplicate-leads-report"]
expected_files:
  - duplicate_leads_insight.py
  - duplicate_leads_insight.js
created: 2026-10-19
updated: 2026-10-22
---

# Update Duplicate Leads Insight Report — Zone Filter + Owner/Status Columns

## Objective

Extend the existing **Duplicate Leads Insight** Script Report with a Zone filter and four new columns showing lead owner and lead status for both the duplicate lead and its parent lead.

## Context

The original report (TASK-duplicate-leads-report) filtered only by Lead Source and Created After date. Users needed the ability to narrow results by Zone and to see ownership and status information for both sides of the duplicate pair without having to open each lead individually.

## Inputs

- Filter: `zone` — Link → `Zone` DocType (optional, default `"TVG"`)
- New column data sources: `dl.lead_owner`, `dl.custom_status`, parent `lead_owner` and `custom_status` carried through the CTE

## Required behaviour

- A new **Zone** filter (Link → Zone, optional, default TVG) must appear after the existing Created After filter.
- The zone filter applies to the **parent lead's zone** (`custom_zone` of the first lead per mobile number). When left blank, no zone restriction is applied.
- Four new columns must be added in the correct order:
  - After Duplicate Lead Source: **Duplicate Lead Status** (`dl.custom_status`), **Duplicate Lead Owner** (`dl.lead_owner`)
  - After Parent Lead Source: **Parent Lead Status**, **Parent Lead Owner**
- Existing filter behaviour (Lead Source and Created After) must be unchanged.

## Constraints

- No schema migration — both `lead_owner` and `custom_status` already exist on `tabLead`.
- Zone value is passed as a bound SQL parameter (`%(zone)s`), not interpolated into the query string.
- Conditional WHERE clause: zone condition is only appended when the filter has a value.

## Expected changes

- `duplicate_leads_insight.js` — add `zone` Link filter with `default: "TVG"`.
- `duplicate_leads_insight.py` — extend CTE to carry `lead_owner`, `custom_status`, `custom_zone` for parent; add 4 new SELECT fields; build dynamic zone condition.

## Validation

Verified by running `bench --site visaguy execute` with two cases:

1. **With `zone = "TVG"`** — returns correct rows, all 12 columns present, spot-checked `CRM-LEAD-2026-23851` (`duplicate_lead_owner = roshan@visaguy.ae`, `duplicate_lead_status = Payment Initiated`) ✅
2. **Without zone filter** — no extra WHERE clause appended, same result set as before ✅

## Definition of done

- `duplicate_leads_insight.py` and `duplicate_leads_insight.js` updated in `visaguy_crm` app.
- Report verified via `bench execute` with and without the zone filter.
- Changes left unstaged for developer review and commit.
