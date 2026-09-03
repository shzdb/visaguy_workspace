---
id: TASK-fix-zoho-multi-company-customer-mapping
feature: null
title: Fix Zoho Multi-Company Customer Mapping
status: completed
repository: visaguy_crm
owners: ["fasil"]
depends_on: []
expected_files:
  - zoho_integration_apis.py
  - migrate_zoho_customer_id_to_company_mapping.py
created: 2026-08-31
updated: 2026-08-31
---

# Fix Zoho Multi-Company Customer Mapping

## Objective
Fix the Zoho integration bug where a single ERPNext Customer shared across multiple companies causes "Customer does not exist" errors in Zoho when invoices are created in a company different from the one where the Zoho customer was originally mapped.

## Context
The Zoho Books integration previously stored a single `custom_zoho_customer_id` field on the ERPNext `Customer` doctype. When a single ERPNext Customer interacts with two different companies (e.g., `TVG LLC` and `TVG`), each connected to a separate Zoho Books account, the integration breaks because the single field can only hold one company's Zoho Customer ID. 

## Inputs
- DocType: `Customer`
- Child DocType: `Zoho Customer Company Mapping` (custom_zoho_company_mappings)

## Required behaviour
- The `custom_zoho_customer_id` field is replaced in logic by a child table `custom_zoho_company_mappings` that maps each ERPNext Company to its respective Zoho Customer ID.
- During Sales Invoice submission, the system looks up the Zoho Customer ID from the child table for the specific company of the invoice.
- If no mapping exists for that company, the system creates the customer in that company's Zoho account and saves the new mapping in the child table.
- Similar company-aware lookups are enforced for Payment Entries and Credit Notes.

## Expected changes
- `visaguy_crm/server_scripts/payment_from_lead/zoho_integration_apis.py`: Updated functions `create_zoho_invoice`, `create_zoho_payment` (advance and SI), and `create_zoho_credit_note` to use company-aware lookup/save helpers.
- `visaguy_crm/patches/migrate_zoho_customer_id_to_company_mapping.py`: Migration script to seed the child table using existing `custom_zoho_customer_id` values and the company of the customer's most recent submitted Sales Invoice.

## Validation
- Verified the Python functions properly read the child table.
- Verified the migration script groups DB commits correctly for performance.

## Definition of done
- The `visaguy_crm` Python code on the remote bench is updated and the patch is deployed.
