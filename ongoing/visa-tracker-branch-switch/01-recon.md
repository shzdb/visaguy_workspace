# FEAT-001 Visa Tracking — Branch/Deploy Recon Log

Read-only recon performed via `ssh -p 2257 shahzad@erpcode.tridz.in`. No repository, bench,
or database write commands were executed. All findings below are raw command output or
directly derived facts.

---

## R1 — Bench app checkout state (`/home/shahzad/bench/apps/<app>`)

### the_visaguy
- Path exists: yes
- Branch: `main`
- HEAD: `e690b5b`
- Working tree dirty lines: `0` (clean)
- Local branch `feat/visa-tracker`: **exists** (`git branch --list` → `+ feat/visa-tracker`, the `+`
  indicates it's a worktree-checked-out branch elsewhere, i.e. linked to the worktree at
  `/home/shahzad/visa-tracker-worktrees/the_visaguy`)
- Remote branch `*feat/visa-tracker*`: none found
- Remotes:
  - `origin  git@github.com:tvgglobal/the_visaguy.git` (fetch/push)
  - `upstream  git@tridz:tvgglobal/the_visaguy.git` (fetch/push)

### passport_extractor
- Path exists: yes
- Branch: `develop`
- HEAD: `07b8cab`
- Working tree dirty lines: `0` (clean)
- Local branch `feat/visa-tracker`: **exists** (`+ feat/visa-tracker`, linked to worktree)
- Remote branch `*feat/visa-tracker*`: none found
- Remotes:
  - `upstream  git@tridz:tridz-dev/passport_extractor.git` (fetch/push)
  - (no `origin` configured)

### fileflo
- Path exists: yes
- Branch: `fix/mandatory-file`
- HEAD: `6683010`
- Working tree dirty lines: `0` (clean)
- Local branch `feat/visa-tracker`: **exists** (`+ feat/visa-tracker`, linked to worktree)
- Remote branch `*feat/visa-tracker*`: none found
- Remotes:
  - `upstream  git@tridz:tridz-dev/FileFlo.git` (fetch/push)
  - (no `origin` configured)

**Note:** the `+` prefix on `git branch --list feat/visa-tracker` in all three repos means the
branch ref exists in the repo but is currently checked out in a *different* worktree (the ones
under `/home/shahzad/visa-tracker-worktrees/`), not in the bench checkout itself. Each bench
checkout's actual current branch is `main` / `develop` / `fix/mandatory-file` respectively — none
of the three bench app checkouts currently have `feat/visa-tracker` checked out.

---

## R2 — Worktrees under `/home/shahzad/visa-tracker-worktrees/`

### the_visaguy
- Exists: yes
- Branch: `feat/visa-tracker`
- HEAD: `910914e`
- Dirty lines: `0`
- `git log --oneline -5`:
  ```
  910914e fix(visa-tracking): brace autoname formats and repair timeline NameError
  088430f test(visa_tracking): implement TASK-010 integration test bodies
  ccbd632 fix(visa-tracking): repair settings loader Single guard and enqueue job-id race
  4593a84 fix(visa-tracking): repair test isolation, friendly status uniqueness, stale skips
  28e58c0 fix: update test schema paths for moved visa tracking DocTypes
  ```
- Is worktree HEAD (`910914e`) an ancestor of bench checkout HEAD (`e690b5b`, branch `main`)?
  **NO** — `merge-base --is-ancestor` exit code `1`.
- Is bench checkout HEAD (`e690b5b`) an ancestor of worktree HEAD?
  **YES** — exit code `0`.
- **Interpretation:** the worktree branch is *ahead* of / diverged from `main` in a way where
  `main`'s current tip is contained in the worktree's history, but the worktree's feature commits
  are NOT in `main`. The feature branch has not been merged into `main`.

### passport_extractor
- Exists: yes
- Branch: `feat/visa-tracker`
- HEAD: `3486fcc`
- Dirty lines: `0`
- `git log --oneline -5`:
  ```
  3486fcc Fix OCR preprocessing: canvas-expanding rotation and raw-image candidates
  cbea215 Fix audit datetime comparison, repair pipeline test fixtures, PaddleOCR 3.x compat
  034f1c1 fix: harden MRZ and extraction error handling
  a13fa3c feat: add passport OCR and MRZ pipeline
  2f25c0d fix: enforce passport extraction invariants
  ```
- Is worktree HEAD ancestor of bench checkout HEAD (`07b8cab`, branch `develop`)? **NO** (exit `1`)
- Is bench checkout HEAD ancestor of worktree HEAD? **YES** (exit `0`)
- Same interpretation as above: feature commits not merged into `develop`.

