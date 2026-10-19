# Visa tracking: go-live checklist (merge to pilot)

Status: 2026-10-05. Owner runs every step. Decisions: ADR-016 (and amendment),
ADR-007 amendment, soft-launch plan D1–D4 and TASK-038 Q1–Q3.

## 0. Where the code is (2026-10-05)

| Repo | Branch | Head (pushed) | Change | Remote |
|---|---|---|---|---|
| `the_visaguy` | `feat/visa-tracker` | `80a5c3a` | Main feature app (TASK-005 … TASK-040) | `git@tridz:tvgglobal/the_visaguy.git` |
| `passport_extractor` | `feat/visa-tracker` | `316154e` | New app: OCR, MRZ, review actions | `git@tridz:tridz-dev/passport_extractor.git` |
| `fileflo` | `feat/visa-tracker` | `219c9aa` | Post-persistence event, `field_id` on multi-upload rows | `git@tridz:tridz-dev/FileFlo.git` |
| `visaguy_crm` | `feat/visa-tracker` | `df74c46` | Live upload path (`field_id`, extension event), no mid-save commits, no duplicate dependant rows | `git@tridz:tridz-dev/visaguy_crm.git` |
| `visa_tracker` | `main` | `654b9f0` | Public tracker SPA (case list, status page) | its `origin` |
| `processflo` | — | — | No change. The bench checkout has an unrelated uncommitted edit (`processflo/generate_file_collection.py`); do not deploy it by accident. | |
| `visaguy_frappe_crm` | — | — | No change. Uncommitted `fixtures/property_setter.json` on the bench; do not deploy it by accident. | |

Not part of the release: `frappe_conversions_api` was installed on the test
site only, so that `visaguy_frappe_crm` could install there.

## 0b. Merge status (2026-10-19, checked against GitHub)

| App | Live branch | Visa tracking work already merged | Still to merge |
|---|---|---|---|
| `the_visaguy` | `main` `3a11dad` | everything through TASK-041: `feat/visa-tracker` `fe91389` (incl. the static WhatsApp button fix) and `feat/visa-tracking-dashboard` `9882273` | tvgglobal/the_visaguy#47 (TASK-044 queue option) |
| `passport_extractor` | `main` `b8f41d8` | through TASK-040 (`316154e`) | tridz-dev/passport_extractor#5 (TASK-042 speed, TASK-043 MRZ recovery, TASK-044 queue) |
| `fileflo` | `main` `955e490` | `feat/visa-tracker` `219c9aa` | nothing |
| `visaguy_crm` | `main` `daa863e` | `feat/visa-tracker` `df74c46` | nothing |
| `visa_tracker` (SPA) | `main` `654b9f0` | case list for several applications | nothing |
| `waflo` | `develop` `c705be5` (only branch) | WhatsApp retry: 25 h spacing and 3-attempt cap (`1063e38`), chain-wide cap and 72 h age (`8d9c649`), webhook index (`d18e5d4`); all six `feat/waflo-correctness` commits are on `develop` as equivalent patches | nothing |
| `frappe_conversions_api` | — | no change for visa tracking | nothing |
| `processflo`, `visaguy_frappe_crm` | — | no change; the bench checkouts carry unrelated uncommitted edits, do not deploy them | nothing |

`the_visaguy` `develop` is 39 commits ahead of `main` with marketing and
insights work only; none of it touches visa tracking.

## 1. Before merging

- [ ] Owner test on `visaguy` finished: scenarios S01–S25
      (`07-soft-launch-plan.md`, Phase 3), browser checks (Process File section and
      buttons, toasts, Passport Extraction Verify dialog and preview as an
      Operations Associate, coverage report, timeline Open links).
- [ ] TASK-040 open items: a real WhatsApp send on a test zone with the approved
      Meta template and the button suffix; first save of an old file end to end.
- [ ] Meta template "Visa Tracking Update" approved (utility; body with applicant
      name and status name; URL button `https://<tracker-domain>/{{1}}`).
- [ ] Public wording of the `Visa Tracking Status` records reviewed (D6).

## 2. Merge

Order: `fileflo` → `visaguy_crm` → `passport_extractor` → `the_visaguy`; the SPA
after the backend is live.

- [ ] For each backend repo: merge its production branch into
      `feat/visa-tracker` first, resolve, and run the suites on the test site
      (`bench --site visa-tracker-test.localhost run-tests --app <app> --skip-test-records`;
      last results: the_visaguy 778 OK, passport_extractor 103 OK).
