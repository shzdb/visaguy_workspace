# Plan — Several Tracking Applications per Passport, and Manual Status from the Process File

> Date: 2026-09-14
> Feature: FEAT-001
> Status: **plan, not ready.** Both items need owner decisions (§1.6, §2.6)
> before tasks can be marked `ready`.
> Evidence: `the_visaguy` `feat/visa-tracker` at `6221926`, Frappe v15 source,
> read-only queries on `visaguy`.

---

## 1. Several tracking applications for one passport

### 1.1 Requirement

One person (one passport + date of birth) can be in several visa cases at
the same time. Their role can differ per case: primary in one and dependant
in another, primary in all, dependant in all. The client verifies once and
must be able to see each case.

### 1.2 What the code does today

| Area | Today | Effect for this requirement |
|---|---|---|
| Scope | Feature README "Excluded from the first release": one active tracking application per verified passport identity; a case selector is out of scope. | This item is a **scope change**. It needs an ADR. |
| Creation | `lifecycle_service.create_tracking_application` looks up active applications by `verification_lookup_hash`. One match → **reuse it**. More than one → flag "identity conflict" and create nothing. | A second case for the same passport never gets its own application. |
| Lead link on reuse | `_ensure_lead_links` sets the *second* Lead's `custom_visa_tracking_application` to the *first* case's application, and only flags "lead mismatch". | **Existing defect:** the second Lead points at another case's application. |
| Verification | `api/verification.py` step 5: `frappe.db.get_value(... verification_lookup_hash in candidates)` returns one arbitrary match. | With several matches the client sees a random case. |
| Session | `session_service.create_session(tracking_application)` stores one application name. | One case per session. |
| Status API | `get_tracking_status(session_token)` returns one application. Primary/dependant role and the dependant display override already come from that application's own Process File (`get_process_file_family`). | The per-case role logic already works once each case has its own application. |
| Frontend | `verifyIdentity` → token → `fetchStatus` → one `StatusPage`. | No selector. |

Live data on `visaguy` (2026-09-14): 20 Passport Extractions; **2 passports
appear in more than one source document**; **2 "Visa tracking: identity
conflict" Error Log entries**; 0 active duplicate hashes. The situation
already happens on test data.

### 1.3 Proposed design

**Rule: one tracking application per applicant per case.** The case key is
the applicant's lead-stage **file collection**, which is already per
applicant per Lead and is already the ownership key for Process Files
(ADR-014).

1. **Creation** — reuse an active application only when both
   `verification_lookup_hash` **and** `file_collection` match (redelivery of
   the same case stays idempotent). Same hash, different file collection →
   create a new application. Remove the "identity conflict" block for that
   case; keep flagging only true duplicates (same hash + same collection).
2. **Lead links** — stop overwriting the Lead's single
   `custom_visa_tracking_application`. Recommended: add a
   `visa_tracking_application` Link on the Lead's applicant child row
   (`custom_applicant_information`, which already carries `file_collection`)
   and keep the Lead-level Link for the primary applicant only.
   (Needs a `visaguy_crm` field; decision D4.)
3. **Role per case** — no new logic. Each application links its own
   Process File (ADR-014); `get_process_file_family` decides primary or
   dependant for that case. Before a Process File exists, the role comes
   from the applicant row `type`.
4. **Verification** — load **all** active, tracking-enabled applications for
   the hash (cap, e.g. 20, ordered by `status_updated_on desc`). Store them
   in the session as a map of **session-scoped opaque refs** → application
   names. No internal names leave the server (ADR-005). Rate limiting and
   the constant failure body are unchanged.
5. **Public API** —
   - `get_tracking_status(session_token, application_ref=None)`. Without a
     ref and exactly one application: today's response, unchanged
     (backward compatible). With a ref: that case.
   - New `list_applications(session_token)` →
     `[{application_ref, destination, visa_type, role, title, last_updated}]`.
     Or add this array to the status response (decision D3).
   - An unknown ref returns the constant generic failure.