### fileflo
- Exists: yes
- Branch: `feat/visa-tracker`
- HEAD: `fa1d6b3`
- Dirty lines: `0`
- `git log --oneline -5`:
  ```
  fa1d6b3 feat: add generic post-persistence extension event
  6683010 fix: if group mandatory file is uploaded, then it satisfies duplicate file uploads
  ffa9587 Merge pull request #55 from tridz-dev/feat/upload-again
  48a2604 update: display max file size in error message
  e9ab5c4 feat: handle file size, starxref error in file upload
  ```
- Is worktree HEAD ancestor of bench checkout HEAD (`6683010`, branch `fix/mandatory-file`)?
  **NO** (exit `1`)
- Is bench checkout HEAD ancestor of worktree HEAD? **YES** (exit `0`) — note bench checkout HEAD
  `6683010` is literally the second commit in the worktree's own log, confirming the worktree
  branch was forked from the bench checkout's current tip and has exactly one commit ahead
  (`fa1d6b3`) not yet present in `fix/mandatory-file`.

**Overall R2 conclusion:** in all three cases, the feature branch (`feat/visa-tracker`) commits
are NOT reachable from the corresponding bench app checkout's current branch. None of the
feature work has been merged/fast-forwarded into the branches actually checked out under
`/home/shahzad/bench/apps/`.

---

## R3 — Apps installed on PRODUCTION site `visaguy`

Command: `cd /home/shahzad/bench && bench --site visaguy list-apps`

```
frappe                 15.113.0  version-15
erpnext                15.106.0  version-15
hrms                   15.45.2   version-15
non_profit             0.0.1     develop
india_compliance       15.18.0   version-15
payments               0.0.1     version-15
helpdesk               0.10.0    modification_develop_branch
visaguy_crm            0.0.1     main
quick_kanban           0.0.1     main
insights               2.2.14    main
fileflo                0.0.1     fix/mandatory-file
processflo             0.0.1     develop
visaguy_hrms           0.0.1     main
crm                    2.0.0-dev tridz-dev
visaguy_frappe_crm     0.0.1     develop
visaguy_business       0.0.1     develop
visaguy_raven          0.0.1     develop
raven                  2.7.1     main
frappe_notifier        0.0.1     develop
visaguy_website        0.0.1     develop
otp_authentication     0.0.1     email
visaguy_helpdesk       0.0.1     develop
the_visaguy            0.0.1     main
frappe_whatsapp        1.0.12    master
waflo                  0.0.1     develop
frappe_conversions_api 0.0.1     develop
payment_integrations   0.0.1     develop
passport_extractor     0.0.1     develop
```

- `the_visaguy`: **present**, but listed on branch `main` (not `feat/visa-tracker`)
- `passport_extractor`: **present**, but listed on branch `develop` (not `feat/visa-tracker`)
- `fileflo`: **present**, but listed on branch `fix/mandatory-file` (not `feat/visa-tracker`)

All three apps are installed on production, but all three are pinned to the branch the bench
checkout currently has checked out — none is running the `feat/visa-tracker` code.

---

## R4 — Apps installed on test site `visa-tracker-test.localhost`

Command: `cd /home/shahzad/bench && bench --site visa-tracker-test.localhost list-apps`

```
frappe             15.113.0  version-15
passport_extractor 0.0.1     develop
erpnext            15.106.0  version-15
crm                2.0.0-dev tridz-dev
insights           2.2.14    main
processflo         0.0.1     develop
fileflo            0.0.1     fix/mandatory-file
the_visaguy        0.0.1     main
```

Note: `bench list-apps` reports the branch of the bench **checkout** (shared across all sites on
this bench), not a per-site branch — this matches the ground fact that the test site was migrated
"against the_visaguy @ 910914e" via a different mechanism (the app code was presumably swapped
in-place temporarily and/or migrated while the checkout pointed at the feature commit, then this
recon window catches the checkout back on `main`). The listed branch labels here reflect the
*current* state of the shared checkout, not necessarily the state active at migration time.

---

## R5 — Visa tracking DocType tables on PRODUCTION `visaguy` database

DocType directories found under
`/home/shahzad/visa-tracker-worktrees/the_visaguy/the_visaguy/the_visa_guy/doctype/`:

```
visa_tracker_audit_log
visa_tracker_settings
visa_tracking_application
visa_tracking_status
visa_tracking_status_log
```

