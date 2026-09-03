# Session Report — FileFlo Completed-Row Trigger, Full Applicant Names, and the `applicant_name` Rename

> Date: 2026-09-03
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Phase: Reconciliation of owner work done **outside** this workspace, plus
> one application change made in this session at the owner's explicit
> instruction (the wire-field rename).
> Repositories touched in this session: `the_visaguy` (bench checkout,
> `feat/visa-tracker`), committed as `05f8169` (Completed-row trigger) and
> `744ff6f` (full applicant name + rename); `visa_tracker`
> (`/Users/shzd/Projects/tridz/visa_tracker`, `main`), committed as
> `9e66484`. Nothing pushed, nothing deployed — both remain the owner's
> decision.

## 1. What this session was

The owner reported a set of visa-tracker changes made directly on the bench,
without going through the workspace, and asked for them to be verified and
recorded. Mid-session the owner then asked for an actual code change: the
applicant-name field, which had been unmasked but left under its old
`applicant_name_masked` key "for compatibility", was to be renamed properly
in both the API and the frontend.

Everything below was verified against source on the bench and in the local
frontend repository — none of it was taken from the summary alone.

## 2. Verified: what had already changed on the bench

### 2.1 Committed, and already recorded elsewhere in this workspace

| Repository | Commit | Change | Already recorded in |
|---|---|---|---|
| `fileflo` | `7bbfb9a` | generic post-persistence extension event | TASK-004 |
| `fileflo` | `c7244a4` | carry `field_id` onto multi-upload rows | feature README defect 1, risk 21 |
| `passport_extractor` | `0216829` | accept state-specific MRZ document subtypes (`PM`, `PD`, `PS`, `PP`) | feature README defect 3 |

### 2.2 Committed, and **not** previously recorded

`passport_extractor` `014a36e` — `run_passport_extraction` now sets
`frappe.set_user("Administrator")` for the job's duration and restores the
previous user in `finally`.

Root cause confirmed in source: the chain begins with a **guest** FileFlo
upload, so the enqueued job inherited `Guest`, who cannot write
`Passport Extraction`. The job could not leave `Queued` and could not save a
failure state either, so the production symptom was extractions sitting at
`Queued` indefinitely with nothing logged where anyone would look.

Recorded as ADR-004 "Amendment (2026-09-03)" and as a new entry in the
runbook's diagnostic order.

### 2.3 Uncommitted in the `the_visaguy` bench checkout

`git status` shows 10 modified files plus one untracked file,
`the_visaguy/visa_tracking/handlers/fileflo_collection_handlers.py`. Verified
line by line:

- **Trigger narrowed to `Completed` rows.** New `doc_events` on
  `FF File Collection File` (`on_update` gated on `status == "Completed"`
  **and** `has_value_changed("status")`; `after_insert` for a row created
  `Completed`). The handler stays inside ADR-004's synchronous boundary:
  settings predicate, `passport_field_ids` check, deterministic `job_id`
  `visa-tracking-fileflo-inspect::<collection>::<row>`, `is_job_enqueued`
  dedupe, `enqueue_after_commit=True`, no file access, and a blanket
  `except Exception: frappe.log_error(...)` so a handler fault cannot fail a
  staff member's save.
- **The inspection is a second gate.** `run_fileflo_inspection` skips any
  matched row whose status is not `Completed`, recording
  `{"action": "skipped", "reason": "ROW_NOT_COMPLETED"}`.
- **Backfill and report narrowed too.** `jobs.enqueue_missing_fileflo_extractions`
  and `reconciliation_service.reconcile_missing_extractions` both add
  `"status": "Completed"` to their `FF File Collection File` filters.
- **The FileFlo extension event is retained.** `hooks.py` still registers
  `fileflo_extension_handlers = ["the_visaguy.visa_tracking.jobs.enqueue_fileflo_inspection"]`.
  It still fires on every submission and is simply a no-op while the row is
  not `Completed`. Two enqueue paths now feed one idempotent inspection.
