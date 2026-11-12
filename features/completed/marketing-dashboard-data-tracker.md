---
id: FEAT-marketing-dashboard-data-tracker
title: Marketing Dashboard Data Tracker
status: completed
priority: high
repositories: [the_visaguy]
owners: []
depends_on: []
created: 2026-10-08
updated: 2026-10-15
---

# Marketing Dashboard Data Tracker

## Summary
A marketing dashboard data tracker in the visaguy erp site, inside `the_visaguy` app, providing insights dashboard with queries and charts based on marketing expenditure and lead generation data.

## User value
Allows marketing and management to track, separate, and roll up marketing expenditure and lead generation data by company and source. Provides a visual dashboard to analyze Cost Per Lead and aggregate metrics.

## Scope

### Included
- Custom DocTypes for tracking lead sources, spend details, and marketing spend.
- Python Script Queries executing DuckDB/MariaDB SQL logic for Frappe Insights v3.
- Visual Query Builder support with hybrid virtual tables and complex SQL operations.
- Unified single-table query joining `tabLead` and `tabCRM Lead` across 46 mapped attributes.
- Marketing Dashboard charts for Lead Status over time and Nationality-to-Destination flow.
- Direct export of updated workbook templates to `the_visaguy` app for deployment.

### Excluded
- Legacy data migrations prior to 2026-08-31 without the integer logic fallbacks.

## Requirements
- Support a structured hierarchy of custom DocTypes.
- Provide dual-path data engine logic (Historical cutoff vs Dynamic).
- Stabilize schemas in Frappe Insights via StringColumn Fix.
- Ensure Visual Query Builder can process UNIONs and safe division logic.
- Standardize lead status (`custom_status` in Lead, `status` in CRM Lead) and nationality (`custom_nationality_link`).

## Proposed design
(See Architecture and Data Model in Completion Notes)

## Tasks
- [x] TASK-build-marketing-dashboard-data-tracker
- [x] TASK-unify-lead-crm-lead-insights-query

## Acceptance criteria
- [x] Marketing Spend document captures weekly budgets by company.
- [x] Child tables accurately track budget and manual metrics.
- [x] Script query dynamically pulls real-time generated leads.
- [x] Visual query builder renders dashboards without JSON serialization crashes or empty row fallback issues.

## Dependencies
- Frappe Insights v3
- `the_visaguy` app

## Risks
- Frappe Insights caching issues (resolved with unique CTE prefixes and `getdate()` intercept).

## Open questions

## Completion notes

### Data Architecture & DocType Schema
The marketing dashboard relies on a structured hierarchy of custom DocTypes designed to capture, separate, and roll up marketing expenditure and lead generation data by company and source.

**1. Lead Source Group (Master)**
A master DocType used to group multiple individual lead sources together (e.g., combining "Website Ads" and "AI Leads") for aggregated reporting.

**2. Child Tables (Spend Details)**
Two distinct child tables capture line-item budgets and manual metrics for individual and grouped sources.
* **Lead Source Spend Details:** Tracks `lead_source` (Link), `amount_spend` (Currency), `total_leads` (Int), `total_messages` (Int), and `organic_messages` (Int).
* **Lead Source Group Spend Details:** Tracks `lead_source_group` (Link) along with the identical spend and count metrics as the individual table.

**3. Marketing Spend (Parent Transaction)**
This transactional DocType captures weekly budgets and contains both child tables, enforcing data separation by company.
* **Core Filters:** `from_date` (Date), `to_date` (Date), `company` (Link).
* **Roll-Up Summaries:** Automatically aggregates the child table data into grand totals: `total_spend`, `total_leads`, and `total_messages`.

### Frappe Insights v3 Script Query Logic
To accommodate historical data formats while transitioning to dynamic CRM tracking, the reporting engine utilizes Python Script Queries executing DuckDB/MariaDB SQL logic.

* **Dual-Path Data Engine (Historical Cutoff Logic):** The SQL logic pivots based on the `from_date` of the Marketing Spend document.
  * **Historical (<= 2026-08-31):** The query bypasses standard CRM tables entirely, pulling the static `total_leads` integer directly from the legacy fields in the custom DocTypes.
  * **Dynamic (>= 2026-09-01):** The query ignores the static fields and executes a `COUNT(DISTINCT)` `LEFT JOIN` against `tabLead` and `tabCRM Lead`. It dynamically matches the document's date range, zone/company, and mapped source fields to pull real-time generated leads.