6. **Frontend** — after verification: one application → status page as
   today; several → a case list (destination, visa type, role, status
   title, last updated), then the status page with a "switch case" control.
   Token and refs stay in React state only (ADR-005).
7. **Labels** — the selector needs something to tell cases apart.
   `destination` and `visa_type` exist on the application but nothing writes
   them today. Populate from the Lead/Process File at creation and on link
   (decision D2).

### 1.4 Work breakdown

| Task (draft) | Repo | Scope |
|---|---|---|
| ADR-015 | workspace | Supersede the one-application-per-identity exclusion; case key; session shape; ADR-005 amendment for refs. |
| TASK-024 | `the_visaguy` (+ `visaguy_crm` field) | Creation key, Lead/applicant-row link, `destination`/`visa_type` population, fix the Lead-link overwrite. |
| TASK-025 | `the_visaguy` | Session holds several refs; `list_applications`; `application_ref` on status; audit per case. |
| TASK-026 | `visa_tracker` | Case list, switch control, wire contract, MSW mocks, E2E and privacy tests. |

Order: ADR-015 → TASK-024 → TASK-025 → TASK-026. Backend deploys before
frontend; the single-application response stays identical, so the current
frontend keeps working in between.

### 1.5 Tests

- Same passport, two file collections → two applications; same collection
  redelivered → one.
- Primary in case A and dependant in case B → each status response shows
  the right role, dependants, and (for B) the primary's display status.
- Verify with 1, 2, and cap+1 applications; refs are opaque and
  session-scoped; a ref from another session fails generically.
- Closed application excluded; one closed + one open → single-case path.
- Second Lead no longer points at the first case's application.
- Frontend: one case skips the list; several show it; switching does not
  re-verify; nothing persisted outside memory.

### 1.6 Decisions needed

- **D1** Case key = lead-stage file collection? (Recommended.) Alternative:
  Lead + applicant row.
- **D2** Selector labels: which fields, and where they come from
  (destination and visa type from Process Template / Lead?).
- **D3** Separate `list_applications` endpoint, or an `applications` array in
  the status response?
- **D4** Lead link: add a Link on the applicant child row (recommended), or
  drop the Lead-level Link entirely?
- **D5** Show closed/completed cases in the list, or active only?
- **D6** The 2 existing identity conflicts on `visaguy`: re-run creation
  after TASK-024, or leave (dev data)?

---

## 2. Manual status change from the Process File

### 2.1 Requirement

Staff change a case's tracking status from the linked `PF Process File`.
The field should get its initial value through `fetch_from` where possible.

### 2.2 What the code does today

- `PF Process File.custom_client_status` — Link → `Visa Tracking Status`,
  **`read_only: 1`**, `depends_on: eval:doc.custom_visa_tracking_application`,
  no `fetch_from`. ADR-010 made it read-only/derived.
- The sync path already exists: `process_file_handlers._maybe_sync_manual_client_status`
  (on `on_update`, when the field changed) →
  `lifecycle_service.sync_process_file_client_status` →
  `status_service.update_tracking_status` (one log row per effective change,
  source = the Process File) → writes the canonical value back.
- Initial value already written today: `link_process_file_to_tracking` ends
  with `sync_tracking_status_to_process_file`, a `db.set_value` of the
  application's `current_status`.
- The derived recompute (`jobs.recompute_client_status`) runs only when
  `workflow_state` or `custom_form_submitted` really changes, and overwrites
  a manual value then (ADR-010 "Ops override becomes transient").
- The direct correction on the application (`correct_tracking_status`)
  requires a reason and the `Visa Tracker Manager` / `System Manager` role.
  No desk UI calls it.

### 2.3 `fetch_from` — what it can and cannot do (Frappe v15 source)

`BaseDocument._validate_links` (runs on every document save) fetches each
field whose `fetch_from` starts with a changed or present Link:

