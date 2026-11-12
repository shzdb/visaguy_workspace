---
id: TASK-unify-lead-crm-lead-insights-query
feature: FEAT-marketing-dashboard-data-tracker
title: Unify Lead & CRM Lead Insights Query and Dashboard Charts
status: completed
repository: the_visaguy
owners: []
depends_on:
  - TASK-build-marketing-dashboard-data-tracker
expected_files:
  - the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json
created: 2026-10-15
updated: 2026-10-15
---

# Unify Lead & CRM Lead Insights Query and Dashboard Charts

## Objective
Unify records from both `tabLead` (ERPNext/legacy custom Lead layer) and `tabCRM Lead` (Frappe CRM layer) into a single virtual table (`CombinedLeads`) with 46 mapped attributes in Frappe Insights v3. Use this unified query to power marketing and operations charts (Lead Status distribution over time, and traveler flow by Nationality to Destination), and export the updated workbook template into `the_visaguy` repository for deployment across environments.

## Context
Visa services track leads across both legacy `Lead` and newer `CRM Lead` DocTypes. Field naming and business logic differ between the two tables:
- `custom_lead_source` in `Lead` vs `source` in `CRM Lead`
- `custom_status` in `Lead` (where standard `status` defaults to `'Lead'`) vs `status` in `CRM Lead`
- `email_id` in `Lead` vs `email` in `CRM Lead`
- `custom_salary` in `Lead` vs `custom_monthly_salary` in `CRM Lead`
- `custom_nationality_link` in both tables (skipping legacy text nationality and country fields)
- Conversion definition is strictly `lead_status = 'Payment Confirmed'` across both tables.

When exporting the workbook from the browser Insights UI, non-HTTPS environments fail on `navigator.clipboard.write` (`Cannot read properties of undefined (reading 'write')`). The workbook template must be exported directly via backend API calls into `the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json`.

## Inputs
- `tabLead` and `tabCRM Lead` tables in database site `visaguy`.
- Frappe Insights v3 Workbook `Marketing Dashboard` (`name: 19`).
- Template location: `the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json`.

## Required Behaviour
1. Design and benchmark a canonical `CombinedLeads` CTE unifying 46 fields across `tabLead` and `tabCRM Lead`.
2. Map `lead_status`:
   - `Lead`: `custom_status AS lead_status`
   - `CRM Lead`: `status AS lead_status`
3. Map `nationality`:
   - `custom_nationality_link AS nationality` in both tables.
4. Support chart queries:
   - **Lead Status (Weekly / Monthly / Yearly)**: Counts by operational status category (Payment Confirmed, Follow Up, Potential, Pending, etc.).
   - **Travelers (Nationality to Destination)**: Volume of applicants grouped by `nationality` and `destination`.
5. Export the updated workbook from Frappe Insights v3 into `the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json` containing 6 queries, 22 charts, and 2 dashboards.

## Expected Changes
- `the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json`:
  - Added query `Lead and CRM Lead Combined` (`djonb43h0p`).
  - Added charts: `Weekly Leads` (`dv67ehi6id`), `Monthly Leads` (`f29q4onusn`), `Yearly Leads` (`f7se002t1m`), `Nationality to Destination` (`g1imlneoku`, `m8leuvmqks`), and `Lead Status` (`jfdpgoqh4r`).
  - Updated workbook dependencies and dashboard layouts for `Marketing - Charts` and `Marketing - Numbers`.

## Validation
- Master CTE query executed directly on site `visaguy` across all 140,376 records in ~1.4 seconds.
- Verified 16,813 converted `Lead` records and 330 converted `CRM Lead` records under `lead_status = 'Payment Confirmed'`.
- Verified top destination flows (e.g., UAE $\rightarrow$ Schengen: 17,083; UAE $\rightarrow$ UK: 8,010; UAE $\rightarrow$ USA: 6,745).
- Verified workbook template export structure matches Frappe Insights v3 import schema.

## Definition of Done
- The query design and field mapping are verified against live bench data.
- The workbook template in `the_visaguy` is updated with all new queries and charts, unstaged for review and deployment.
- Workspace feature and task documentation updated.
