# Visa Tracking Soft Launch — Implementation State

## Ground facts

- Scope: FEAT-001 soft-launch tasks TASK-031 to TASK-036
  (`tasks/ready/visa-tracking/`). Decisions: ADR-016 and its amendment,
  ADR-007 amendment, soft-launch plan D1–D4.
- Orchestrator: Claude (this session). Executor: Cursor CLI, run locally:
  `cursor-agent -p --force --trust --sandbox disabled --workspace <worktree> --add-dir <workspace> "$(cat prompts/<file>)"`.
  Cursor is not logged in on the bench, and the bench has no free memory
  (32 GB RAM used, 12 GB swap full), so executors run on the Mac.
- Local clones: `/Users/shzd/Projects/tridz/worktrees/visa-soft-launch/{the_visaguy,passport_extractor}`
  (remote `bench` = `erpcode:/home/shahzad/bench/apps/<repo>`). One local
  worktree per task under `.../visa-soft-launch/wt/<task>/`, branch
  `sl/task-0NN`, from `feat/visa-tracker`.
- Bench bases: `the_visaguy` `12ded1a`, `passport_extractor` `0febf6c`, both
  clean on `feat/visa-tracker`.
- Pure-tier baseline (`the_visaguy`, bench worktree, 2026-09-28): Ran 324,
  FAILED (errors=2, skipped=20); the 2 errors are the known
  `TestProcessFileHandler` site-context cases.
- On-site tier: `bench --site visa-tracker-test.localhost run-tests --app the_visaguy --skip-test-records`
  (last recorded 418 OK, 2026-09-14). Always scope with `--app`.
- Pushes go only into the bench's own repos (task branches). Never to
  `origin`. The owner deploys and pushes.

## Phase table

| # | Phase | Output | Status |
|---|---|---|---|
| 1a | TASK-036 field ID patch | `01a-task-036.md` | done `5f1cf81` (348 pure, 2 known errors); orchestrator spot-check OK |
| 1b | TASK-031 ensure tracking + manual actions | `01b-task-031.md` | done `e238e1f` (402 pure, 2 known errors); spot-check OK |
| 1c | TASK-033 extraction review actions (passport_extractor) | `01c-task-033.md` | done `cec7708` (25 new pure OK; doctype tier 37 with 2 baseline errors); spot-check OK |
| 1d | TASK-034 roles and permissions | `01d-task-034.md` | done `1d070d0` (incl. corrective 01d2); verified |
| 1e | TASK-032 desk layout and navigation | `01e-task-032.md` | done `07e7c73`; corrective 01e2 (PF field_order) IN PROGRESS (bg bopzo1n3d) |
| 2 | Orchestrator review of wave 1 | `02-review.md` | pending |
| 3 | Integration: merge into `feat/visa-tracker` on the bench, migrate test site, on-site suites | `03-integration.md` | pending |
| 4 | TASK-035 coverage report | `04-task-035.md` | done `3cb73cd`, merged `1118035`; report verified on test site |
| 5 | Runtime smoke test + gap recon | `05-runtime-verification-and-gaps.md` | done (13/13 pass; 10 gaps listed) |
| 6 | Final report | `06-final-report.md` | done |

## Decisions log

- 2026-09-28: Wave 1 runs five executors in parallel on separate branches,
  with a shared-file ownership table and two cross-task contracts (C1 retry
  helper, C2 outcome codes) in `prompts/00-common.txt`. TASK-035 waits for
  TASK-031 (it consumes C2). Integration and on-site tests are serial,
  because the test site imports the installed app checkout.
- 2026-09-28: 1a accepted. Spot-checked the bulk UPDATE (chunked, parameterized, empty-field_id guard, no saves) and the scan guards. Open: ProcessFlo `generate_file_collection_process_file` does not copy `field_id` from the template, so a passport uploaded to a Process-File-stage collection gets no field ID. Passports are in the Lead-stage collection in all 6,083 ready files, so this does not block; record as a risk.
- 2026-09-28: 1c accepted. Spot-checked verify_extraction (per-document write check, Needs Review only, normal save) and create_retry_extraction (Failed only, copies source fields, long queue after commit). DocType JSON: flags only.
- 2026-09-28: 1d reviewed: matrix correct, standard-row union present. Corrective 01d2: add System Manager to Visa Tracker Settings (existing Custom DocPerm rows already lock System Manager out). Operator write on Application kept; Desk User kept (D3).
- 2026-09-28: 1e reviewed: Custom Field chain correct, but PF Process File has a `field_order` Property Setter (45 fields, shipped by visaguy_hrms fixtures) that overrides insert_after, and custom_section_break_mw0ux shares the custom_form_submitted anchor. Corrective 01e2: after_migrate hook in the_visaguy that rewrites field_order idempotently.
- 2026-09-28: 1b accepted. Spot-checked: 3a guard runs after same-row reuse and before creation, flags once per Lead; save hook enqueue-only with job_id + deduplicate, wrapped in try/except; desk actions check roles server-side; Error Log dedupe keys on Error Log.method (= title in v15) + reference within 7 days. Accepted deviations: 6 extra outcome codes (no_source_lead, verified_not_linked, inspection_error, and three TASK-035 reasons), dependants resolved via custom_primary_process_file, review-flag dedupe per Lead.
- 2026-09-28: Phase 3 dispatch (cursor-agent --force with merge/migrate rights on the installed bench checkouts and test site) was denied by the Claude Code auto-mode permission classifier. Prompt is ready at prompts/03-integration.txt. Waiting for the owner to allow it or run it.
- 2026-09-28: Owner: merge and migrate the TEST site only; never run anything on `visaguy` (owner tests it). Patch may run on the test site. Integration done directly by the orchestrator. See 03-integration.md.
- 2026-09-28: TASK-035 merged (`1118035`); test-site migrate OK; the_visaguy on-site 638 OK; report reasons match ensure_tracking. Tasks 031–036 moved to in-progress (awaiting owner visaguy test and deploy).
- 2026-09-28: TASK-037 (HEIC message) merged `a318f8c`; on-site 657 OK. TASK-038 (realtime alerts) planned, blocked on owner Q1–Q3.
- 2026-09-28: TASK-038 (realtime alerts, owner Q1 none / Q2 roles / Q3 no headline) merged `b372f73`; on-site 719 OK. Found: cursor-agent adds `Co-authored-by: Cursor` to its commits (8 commits: tvg 1d070d0 96dadd4 924480e e238e1f 3cb73cd 07e7c73 d46364c; pe cec7708) because ~/.cursor/cli-config.json has attribution.attributeCommitsToAgent true. Nothing pushed. Owner decision pending on rewriting.
- 2026-09-28: Owner approved removing the `Co-authored-by: Cursor` trailer. On the bench, `git filter-branch --msg-filter` rewrote only commit messages from 12ded1a (the_visaguy) and 0febf6c (passport_extractor) to feat/visa-tracker; trees, authors, dates and subjects are identical; 0 trailers left. New heads: the_visaguy `b372f73`, passport_extractor `eb6684a`. Old commits kept under refs/original/ as a backup. All sl/* branches and task worktrees deleted on the bench and locally. ~/.cursor/cli-config.json attribution.attributeCommitsToAgent set to false (backup .bak-2026-09-28). Workspace SHAs updated to the rewritten ones.
