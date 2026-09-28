# Runtime verification and gap recon (2026-09-28)

Test site `visa-tracker-test.localhost` only. Nothing run on `visaguy` (owner tests it).

## Runtime smoke test (rolled back)

Real code path from a Process File save to a linked, status-correct application.
`frappe.enqueue` was captured (no worker jobs); OCR was simulated by writing a
`Needs Review` result onto the queued extraction; everything was rolled back.

| # | Check | Result |
|---|---|---|
| S1 | PF insert enqueues `ensure_tracking_job` (job id per file, short queue) | pass |
| S2 | `ensure_tracking` finds the `field_id = passport` Completed row, creates a Queued extraction (`source_field_id = passport`) | `extraction_queued` |
| S3 | Extraction in Needs Review | `needs_review` |
| S4 | `verify_extraction` → Verified, verified_by set, note has no values | pass |
| S5 | Application created; PF, Lead applicant row and application linked both ways; display name from the extraction | pass |
| S6 | `recompute_client_status`: Inprogress → `IN_PROGRESS`; PF Client Status synced | pass |
| S7/S8 | Re-run and desk Generate → `already_linked` with a plain message | pass |
| S9–S11 | Second applicant of the same Lead, same passport → no application, `duplicate_identity_in_lead`, one Error Log, none on re-run | pass |
| S12 | Rejected file → `excluded_state` | pass |
| S13 | Desk action as a user without the roles → PermissionError | pass |

Not exercised here: real OCR (no passport files on the test site; bench memory),
browser UI (buttons, dialogs, previews), a real worker run of the queued jobs.

## Gaps found

| # | Gap | Impact | Proposed action |
|---|---|---|---|
| G1 | TASK-035 coverage report not built. | No way to measure the soft launch. | In progress (phase 4). |
| G2 | `passport_field_ids` must contain `passport`. The test site had `passport_front` / `passport_back`. If production is not set, nothing is detected, silently. | Blocks the whole flow. | Owner sets it at deploy (plan Phase 2), or the TASK-036 patch appends `passport` when missing. Owner decision. |
| G3 | `Visa Tracker Settings.supported_extensions` is not read by any runtime code. The extractor enforces its own fixed list (pdf, jpg, jpeg, png; case-insensitive). | Misleading setting; no functional impact. | Later: wire it or hide it. |
| G4 | HEIC (iPhone) passports end `Failed` (unsupported type). Retry cannot fix them. | 4 of 25,191 passport files seen. | Staff ask for JPG/PDF. Later: convert HEIC, or make the Generate message say so. |
| G5 | ProcessFlo does not copy `field_id` into Process-File-stage collections. | A passport uploaded there is not detected. All 6,083 ready passports are in the Lead-stage collection. | Record as a risk; fix in ProcessFlo later if it occurs. |
| G6 | The public SPA work (TASK-017, TASK-025/026 case list) is still undeployed. | Clients with several cases need the case list. | Deploy backend then `visa_tracker` together with this release. |
| G7 | Private file preview for operations users on Passport Extraction depends on their read access to the file's FF Document. | Preview may show nothing for Ops. | Owner browser check as an Operations Associate. |
| G8 | Tracker link is not in any client message. | Needed before marketing only. | Plan: after D7. |
| G9 | The installed `the_visaguy` code is now merged; the `visaguy` site runs it on the next worker reload. `passport_extractor` is not installed there yet. | The save hook enqueues jobs that cannot run extraction. | Install `passport_extractor` and migrate `visaguy`, or keep `Visa Tracker Settings.enabled` off until then. |
| G10 | `application_closed` is never set automatically. | Later item in the plan. | None for soft launch. |