- [ ] Merge `feat/visa-tracker` into the production branch (no squash: the
      patches and fixtures history matters for review).
- [ ] Check no AI attribution trailers:
      `git log --format=%B <prod>..feat/visa-tracker | grep -ci co-authored` → 0.
- [ ] `visa_tracker`: `main` is the release branch; tag the release.

## 3. Production server preparation

- [ ] Full backup: database **and** private files.
- [ ] Risk 25 check before migrate: these Custom Fields exist —
      `PF Process File-custom_visa_tracking_application`,
      `PF Process File-custom_client_status`. (The Lead one is intentionally
      removed by TASK-039.)
- [ ] Python dependencies for `passport_extractor` in the bench env:
      `paddleocr>=3,<4`, `paddlepaddle>=3,<4`, `PyMuPDF>=1.24`,
      `opencv-python-headless>=4.8`, `Pillow>=10`
      (`bench setup requirements` after `get-app`, or `bench pip install -e apps/passport_extractor`).
- [ ] PaddleOCR models on the server before go-live (`~/.paddlex/official_models`:
      `PP-OCRv6_medium_det`, `PP-OCRv6_medium_rec`, `PP-LCNet_x1_0_textline_ori`).
      Run one extraction by hand to trigger the download if the server has internet.
- [ ] Memory: OCR uses about 1–2 GB per job; check free memory on the server.
- [ ] Workers: add a dedicated `long`-queue worker for OCR (G11: 1.5–9 minutes
      per file). Keep at least one worker for `short` / `default`, so tracking
      jobs, status recomputes and alerts are not blocked by OCR.
- [ ] Scheduler enabled (hourly status reconciliation sweep).
- [ ] socket.io running (desk toasts, TASK-038).

## 3b. Passport extraction queue (TASK-044, 2026-10-19)

The pilot is already live, so this is an update of a running site. OCR moves
from `long` to its own `passport_extraction` queue (2 workers, 1800 s).

1. [ ] Check free memory first: each OCR job uses about 1–2 GB, so two
       workers need up to 4 GB on top of today's use.
2. [ ] Deploy `passport_extractor` (TASK-042 + TASK-043 + TASK-044) and
       `the_visaguy` (TASK-044), then `bench --site <live> migrate`.
3. [ ] Check that `sites/common_site_config.json` now has
       `"workers": {..., "passport_extraction": {"timeout": 1800, "background_workers": 2}}`.
       The migrate prints a line when it adds it. If the key was missing, add
       it by hand with those values; an existing entry is never overwritten.
4. [ ] Production (supervisor): `bench setup supervisor`, then
       `sudo supervisorctl reread && sudo supervisorctl update`. Confirm
       `sudo supervisorctl status` shows a `…-passport_extraction-worker`
       group with two processes. (If the server uses a Procfile instead, add
       `worker_passport_extraction: bench worker --queue passport_extraction`.)
       Answer **no** if `bench setup supervisor` offers to overwrite custom
       changes you want to keep, and compare the new file first.
5. [ ] `bench build --app passport_extractor` (list view button), then
       `bench restart`. The restart kills any OCR job that is running; step 7
       picks those records up again.
6. [ ] Visa Tracker Settings → Queues → **Extraction Queue** =
       `passport_extraction`. Until a worker config exists, the code falls
       back to `long`, so this order is safe.
7. [ ] Passport Extraction list → **Requeue Pending Extractions** (System
       Manager). It first shows a dry run: jobs to move from `long`, records to
       restart (no running job), records running now (left alone). Confirm.
       Without the desk: `bench --site <live> execute
       passport_extractor.passport_extractor.extraction_queue.requeue_pending_extractions --kwargs "{'dry_run': 0}"`
       (run it once with `'dry_run': 1` first). It must run as a System
       Manager; with `bench execute` that is Administrator.
8. [ ] Watch: RQ Job list filtered on queue `passport_extraction`; Passport
       Extractions leave `Queued`; `long` no longer receives OCR jobs.
9. [ ] Optional speed-up from the TASK-042 benchmark: site config
       `passport_extractor_textline_orientation: 0` gave the same results on
       all 36 pilot files and cut the average from 77.6 s to 46.1 s.

Rollback: set Extraction Queue back to `long`. New uploads go to `long`;
jobs already on `passport_extraction` finish there while its workers run.

## 4. Deploy the backend

