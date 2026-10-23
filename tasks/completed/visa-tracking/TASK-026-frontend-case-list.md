---
id: TASK-026
feature: FEAT-001
title: Case list and case switching in the tracker SPA
status: completed
repository: visa_tracker
app_path: /Users/shzd/Projects/tridz/visa_tracker
owners: []
depends_on:
  - TASK-025
created: 2026-09-14
updated: 2026-10-23
---

# TASK-026: Case list and case switching in the tracker SPA

## Required behaviour

1. After verification call `list_applications`. One case → status page as
   today. Several → a case list showing destination, role, status title,
   last updated.
2. Status page for the chosen `application_ref`, with a control to switch
   case without re-verifying.
3. Remove `visa_type` (ADR-015 §7).
4. Token and references in React state only (ADR-005).
5. Wire contract, MSW mocks, contract tests, E2E for one and several cases.

## Implementation (2026-09-14)

`visa_tracker` `654b9f0` on `main`. Pushed 2026-09-14 (`49dd6b1..654b9f0`).

- `src/types/tracking.ts`: `ApplicationSummary`, `ApplicationsResponse`;
  `visa_type` removed.
- `src/api/client.ts`: `LIST_ENDPOINT`, `fetchApplications`;
  `fetchStatus(token, applicationRef?)` sends `application_ref` only when given.
- `src/hooks/useTrackingStatus.ts`: shared `useTrackingRequest` (keyed
  request, callbacks through refs); `useTrackingStatus(token, ref)`.
  New `src/hooks/useApplications.ts`.
- `src/pages/StatusPage.tsx`: loads the list; one case is opened directly;
  several show `ApplicationList` under a "Your applications" heading. The
  chosen reference is page state. `ApplicationStatus` is keyed by reference,
  so switching starts clean; "View all applications" appears only when
  there are several.
- New `src/components/tracking/ApplicationList.tsx`.
- `StatusSummary`: visa type card removed.
- `wireContract.ts` / `mocks/handlers.ts`: list fixtures (one and two cases),
  a second status fixture, `multipleApplicationsHandlers`.

## Validation

`npm run verify`: lint (only the existing `SessionContext.tsx`
fast-refresh warning), `tsc --noEmit`, **72/72 tests**, build clean.
New tests: list request and response conformance; status request with a
reference; `ApplicationList` rendering and selection (reference never
rendered); E2E — several cases listed with roles, the chosen case opens,
switch back and open the other without re-verifying, nothing written to
storage or the URL; a single case opens directly with no list or switch.

## What remains

1. Push `visa_tracker` `main` (also carries `dc53ce6`).
2. Deploy after the TASK-025 backend.
3. Human visual check of the case list on desktop and mobile.

## Completion (2026-10-23)

Moved to `completed` by a workspace maintenance pass.

- **Deployment evidence:** owner confirmation, 2026-10-23: everything merged
  to `main` up to the 2026-10-20 go-live is deployed on live, including
  tridz-dev/passport_extractor#5 and tvgglobal/the_visaguy#47, and the
  `visa_tracker` frontend is live.
- **Merge evidence (GitHub compare, 2026-10-23):** every commit listed in
  this task is contained in `main` as of the go-live: `the_visaguy`
  `4f3d063`, `passport_extractor` `a2f5a4a`, `visaguy_crm` `daa863e`,
  `visa_tracker` `654b9f0`, `fileflo` `main`.
- **Validation:** as recorded above in this task (pure and on-site suites on
  `visa-tracker-test.localhost`).
- **Known limitations:** owner checks other than deployment that are listed
  under "What remains" (browser or desk checks, printed patch counts) were
  not recorded in the workspace.
- **Note:** The owner confirmed the `visa_tracker` frontend is live.
