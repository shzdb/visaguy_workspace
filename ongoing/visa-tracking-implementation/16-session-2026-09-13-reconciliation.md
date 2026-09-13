# Session Report — Reconciliation of Work Done Between 2026-09-03 and 2026-09-07

> Date: 2026-09-13
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Phase: Verify the workspace against the code, record what was missing,
> find gaps, merge the workspace branch to `main`.
> Application code changed in this session: none. One owner change was
> committed in `visa_tracker` (see §6). Nothing pushed, nothing deployed.

## 1. Repository state (verified 2026-09-13)

| Repository | Branch | HEAD | Tree | Against its remote ref (not re-fetched) |
|---|---|---|---|---|
| `the_visaguy` | `feat/visa-tracker` | `d59614f` | clean | equal to `upstream/feat/visa-tracker` |
| `fileflo` | `feat/visa-tracker` | `219c9aa` | clean | **4 ahead** of `upstream/feat/visa-tracker` (the `main` merge) |
| `passport_extractor` | `feat/visa-tracker` | `0febf6c` | clean | equal |
| `visaguy_crm` | `feat/visa-tracker` | `de7c959` | clean | equal |
| `visa_tracker` (local) | `main` | `49dd6b1`, then the §6 commit | clean after §6 | equal to `origin/main` before §6 |

Remote refs were not fetched, so "equal" means equal as of the last fetch.

Other bench apps have uncommitted changes that are not part of FEAT-001:
`insights`, `mansico_meta_integration`, `processflo`, `visaguy_business`,
`visaguy_frappe_crm`, `visaguy_raven`. They were not touched (risk 1).

## 2. Commits that were not recorded in the workspace

| Repository | Commit | Date | Change | Now recorded in |
|---|---|---|---|---|
| `the_visaguy` | `b99dea7` | 2026-09-03 | Process File ↔ tracking application linking by file collection; parent `FF File Collection` trigger; one inspection job per collection; `Visa Tracking Status` fixture | ADR-014, ADR-012 amendment, TASK-022 |
| `the_visaguy` | `d59614f` | 2026-09-07 | link written with `db.set_value(update_modified=False)`; fixes `TimestampMismatchError` in Lead conversion | ADR-014, TASK-022 |
| `visaguy_crm` | `de7c959` | 2026-09-07 | skip duplicate dependant rows on conversion re-run | TASK-023, risk 36 |
| `passport_extractor` | `0febf6c` | 2026-09-03 | PaddleOCR packages in `pyproject.toml` | feature README |
| `visa_tracker` | `6a76283`, `49dd6b1` | 2026-09-03, 2026-09-07 | header logo bar; iOS date input sizing | feature README |

Records that were stale and are now corrected:

- TASK-010, TASK-011, TASK-012 said the TASK-011/012/016 work was
  uncommitted. It is committed: `25e3186` (TASK-011), `53b0f28` (TASK-012),
  `e7167ff` + `7ec522f` (TASK-016).
- TASK-017 said `visa_tracker` was 4 commits ahead of `origin/main`. It was
  equal on 2026-09-13.
- Risk 33 said its two changes were uncommitted. They are committed.
- Risks 31 and 32 each existed twice. The second pair is now 34 and 35.
  Existing references to "risk 31" and "risk 32" all mean the first pair.

## 3. Verification run in this session

| Check | Result |
|---|---|
| `the_visaguy` pure tier | **286 run, 19 skipped, 2 errors.** Both errors are the known `TestProcessFileHandler` site-context errors. |
| `the_visaguy` on-site tier | **Did not run.** Redis Queue on the bench refused connections. The bench is shared; no process was started or signalled. |
| `visa_tracker` `npm run verify` | **64/64**, lint, `tsc`, and build clean. |
| Data on `visaguy` (read-only) | 4 of 3,875 Process Files linked; 4 of 11 applications have `process_file`; dependant child links all valid; 3 + 4 duplicate dependant groups. |