- [ ] `bench get-app` / pull: `fileflo`, `visaguy_crm`, `passport_extractor`, `the_visaguy`.
- [ ] `bench --site <live> install-app passport_extractor` (if not installed).
- [ ] `bench --site <live> migrate`. Read the patch output:
  - `set_passport_field_id`: template and collection rows updated (expect about
    223 template rows and about 37,000 collection rows on a site like `visaguy`);
    also the top unmatched "passport" labels — review them.
  - `link_tracking_applications_to_applicant_rows`: counts (risk 41).
  - `remove_lead_passport_extraction_field`, `backfill_application_passport_number_and_dob`,
    `remove_frontend_base_url_setting`: no errors.
- [ ] `bench build` (desk JS: client scripts, Passport Extraction and
      application form scripts), then `bench restart`.
- [ ] Never run `enqueue_missing_fileflo_extractions` or
      `reconcile_missing_extractions` without `collections` or `limit`
      (TASK-036 guard): after the patch they would queue OCR for every
      Completed passport.

## 5. Configure

**Visa Tracker Settings**

- [ ] `enabled` on, `enable_passport_extraction` on.
- [ ] `passport_field_ids` = `passport` (nothing is detected without it).
- [ ] `require_manual_verification` off (ADR-007 amendment).
- [ ] `inspection_queue` = short, `extraction_queue` = long.
- [ ] `default_lead_status`, `process_file_created_status`;
      `enable_process_file_created_transition` off (D9).
- [ ] `auto_create_tracking_application` on, `auto_link_verified_passport` on.
- [ ] `enable_public_tracking` on **only when the SPA is live** (step 6).
- [ ] Session, lockout and scope-lockout values (TASK-012), `status_history_limit`,
      `generic_failure_message`, `support_link`.

**Site config and other records**

- [ ] `allow_cors` in `site_config.json` includes the tracker origin (ADR-008, ADR-013).
- [ ] `Whatsapp Default` per pilot zone: `tracking_url` set; `notify_visa_tracking_updates`
      **off** until the pilot step that tests it; a `Visa Tracking Update` template row.
- [ ] Roles: fixtures sync the permissions (TASK-034, TASK-039). Assign
      `Visa Tracker Manager` to the people who change settings.
- [ ] `Visa Tracking Status` public titles and messages per D6.

## 6. Deploy the public tracker (`visa_tracker`)

- [ ] Build with `VITE_API_BASE_URL=<live site URL>` (see `.env.example`).
- [ ] Host on the tracker domain over HTTPS; the same origin as in `allow_cors`.
- [ ] Turn `enable_public_tracking` on.

## 7. Smoke test on live (before the pilot)

- [ ] One internal test file: mark the passport row Completed → extraction → linked
      application → status matches the workflow → toast on the open form.
- [ ] Public tracker: correct passport + DOB opens the case; wrong DOB five times
      gives the generic lockout message; a client with two cases sees the case list.
- [ ] Coverage report opens; Error Log has no new visa tracking errors.

## 8. Pilot (1–2 weeks, no marketing)

- [ ] Tracking is created as staff save Process Files (ADR-016). Optionally use
      **Generate Visa Tracking** on the pilot files.
- [ ] Send the tracker link by hand to the chosen pilot clients (D7), or turn on
      `notify_visa_tracking_updates` for one pilot zone.
- [ ] Daily: coverage report (open files tracked, counts per reason); Passport
      Extractions in `Needs Review` (verify within a working day) and `Failed`
      (Retry, or ask for a JPG/PNG/PDF if `unsupported_file_type`); Error Log;
      `long`-queue backlog and worker memory.

## Rollback

- `enable_public_tracking` off: the public API returns the generic failure.
- `Whatsapp Default.notify_visa_tracking_updates` off: no client messages.
- `Visa Tracker Settings.enabled` off: no new extraction or application;
  Process File saves are unaffected.
- Code rollback: redeploy the previous code. The patches change little data and
  are reversible without the backup:
  - `remove_lead_passport_extraction_field` deletes only the Custom Field
    definitions of the "Passport Extraction" link on Lead and CRM Lead. Frappe
    keeps the DB column and its values; re-creating a Custom Field named
    `custom_passport_extraction` shows them again.
  - `set_passport_field_id` only fills empty `field_id` / `field_id_link` with
    `passport` on passport rows; it can be cleared by an UPDATE.
  - `backfill_application_passport_number_and_dob` writes only the two new
    application fields.
  The step-3 backup is the safety net for anything else.

## Before marketing (not part of the pilot)

TASK-012 deployed and verified (D8), Rejected-file wording (D5), tracker link
in client messages (D7), decision on untouched open files (D10).