- **`applicant_display_name` is populated.** `lifecycle_service` sets it on
  create from the verified extraction's `given_names` + `surname`, and
  `_backfill_applicant_display_name` fills it on reuse with an
  `update_modified=False` `db.set_value`.
- **The name was unmasked** in `response_service.build_status_payload`, for
  the primary and for each `dependants` entry.

**A finding the summary did not mention, confirmed by grep across the whole
app:** before this change *nothing* had ever written
`applicant_display_name` — no service, no handler, no patch. The field was
always empty, so `mask_applicant_name` always hit its blank branch and the
public payload returned the placeholder `*****` as the applicant's name for
**every** application. The "unmask the name" change is therefore also the
change that made the name appear at all.

The dependant-race diagnosis (`FF_DOCUMENT_NOT_LINKED`,
`visa_tracking/utils/provenance.py:65`) was confirmed as a real code path.
The dropped fix — re-inspect on the document-link edge — leaves no trace in
the working tree, consistent with the owner's account that it was replaced
rather than layered on.

## 3. Done in this session: the `applicant_name_masked` → `applicant_name` rename

Owner instruction, mid-session. A key named `..._masked` carrying an unmasked
value is a lie in the contract; the rename removes it rather than explaining
it.

**Backend (`the_visaguy`, working tree):**
`response_service.py` — `STATUS_RESPONSE_KEYS`, `DEPENDANT_ENTRY_KEYS`, both
payload construction sites, and the module docstring; the two "key kept for
API compatibility" comments are deleted rather than reworded. Test
references updated in `test_response_service.py`, `test_public_api.py`, and
`the_visa_guy/doctype/visa_tracking_application/test_visa_tracking_application.py`.
`passport_number_masked` is untouched and still masked.

**Frontend (`visa_tracker`, working tree):**
`src/types/tracking.ts` (both `StatusResponse` and `DependantSummary`, with
the doc comments rewritten — they still claimed "masked by the server; the
SPA never receives the full value"), `src/test/contract/wireContract.ts`,
`src/components/tracking/StatusSummary.tsx`,
`src/components/tracking/DependantsList.tsx`, and the four test files that
key off the field.

**Two things in the frontend that the mechanical rename would have gotten
wrong, fixed deliberately:**

1. `applicant_name` was listed in `FORBIDDEN_STATUS_RESPONSE_FIELDS` — the
   set of keys the contract test asserts must **never** appear in a status
   response, where it meant "the unmasked name". Left in place, the contract
   suite would have failed on the very key the change introduces. It is
   removed, with a comment saying why.
2. The wire fixtures still carried masked sample values (`"J****e"`,
   `"S****h"`, `"A****n"`, and `"*****"` for the empty-optional case). They
   now carry full names, and the empty-optional fixture carries `""` —
   which is what the backend actually sends for a nameless application, and
   is a behaviour change worth having a fixture for (risk 32).

Stale prose was corrected alongside the rename rather than left to mislead:
`StatusSummary`'s "renders only server-provided masked values", the mocks
module's "values are ... already masked", and three test names that promised
a masked summary. The passport-number comments are untouched and still true.

**Blast radius check:** a grep for `applicant_name_masked` across every app
on the bench (`~/bench/apps`, excluding `.git`/`node_modules`) returns
nothing. `visa_tracker` was the only consumer, and both sides moved together.

## 4. Verification

| Suite | Result |
|---|---|
| `visa_tracker` `npm run verify` (oxlint + `tsc --noEmit` + vitest + build) | **64/64 green**, one pre-existing fast-refresh lint warning in `SessionContext.tsx`, build clean |
| `the_visaguy` pure tier (`python -m unittest discover -s the_visaguy/visa_tracking/tests`) | 274 run, **2 errors**, 20 skipped — both errors are `test_lifecycle_service.TestProcessFileHandler`, failing on `AttributeError: site` because they need a site context; unrelated to this change |
| `the_visaguy` on-site tier (`bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`) | **366 run, OK** — zero failures, zero errors |

A first attempt at the on-site tier was run **without** `--skip-test-records`
and aborted during test-record bootstrap with
`DoesNotExistError: DocType Company Print Options not found`. That was an
operator error, not a site defect: the runbook's "Test execution" section
already requires `--skip-test-records`. Recorded here because the failure
mode looks like a broken site and is not one.

## 5. What is not verified

- **Nothing is pushed or deployed.** All three repositories are committed
  locally only; push and deploy remain the owner's decision and neither was
  attempted.
- `visa_tracker`'s `.env.example` change (pointing the example API base URL
  at `visa.erpcode.tridz.in`) is the owner's, unrelated to this work, and was
  deliberately left uncommitted.