Exact DocType `name` field (from each doctype's `.json`):
- Visa Tracker Audit Log
- Visa Tracker Settings
- Visa Tracking Application
- Visa Tracking Status
- Visa Tracking Status Log

DB credentials read from `/home/shahzad/bench/sites/visaguy/site_config.json` (`db_name`,
`db_type: mariadb`, `db_password` present) — read successfully, not reproduced here. Query
executed: `mysql -u <db_name> -p<db_password> <db_name> -e "SHOW TABLES LIKE 'tab<DocType Name>'"`
(SELECT/SHOW only, no writes).

| Table | Present on `visaguy`? |
|---|---|
| `tabVisa Tracker Audit Log` | **MISSING** |
| `tabVisa Tracker Settings` | MISSING (expected — see note) |
| `tabVisa Tracking Application` | **MISSING** |
| `tabVisa Tracking Status` | **MISSING** |
| `tabVisa Tracking Status Log` | **MISSING** |

**None of the visa tracking tables exist on the production `visaguy` database.** This is
consistent with R3 (production runs `the_visaguy` on `main`, which does not contain the feature
migrations) and R2 (feature commits not merged into `main`).

Note on `Visa Tracker Settings`: confirmed via its doctype JSON (`"issingle": 1`) that this is a
**Single** DocType. Single DocTypes do not get a dedicated table in Frappe — their data lives in
the shared `tabSingles` table — so "MISSING" here is the *expected* result even on a site where
the feature is otherwise installed (confirmed in R6 below, where it is also MISSING on the known
good test site while the other 4 tables exist).

---

## R6 — Visa tracking DocType tables on test site `visa-tracker-test.localhost` (comparison)

Same query, using credentials read from
`/home/shahzad/bench/sites/visa-tracker-test.localhost/site_config.json`.

| Table | Present on `visa-tracker-test.localhost`? |
|---|---|
| `tabVisa Tracker Audit Log` | **EXISTS** |
| `tabVisa Tracker Settings` | MISSING (expected — Single DocType, no dedicated table) |
| `tabVisa Tracking Application` | **EXISTS** |
| `tabVisa Tracking Status` | **EXISTS** |
| `tabVisa Tracking Status Log` | **EXISTS** |

This confirms the test site is indeed migrated with the feature schema (4/4 non-Single tables
present), and validates that R5's all-MISSING result on `visaguy` is a real absence of the
feature schema on production, not a query/credential problem.

---

## R7 — `apps.txt`

- `/home/shahzad/bench/sites/apps.txt`: **EXISTS**. Full contents:
  ```
  frappe
  visaguy_business
  erpnext
  visaguy_hrms
  visaguy_crm
  payments
  india_compliance
  visaguy_helpdesk
  insights
  employee_self_service
  the_visaguy
  waflo
  fileflo
  raven
  helpdesk
  crm
  visaguy_frappe_crm
  non_profit
  frappe_conversions_api
  quick_kanban
  payment_integrations
  mansico_meta_integration
  frappe_notifier
  visaguy_website
  passport_extractor
  frappe_whatsapp
  otp_authentication
  hrms
  processflo
  visaguy_raven
  ```
  All three apps (`the_visaguy`, `fileflo`, `passport_extractor`) are listed. Note: this file also
  lists `employee_self_service` and `mansico_meta_integration`, which did **not** appear in either
  `bench --site visaguy list-apps` or `bench --site visa-tracker-test.localhost list-apps` output —
  those two apps exist in the bench's global app registry but are apparently not installed on
  either of these two specific sites (not investigated further; out of scope for this recon).
- `/home/shahzad/bench/apps.txt`: **NOT FOUND**.

---

## GATES — post-task verification

Re-ran `git status --porcelain` on all 6 repos at the end of the session:

- `/home/shahzad/bench/apps/the_visaguy`: `0` lines (unchanged, clean)
- `/home/shahzad/bench/apps/passport_extractor`: `0` lines (unchanged, clean)
- `/home/shahzad/bench/apps/fileflo`: `0` lines (unchanged, clean)
- `/home/shahzad/visa-tracker-worktrees/the_visaguy`: `0` lines (unchanged, clean)
- `/home/shahzad/visa-tracker-worktrees/passport_extractor`: `0` lines (unchanged, clean)
- `/home/shahzad/visa-tracker-worktrees/fileflo`: `0` lines (unchanged, clean)

**Identical to the state observed at the start of the session (all clean, 0 dirty lines).**

No `git checkout/switch/pull/fetch/stash/merge` was run. No `bench migrate/install-app/build`,
`bench console`, or any other write command was run. No process on the shared host was
started/stopped/restarted. The `visaguy` production database was only read via `SHOW TABLES LIKE`
statements — no writes were made.