* **Schema Stability (The StringColumn Fix):** Frappe Insights permanently caches a chart's column schema upon initial load. Using SQL formatting wrappers like `DATE_FORMAT()` flattens dates into strings, permanently breaking date-based truncations (Day/Month grouping). The engine resolves this by selecting raw dates in SQL and intercepting the output via Python using `frappe.utils.getdate()` or `frappe.utils.get_datetime()` to force the visual builder to lock the schema as a manipulatable Date object.
* **Empty Row Fallbacks:** To prevent visual builder rendering crashes when a query returns zero results, the script defines an `empty_row` dictionary containing all `None` values. If the SQL output is empty, it returns `[empty_row]` to preserve the column headers.

### Visual Query Builder & Dashboard Mechanics
The Insights drag-and-drop Visual Query Builder lacks native support for complex `UNION` operations or multi-conditional date range joins. The dashboard circumvents these limitations using hybrid virtual tables.

* **Virtual Tables & CTE Namespacing:** The complex SQL logic (combining both child tables via `UNION ALL`) is saved as a Native SQL query (e.g., "Master Source Spend"), which the Visual Query Builder then targets as a standard data source. To prevent fatal namespace collisions with Frappe Insights' background cache, all Common Table Expressions (CTEs) within these saved queries utilize strictly unique prefixes (e.g., `cte_individual_spends`).
* **Safe Division Mutate Operations:** Calculated columns mapped directly in the Visual Query Builder (like Cost Per Lead) are evaluated in a single-line sandbox. To prevent `Infinity` JSON serialization crashes when `sum_of_Total_Leads` evaluates to zero, standard inline SQL conditional logic is enforced. The syntax `"sum_of_Total_Spend" / NULLIF("sum_of_Total_Leads", 0)` is used to safely convert zero-division attempts into valid `null` values rather than crashing the dashboard.
 
### Unified Lead & CRM Lead Query Architecture (`TASK-unify-lead-crm-lead-insights-query`)
To enable cross-cutting analytics without querying disparate DocTypes, a canonical single-source CTE (`CombinedLeads`) was designed and benchmarked against 140,376 records.

1. **Schema Normalization**:
   - Maps 46 attributes across `tabLead` (124,682 rows) and `tabCRM Lead` (15,694 rows).
   - `lead_status`: Takes `custom_status` for `tabLead` (ignoring the default `status = 'Lead'`) and `status` for `tabCRM Lead`.
   - `lead_source`: Resolves `custom_lead_source` in `tabLead` and `source` in `tabCRM Lead`.
   - `nationality`: Strictly maps `custom_nationality_link` in both tables.
   - `is_converted`: Removed from columns; converted leads are defined by `lead_status = 'Payment Confirmed'`.
   - `email`: Maps `email_id` in `tabLead` to `email` in `tabCRM Lead`.
   - `monthly_salary`: Maps `custom_salary` in `tabLead` to `custom_monthly_salary` in `tabCRM Lead`.
   - Deprecated and orphan columns (`custom_assigned_to`, `custom_nationality`, `country`) were excluded.
2. **Dashboard Visualizations Added**:
   - **Lead Status over Time**: Aggregates counts across all operational status categories (`Payment Confirmed`, `Follow Up`, `Pending`, `Potential`, `Non Potential`, etc.) grouped by period (Weekly, Monthly, Yearly).
   - **Travelers (Nationality to Destination)**: Displays applicant volume flowing from nationality to destination country/region.
3. **Template Export & Deployment**:
   - Frappe Insights UI "Copy JSON" action fails on non-HTTPS environments due to browser Clipboard API security restrictions (`Cannot read properties of undefined (reading 'write')`).
   - The updated workbook was exported via Python backend `wb.export()` and synchronized directly to `the_visaguy/tvg_insights/workbook_templates/marketing/workbook.json` with 6 queries, 22 charts, and 2 dashboards for clean deployment across environments.