- No **live traffic** evidence for either change. The on-site suite is green
  at 366, but no real staff member has marked a real row `Completed` and been
  observed to produce an extraction, and no live HTTP smoke of the public
  status endpoint has run since the rename — the last wire-level probe is
  phase 09j, which predates it. On this feature specifically, four serious
  defects previously survived a fully green suite; 366 green is necessary,
  not sufficient (risk 33).

## 6. Workspace changes made

- New: `decisions/ADR-012-extraction-triggers-on-completed-file-row.md`.
- `ADR-004`: status narrowed by ADR-012; new "Amendment (2026-09-03)" for
  the Administrator elevation.
- `ADR-005`: status now records two narrowings; masking bullet amended; new
  "Amendment (2026-09-03): applicant names are returned in full", including
  the rename and the `FORBIDDEN_STATUS_RESPONSE_FIELDS` reversal.
- `ADR-010`: correction block on the dependant privacy-shape paragraph,
  which described the names as masked under the old key.
- `features/ongoing/visa-tracking/README.md`: the chain diagram now shows
  the `Completed` gate and the Administrator-run job; public information
  boundary amended; new "Changes made outside the workspace (2026-09-03)".
- `docs/operations/visa-tracking-runbook.md`: diagnostic order now starts
  with the `Completed` check, adds the two enqueue paths, the
  stuck-at-`Queued` guest defect, and a "tracker shows no name" step.
- `docs/risks-and-open-questions.md`: risks 31 (silent dependency on a
  manual staff action), 32 (empty applicant name), 33 (no on-site runtime
  evidence for this work).
- `docs/security-and-privacy.md`: new "Public visa tracker payload (FEAT-001)" section, giving the per-field treatment of the one surface that returns applicant PII to an unauthenticated caller.
- `TASK-004`: "Change note (2026-09-03)" — still completed, trigger edge
  moved.
- `TASK-007`: masking rule marked superseded.
- `TASK-017`: banner note that the wire field renamed under it.

## 7. Commits

| Repository | Commit | Scope |
|---|---|---|
| `the_visaguy` | `05f8169` | Completed-row trigger (ADR-012): hooks, the new `fileflo_collection_handlers`, inspection gate, backfill and reconciliation filters, tests |
| `the_visaguy` | `744ff6f` | full applicant name and the `applicant_name` rename (ADR-005 amendment): `lifecycle_service`, `response_service`, tests |
| `visa_tracker` | `9e66484` | frontend half of the rename, the `FORBIDDEN_STATUS_RESPONSE_FIELDS` removal, fixtures, and the corrected comments |

The two `the_visaguy` commits are split by concern rather than by when the
work happened: the trigger change and the name change are independent
decisions with independent ADRs, and a reader bisecting for either one
should not have to read the other.

## 8. Housekeeping finding

`ongoing/visaguy-crm-trigger-fix/repo/` is an 8.5 MB clone of the
`visaguy_crm` **application** repository sitting untracked inside this
workspace. `.agents/rules/project-rules.md` prohibits application code here.
It is untracked, so nothing has been committed, but it should be removed or
moved outside the workspace before anyone runs `git add -A`. Left in place —
deleting someone's working clone is not this session's call.