- **Without `fetch_if_empty`**, Frappe re-fetches on **every save**. A manual
  value would be overwritten by the application's status on the next save of
  the Process File. Not usable.
- **With `fetch_if_empty: 1`**, Frappe fetches only while the field is empty.
  This is the correct setting: it fills the initial value and then leaves
  staff edits alone. In Desk it also fills the field when the Link is set in
  the form.
- **Limit:** the Link is written server-side with `db.set_value` (ADR-014,
  `d59614f`), which does not run validation, so `fetch_from` does not fire
  on that path. The explicit `sync_tracking_status_to_process_file` at link
  time stays the primary initial write; `fetch_from` is the fallback for a
  Process File saved later with an empty status (for example one linked by
  hand).
- `fetch_if_empty` does not follow later changes on the application. Those
  already reach the Process File through `sync_tracking_status_to_process_file`.

So: `fetch_from: custom_visa_tracking_application.current_status`,
`fetch_if_empty: 1` — possible, useful as a fallback, not a replacement for
the explicit write.

### 2.4 Proposed design

1. **Field** (`the_visaguy` `fixtures/custom_fields.json`): `read_only: 0`,
   `fetch_from: custom_visa_tracking_application.current_status`,
   `fetch_if_empty: 1`. Keep `depends_on`, so the field stays hidden on
   older unlinked Process Files.
2. **Who can edit** — put the field on `permlevel: 1` and grant permlevel-1
   write on `PF Process File` to the chosen ops roles (Property Setter /
   Custom DocPerm fixture). Others see it read-only. (Decision M1.)
3. **Validate before save** — add a `PF Process File` `validate` handler that
   rejects an inactive or unknown status with a visible message. Today the
   sync runs in `on_update` inside `try/except → log_error`, so a bad value
   would save on the Process File and silently fail to reach the
   application.
4. **Status choices** — client script `set_query` on the field to active
   statuses only, in sort order.
5. **Sync** — reuse `_maybe_sync_manual_client_status`; record
   `changed_by = session user` and, if M3 says so, the reason. One log row
   per effective change (existing contract).
6. **Derived recompute** — keep ADR-010's transient override (recommended):
   a manual value holds until the next real workflow change. Show a short
   description on the field saying so. Alternative: a "manual lock" check
   that stops the recompute (decision M2).
7. **Dependant Process Files** — the public tracker shows a dependant the
   **primary's** status (temporary display override, ADR-010 amendment).
   A manual change on a dependant's Process File updates its own
   application but the client will not see it. Recommended: allow edits on
   primary Process Files only while the override exists (decision M4).
8. **ADR-010 amendment** — `custom_client_status` is editable again, with
   the rules above.

### 2.5 Work breakdown and tests

| Task (draft) | Repo | Scope |
|---|---|---|
| TASK-027 | `the_visaguy` | Field fixture change, permlevel + role grant, `validate` handler, client `set_query`, audit fields, tests, ADR-010 amendment. |

Tests: `fetch_if_empty` fills an empty field on save and never overwrites a
set one; an unrelated Process File save keeps a manual value; a manual
change appends exactly one log row and updates the application; an
inactive status is rejected in `validate`; a user without the role cannot
change the field; the next genuine `workflow_state` change still recomputes
(or not, per M2); dependant rule per M4.

Deployment: fixture change needs `bench migrate`. Check first that the
field exists on `visaguy` — risk 25 recorded it deleted on 2026-08-07.

### 2.6 Decisions needed

- **M1** Which roles may change the status on a Process File?
- **M2** Manual value: transient until the next workflow change (ADR-010,
  recommended), or locked until cleared?
- **M3** Require a reason for a manual change (as the application-side
  correction does)?
- **M4** Allow edits on dependant Process Files, given the client sees the
  primary's status?
- **M5** Visible to the client as a normal timeline entry (current default)?