## 4. Gaps found

1. **Duplicate-row guard returns too early** (`visaguy_crm` `de7c959`).
   When the Process File detail row exists, the file-collection detail row
   is never checked or written. No test. Existing duplicates not cleaned.
   → TASK-023, risk 36.
2. **No backfill of Process File links.** Only new events link. 4 of 3,875
   linked. A wrong link is never re-resolved. → TASK-022, risk 37.
3. **Stale `hooks.py` comment** keeps the TASK-016 drift sweep unscheduled
   because "no PF Process File is linked". Now false. → TASK-022.
4. **No on-site evidence for `b99dea7` / `d59614f`.** → risk 38.
5. **`fileflo` `feat/visa-tracker` has 4 unpushed commits** (the merge of
   `main`). Push is the owner's.
6. **Executor transcript and app clones in `ongoing/`.** The clones
   (`multi-zone-whatsapp/*`, `visaguy-crm-trigger-fix/repo`,
   `waflo-correctness/worktree`) and `*.log` transcripts are now in
   `.gitignore`. They are left on disk.

## 5. Workspace changes

- New: `decisions/ADR-014-process-file-ownership-by-file-collection.md`.
- `ADR-012`: amendment for the parent-collection trigger.
- New: `tasks/in-progress/visa-tracking/TASK-022-link-process-file-to-tracking-application.md`,
  `TASK-023-skip-duplicate-dependant-rows.md`.
- `TASK-010`, `TASK-011`, `TASK-012`, `TASK-016`, `TASK-017`: dated updates
  for commit and push state.
- `features/ongoing/visa-tracking/README.md`: "Changes made outside the
  workspace (2026-09-03 to 2026-09-07)".
- `docs/risks-and-open-questions.md`: risk 1 and 33 corrected, 34/35
  renumbered, 36–38 added.
- `STATE.md`: ground facts and decisions log.
- `ongoing/process-file-tracking-link/PROMPT.md`: status note; passport
  number and DOB redacted.
- Added the untracked session records `ongoing/tracker-ui-polish/` and
  `ongoing/tracker-site-parity/` (without the raw transcript).
- `.gitignore`: app clones and executor logs.

## 6. Code committed in this session

`visa_tracker` `.env.example` — `VITE_API_BASE_URL` changed from the
placeholder to `https://visa.erpcode.tridz.in`. This is the owner's change;
session 15 left it uncommitted on purpose. Committed now on the owner's
instruction to commit uncommitted code. It is an example file with a public
URL, no secret.

## 7. Merge

`docs/feat-001-visa-tracking-implementation-record` merged into `main`
(fast-forward; `main` had no other commits).

`chore/workspace-audit-remediation` was **not** merged. It forked from the
same `main` and holds 27 commits of separate work (WhatsApp FEAT-002/003,
an audit of the visa tracking records dated 2026-08-06). A trial merge
conflicts in 9 files, and the branch reuses numbers already taken on
`main`: ADR-003 to ADR-009 name different decisions, and TASK-011 to
TASK-020 name different tasks. Its visa tracking status (SPA not started,
TASK-008 ready) is a month out of date. Merging needs a renumbering
decision from the owner.

## 8. What is left for FEAT-001

1. Re-run the on-site suite when Redis Queue is up (risk 38).
2. Fix the TASK-023 early return, add its test, decide on duplicate cleanup.
3. Decide on a Process File link backfill; revisit the drift sweep schedule.
4. Push `fileflo` `feat/visa-tracker`.
5. Deploy backend before frontend (TASK-017), then close TASK-010/011/012/
   016/017/022/023 on deployment evidence.
6. Open items carried forward: TASK-013 (blocked), TASK-014, TASK-015,
   TASK-018 (ready), risk 28 root cause, risk 34 recompute patch not run,
   risk 35 `allow_cors` decision, human visual check of the status page
   (TASK-017).
