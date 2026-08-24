---
id: TASK-duplicate-leads-report
feature: null
title: Create Duplicate Leads Insight Script Report
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - duplicate_leads_insight.py
  - duplicate_leads_insight.js
  - duplicate_leads_insight.json
created: 2026-08-20
updated: 2026-08-20
---

# Create Duplicate Leads Insight Script Report

## Objective
Create a standard Script Report for the Lead DocType in `visaguy_crm` to identify duplicate leads along with their parent lead based on specific date and source filters.

## Context
Consultants may create duplicates of existing leads, sometimes deliberately. We need a report to gain insights into leads duplicated after a specific date. The parent lead is identified as the first lead with the same mobile number.

## Inputs
- DocType: `Lead`
- Field: `custom_is_duplicate` (Check)
- Field: `mobile_no` (Data)
- Filter 1: `lead_source` (default "Google Ads")
- Filter 2: `created_after` (default "2026-07-22")

## Required behaviour
- The report should display the duplicate lead and its parent lead side-by-side.
- Parent lead is determined by grouping leads by `mobile_no` and finding the one with the earliest `creation` date.
- Both the duplicate lead and its parent lead must have a `creation` date on or after `created_after`.
- The parent lead must match the selected `lead_source` filter. The duplicate lead's source is not filtered.
- `custom_is_duplicate` must be checked (1) for the duplicate lead.

## Constraints
- Do not use a correlated subquery in the `JOIN` clause to avoid performance issues on large tables. Use a Common Table Expression (CTE) with `ROW_NUMBER()` or a `GROUP BY` to find the earliest lead per `mobile_no`.
- Must be a Standard Script Report belonging to the `visaguy_crm` app.

## Expected changes
- A new Script Report `Duplicate Leads Insight` configured in the database.
- Python server script (`duplicate_leads_insight.py`) with the SQL CTE logic.
- JS client script (`duplicate_leads_insight.js`) defining the two mandatory filters with their defaults.

## Validation
- Verify the SQL query executes correctly and filters on `custom_is_duplicate`, parent source, and both creation dates.
- Verify the JS configures the `created_after` filter to default to `2026-07-22`.

## Definition of done
- The implementation code (Python and JS) is generated and handed over to the developer for deployment in `visaguy_crm` as an artifact.
- The logic accounts for edge cases like missing mobile numbers and multiple leads with the same mobile number.
