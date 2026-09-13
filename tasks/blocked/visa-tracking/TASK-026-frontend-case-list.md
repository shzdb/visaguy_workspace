---
id: TASK-026
feature: FEAT-001
title: Case list and case switching in the tracker SPA
status: blocked
repository: visa_tracker
app_path: /Users/shzd/Projects/tridz/visa_tracker
owners: []
depends_on:
  - TASK-025
created: 2026-09-14
updated: 2026-09-14
---

# TASK-026: Case list and case switching in the tracker SPA

## Blockers

- TASK-025 (wire contract).

## Required behaviour

1. After verification call `list_applications`. One case → status page as
   today. Several → a case list showing destination, role, status title,
   last updated.
2a. Remove `visa_type` (ADR-015 §7): `src/types/tracking.ts`,
   `src/test/contract/wireContract.ts` (fixtures and the key list),
   `src/components/tracking/StatusSummary.tsx`, `src/api/contract.test.ts`.
2. Status page for the chosen `application_ref`, with a control to switch
   case without re-verifying.
3. Token and refs in React state only (ADR-005); no URL, storage, or logs.
4. Wire contract, MSW mocks, contract tests, E2E journey for one and for
   several cases, privacy assertions extended to refs.

## Validation

`npm run verify` green; a human visual check of the list on desktop and
mobile. Deploy after TASK-025.
