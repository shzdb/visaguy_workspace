---
id: TASK-build-marketing-dashboard-data-tracker
feature: FEAT-marketing-dashboard-data-tracker
title: Build Marketing Dashboard Data Tracker
status: completed
repository: the_visaguy
owners: []
depends_on: []
expected_files: []
created: 2026-10-08
updated: 2026-10-08
---

# Build Marketing Dashboard Data Tracker

## Objective
Build a marketing dashboard data tracker in the visaguy erp site, inside `the_visaguy` app, providing an insights dashboard with queries and charts.

## Context
The marketing dashboard relies on a structured hierarchy of custom DocTypes designed to capture, separate, and roll up marketing expenditure and lead generation data by company and source.

## Inputs
- Existing Frappe Insights configuration.
- Lead and CRM Lead data sources.

## Required behaviour
- Implement Custom DocTypes: Lead Source Group, Lead Source Spend Details, Lead Source Group Spend Details, Marketing Spend.
- Create Python Script Queries executing DuckDB/MariaDB logic for dual-path data fetching (historical static values vs dynamic COUNT(DISTINCT) queries).
- Mitigate Frappe Insights caching issues by selecting raw dates and casting in Python, using unique CTE prefixes for namespace safety, and implementing safe division via NULLIF.

## Constraints
- Must handle historical cutoff logic (<= 2026-08-31 for static numbers, >= 2026-09-01 for dynamic queries).
- Must resolve the StringColumn fix for date schemas in Frappe Insights.
- Must prevent dashboard rendering crashes on division by zero using NULLIF.

## Expected changes
- Custom DocTypes creation.
- Native SQL Queries saving for Frappe Insights virtual tables.
- Python logic intercepts to enforce correct type serialization.

## Validation
- Verified the dashboard aggregates data accurately.
- Verified zero results fallback preserves column schemas.
- Verified dynamic date range queries match expected counts.

## Definition of done
- The feature is fully implemented and deployed in the workspace, with architecture and logic documented in the workspace tracker.
