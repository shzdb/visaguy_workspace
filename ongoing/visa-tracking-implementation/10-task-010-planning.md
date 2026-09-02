# TASK-010 Rollout and Rollback Plan — FEAT-001 Visa Tracking

> Date: 2026-09-02 (rewritten; supersedes the 2026-07-22 version of this
> document in full — see "Superseded content" at the bottom)
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-010 — End-to-end verification and rollout
> Companion evidence: `ongoing/visa-tracking-implementation/11-task-010-evidence.md`
> Operational reference (do not duplicate — this plan sequences and
> decision-gates the same steps): `docs/operations/visa-tracking-runbook.md`

**This document is procedural only.** It does not authorize, schedule, or
perform any push, release, production migration, deployment, worker restart,
DNS/CORS change, or secret provisioning. Every step below requires explicit
human approval and execution outside this task (§8 of TASK-010; restated in
full in §7 below).

Evidence labels follow `AGENTS.md`.

---

## 0. What "rollout" means here, and why the previous version of this plan is void

The 2026-07-22 version of this plan assumed a rollout **to** `visaguy` had not
yet happened, scoped against a `the_visaguy` HEAD (`d20cc6d4`) that could not
even migrate. That premise is gone. Per ADR-006, the owner authorised, and
the project executed, a deploy of `feat/visa-tracker` to `visaguy` on
2026-07-22/23, and `visaguy` was reclassified from "production, read-only" to
**development bench**. Since then, further work (TASK-011, TASK-012,
TASK-016/ADR-010, a `main`-merge in two repositories) has been implemented,
tested, and left **committed-but-unpushed or fully uncommitted** — see the
table in §1. The rollout this plan now governs is therefore not "first
deploy to `visaguy`" but:

1. **Commit** the currently uncommitted work in `the_visaguy`.
2. **Push** the resulting branches (`the_visaguy`, `visaguy_crm`) to their
   remotes — closing the "unpushed commits" blocker TASK-010 has carried
   since 2026-09-01.
3. **Re-deploy** the updated `the_visaguy` (and, separately and later,
   `visa_tracker` once TASK-017 ships) to `visaguy`, which is already running
   an earlier point in the same feature branch.

Everything below is written against that reality. Nothing in this plan
authorises steps 1-3; it specifies the order and safeguards for when a human
decides to execute them.

---

## 1. Pre-rollout checklist

| # | Gate | Current state (2026-09-02) |
|---|------|-----------------------------|
| 1 | TASK-002 through TASK-009 implementation evidence reconciled | Pass — `11-task-010-evidence.md` |
| 2 | TASK-011 (auto-verification tests) | Implemented, mutation-proven, **uncommitted** in `the_visaguy` |
| 3 | TASK-012 (two-counter rate limiting, ADR-009) | Implemented, runtime-verified on the test site, **uncommitted** in `the_visaguy`, **not deployed** to `visaguy` — risk 18 stays live in reality until this deploys |
| 4 | TASK-016 (derived client status, ADR-010) | Implemented, 342/342, mutation-proven, **uncommitted** in `the_visaguy` |
| 5 | TASK-017 (frontend renders `title`) | In progress separately, **not included** in the current `visa_tracker a6a07a9` build |
| 6 | Repository state reconciled | See table below — this is the actual current state, superseding every earlier SHA table in this file and in TASK-010 |
| 7 | Dedicated-site runtime evidence | 342/342 (`the_visaguy`), 63/63 (`passport_extractor`), 8/8 (`fileflo`) on the rebuilt `visa-tracker-test.localhost` — see the runbook's rebuild recipe. Rebuild is now known to require `visaguy_crm` and `hrms` (risk 27); a rebuild that omits them produces a false-green suite |
| 8 | Human visual design-parity approval | Provisionally accepted 2026-07-22; beautification/polish deferred |
| 9 | `visa_tracker_lookup_hmac_key` configured on `visaguy` | **Already set and in active use** on `visaguy` (runbook §"Required server-side configuration") — this is a re-deploy, not a first deploy; **do not rotate this key** (risk 22 — no recompute seam, rotation silently invalidates every existing application's lookup) |
| 10 | `allow_cors` configured on `visaguy` | Already set; required per ADR-008 |
| 11 | Redis available, queues configured, workers running | `bench start` on `visaguy` is **currently NOT running** after a maintenance reboot — see §2 step 0, this is a hard precondition, not a post-step |
| 12 | PaddleOCR models preloaded | Runtime-verified present (user-level `~/.paddlex`, survives site operations) |
| 13 | Full backup of `visaguy` taken immediately before migration | Human step, mandatory before §2 |
| 14 | Rollback owner and approver identified | Human step — see §7.4 |

### Repository state (supersedes all earlier SHA tables in this document and in TASK-010)

| Repository | Deployed on `visaguy` | Local HEAD (`feat/visa-tracker`) | Gap |
|---|---|---|---|
| `the_visaguy` | `8254f93` | `4192e36` on disk, **plus TASK-011/012/016 uncommitted on top** | 1 pushed-but-undeployed merge commit + 3 tasks' worth of uncommitted work |
| `visaguy_crm` | `b573e2c` (approx., pre-merge) | `b492a34` | 1 unpushed merge commit |
| `passport_extractor` | `0216829` | `0216829` | none — in sync |
| `fileflo` | `c7244a4` | `c7244a4` | none — in sync |
| `visa_tracker` (frontend) | not deployed as a build artifact yet | `a6a07a9` on `main`, in sync with `origin/main` | TASK-017 not yet included |

**Practical consequence:** the single largest pre-rollout action is not a
schema or config step — it is committing TASK-011/012/016 in `the_visaguy`,
then deciding whether to push the resulting branch (and the already-pending
`visaguy_crm` merge commit) before or as part of the deploy. This plan takes
no position on that decision; it is the owner's per §0.

---

## 2. Order of app installs / migrations on `visaguy`

### Step 0 — restart `bench start` first, unconditionally

`bench start` is **not currently running** on `visaguy` after a maintenance
reboot. This must be confirmed running (and confirmed to be **our** process —
see shared-host safety below) *before* step 1, independent of anything this
rollout changes, because nothing below can be verified against a dead
process. This is also the step the runbook singles out as "the single most
common cause of 'the fix didn't work'" — `frappe.conf` and already-imported
Python modules are cached per process and are not refreshed by
`clear-cache` alone. Restart it again in step 5 after code lands; a restart
before deploying only proves the baseline is alive.

### Step 1 — pre-checks

1. Confirm `ps` ownership of any bench process is `shahzad` before touching
   anything (`erpcode.tridz.in` is shared with `anwar`, `safwan`, `jezlan`,
   `swafa`, `shahalakv`, `vaishna`, `vyshnav`, `sandra`, and others — runbook
   "Shared-host safety").
2. `bench --site visaguy backup` (§1 gate 13).
3. Confirm the commit/push decision from §0 has actually been executed —
   i.e. the code about to be deployed is the code that was reviewed.

### Step 2 — update code

Check out the landed revision of `the_visaguy` (and `visaguy_crm`, if that
merge commit is being pushed in the same window) at
`~/bench/apps/<app>` on the bench. `passport_extractor` and `fileflo` are
already at the revisions in the table above; no code update needed there
unless the owner separately decides to touch them.

### Step 3 — migrate

```
bench --site visaguy migrate
```

**This migrates every installed app on `visaguy`, not only the four FEAT-001
apps** — ADR-006 already recorded this as a known, accepted widening of
change surface for the 2026-07-22 deploy ("pending patches in `insights`,
`crm`, `raven`, `helpdesk`, `hrms` and others also ran; no adverse effect was
observed"). Treat that precedent as informative, not as a guarantee for this
run — a fresh `migrate` will pick up whatever has changed in those other
apps' checkouts since, which this task has not inspected.

This single `migrate` run applies both schema changes at once — there is no
way to sequence them independently within one `migrate` invocation:

- `Visa Tracking Status.public_title` (new field, ADR-010).
- `Visa Tracker Settings.scope_maximum_failed_attempts` and
  `.scope_lockout_minutes` (new fields, ADR-009). Both may be left unset
  after migration — their getters fall back to the safe defaults 20 and 60 —
  but confirm they exist as fields rather than assuming it.

Remember the field-add-to-Single hazard already surfaced during TASK-012
(ADR-009 "Consequences — Negative"): a newly added `Int` field on an existing
Single record reads back as `0`, not `None`, immediately after migration.
Verify the two new settings fields explicitly rather than trusting a
truthiness check.

### Step 4 — verify fixtures and custom fields

1. Confirm the 4 tracking tables exist with no drift, and the **new** six
   `Visa Tracking Status` fixture records replaced the old six (see §3 for
   exactly what this replacement means for existing data — read that before
   treating this step as done).
2. Confirm the three Custom Fields deleted 2026-08-07 (risk 25) —
   `Lead-custom_visa_tracking_application`,
   `PF Process File-custom_visa_tracking_application`,
   `PF Process File-custom_client_status` — are restored by fixture sync.
   This is a positive side effect of this deploy, not a separate step; verify
   it explicitly rather than assuming, since risk 25's root cause (an
   unfiltered fixture-reconciliation sweep) is still unexplained and could in
   principle recur.
3. Confirm `PF Process File-custom_client_status` is now `read_only: 1`
   (TASK-016) — this is a behaviour change for anyone who was hand-typing it
   in the desk UI; ops should be told before this lands, not after.
4. Confirm `PF Process File.workflow_state` and `custom_form_submitted`
   still exist as expected (owned by `visaguy_crm`, not `the_visaguy` — this
   deploy does not create them, it only starts reading them).

### Step 5 — restart `bench start` again

Mandatory, not optional, per the runbook. Restart after migration completes,
then run `bench --site visaguy clear-cache` and confirm the process is ours
before and after.

### Step 6 — queue workers

- Confirm the RQ worker(s) serving the default/short queue picked up
  `the_visaguy.visa_tracking.jobs.recompute_client_status` and the existing
  FileFlo inspection job — this requires the same `bench start` restart as
  step 5; a worker process is a long-lived Python process subject to the
  identical module-caching hazard.
- Confirm the long queue worker (PaddleOCR) is unaffected — no code in this
  deploy touches `passport_extractor`.
- **Updated 2026-09-02: there is no scheduler entry to confirm.** The
  hourly scheduler entry for `run_client_status_reconciliation_sweep` that
  TASK-016 originally wired into `the_visaguy` `hooks.py` has since been
  removed by owner decision (ADR-010 "Amendment (2026-09-02)"). Nothing
  runs the sweep automatically on this or any deploy. The functions
  (`jobs.run_client_status_reconciliation_sweep`,
  `services.reconciliation_service.repair_client_status_drift`) are still
  present and callable — see §3.3 for how to invoke them manually if
  desired.

### Step 7 — settings review, not blind carry-forward

`Visa Tracker Settings.default_lead_status` and `.process_file_created_status`
on `visaguy` currently point at codes from the **old** six-status set
(e.g. `APPLICATION_RECEIVED`, `WORKING_ON_APPLICATION` — see the runbook's
test-site table, which explicitly notes these are "superseded once TASK-016
lands"). After this migration those codes no longer exist as
`Visa Tracking Status` records. Update both settings to valid codes from the
new six (`QUESTIONNAIRE_NOT_SUBMITTED` … `ON_HOLD`) as part of this step, not
as an afterthought discovered by a failing lookup later.

---

## 3. What deploying actually changes (read before executing §2)

### 3.1 Schema changes

Two additive fields land in this migration: `Visa Tracking
Status.public_title` and `Visa Tracker Settings.scope_maximum_failed_attempts`
/ `.scope_lockout_minutes`. Both are backward-compatible additions — nothing
reads them until the new code that writes/consumes them is also live, which
happens in the same deploy.

### 3.2 The status records are replaced — what that means for existing rows

Six old codes (`APPLICATION_RECEIVED`, `DOCUMENTS_UNDER_REVIEW`,
`VERIFICATION_IN_PROGRESS`, `WORKING_ON_APPLICATION`, `APPLICATION_SUBMITTED`,
`UPDATE_SHARED_WITH_CLIENT`) are replaced by six new ones
(`QUESTIONNAIRE_NOT_SUBMITTED`, `QUESTIONNAIRE_SUBMITTED`, `FILE_ASSIGNED`,
`IN_PROGRESS`, `COMPLETED`, `ON_HOLD`). The owner has stated no data
migration is needed because these are development sites. In practice, on
`visaguy`, that means:

- Every existing `Visa Tracking Application` row's `current_status` Link
  field will point at a `Visa Tracking Status` name that **no longer
  exists** after this migration. Frappe does not enforce Link integrity
  retroactively on existing rows, so this does not itself break at
  migration time — but any code path that re-reads and re-validates that
  Link (a resave, a report, a future data-quality pass) will encounter a
  broken reference. The plan does not create fictitious rows to paper over
  this; it records the fact so it is not mistaken for a new defect on first
  encounter.
- The reconciliation sweep and the `on_update` hook (TASK-016) never
  **read** `current_status` off the old value to decide the new one — they
  compute forward from `workflow_state`/`custom_form_submitted` and write
  fresh. So every `Visa Tracking Application` linked to an active Process
  File will self-correct to a valid new status the first time its Process
  File is touched (or the next time someone runs the sweep manually — see
  §3.3, the sweep is no longer scheduled). Applications with **no** linked
  Process File (Lead-only stage) do not get touched by either path and will
  sit on a dangling old code until manually corrected or until a Process
  File is linked. In practice, per §3.3's verified figures, this affects
  essentially the whole current population of tracking applications (2
  total, both Lead-only), not a large fraction of 3,866 rows.
- `Visa Tracker Settings.default_lead_status` and
  `.process_file_created_status` must be updated in the same deploy window
  (§2 step 7) — leaving them pointing at deleted codes means every new
  Lead-only tracking application created after this deploy is created with a
  broken status reference from the start, which is a strictly worse outcome
  than the pre-existing dangling rows above because it is newly introduced.

### 3.3 Behaviour change at deploy — recompute on genuine change; the sweep is manual, not scheduled

**Updated 2026-09-02 — the risk this section originally described no longer
applies; see below for why and what replaces it.**

Once deployed, the `PF Process File` `on_update` hook begins enqueuing a
recompute job on every genuine `workflow_state` / `custom_form_submitted`
change, as designed. That part of this section is unchanged.

The rest of this section originally assumed an hourly
`run_client_status_reconciliation_sweep` scheduler entry would begin
repairing drift across the whole `PF Process File` table unattended, and
built a mitigation around that: disable the scheduler entry after deploy,
run the sweep once manually under observation, spot-check results, then
re-enable the entry. **That entire mitigation is now moot and has been
removed.** The owner removed the scheduler entry itself from `the_visaguy`
`hooks.py` on 2026-09-02 (ADR-010 "Amendment (2026-09-02)") — there is no
scheduler entry left to disable, observe-then-re-enable, or otherwise
manage as part of this rollout. An operator following the old three-step
mitigation literally would be disabling a scheduler entry that no longer
exists.

**The actual position, as of this deploy:**

- Nothing scheduled runs the sweep on this or any future deploy. The sweep
  (`jobs.run_client_status_reconciliation_sweep`) and the underlying repair
  function (`services.reconciliation_service.repair_client_status_drift`)
  remain present and callable, but only by explicit manual invocation:

  ```bash
  # read-only report of diverging PF / tracking-application pairs
  bench --site visaguy execute the_visaguy.visa_tracking.services.reconciliation_service.reconcile_status_mismatches

  # cautious repair, bounded
  bench --site visaguy execute the_visaguy.visa_tracking.services.reconciliation_service.repair_client_status_drift --kwargs "{'limit': 20}"

  # full sweep
  bench --site visaguy execute the_visaguy.visa_tracking.jobs.run_client_status_reconciliation_sweep
  ```

- **The blast radius this section originally worried about (an unattended
  hourly sweep against ~3,866 Process Files) was in any case zero**, not
  merely mitigated. Verified live on `visaguy`: 3,866 Process Files exist,
  but **zero** are linked to a Visa Tracking Application and **zero** have a
  client status set — only 2 tracking applications exist at all, both from
  the Lead-stage passport chain. A sweep run today, scheduled or manual,
  would scan the table and find nothing to repair. There was never a
  first-run performance or correctness event to protect against at this
  deploy; the earlier estimate that thousands of records would be rewritten
  on deploy was wrong — the correct figures are the ones just stated (0
  linked Process Files, 0 with a client status, 2 tracking applications).
- If an operator wants to run the sweep as part of this rollout anyway
  (e.g. to confirm it behaves correctly against live data, given the
  current near-empty result set), that is optional, not required, and
  produces negligible load precisely because there is almost nothing for it
  to act on yet. `reconcile_status_mismatches()` is strictly read-only and
  is the safe first step if this is attempted.
- When Process Files begin actually flowing through the stage model at
  volume (i.e. tracking applications get linked and client statuses get
  set at real scale), reinstating the scheduled sweep becomes worth
  revisiting — at that point, and only then, does something resembling the
  original hourly-sweep-at-scale risk this section described become
  relevant again, and a mitigation plan like the original one should be
  reconsidered.

### 3.4 The rate-limit fix goes live (risk 18)

Risk 18 (DOB enumeration via the per-identity-only counter) closes only when
TASK-012 is committed **and** deployed. This deploy is that deploy. After
step 5-6 of §2, re-run the runbook's post-deploy CORS/lockout smoke check
and additionally confirm the per-IP scope counter trips (20 failures/hour →
`Retry-After` reflecting the greater of the two counters) — this was
runtime-verified on the test site only; it has never been proven against
`visaguy`.

### 3.5 Fixture sync restores three Custom Fields (risk 25, positive side effect)

Covered in §2 step 4.2. Verify it; do not assume it.

### 3.6 Frontend `title` field — ordering constraint with TASK-017

The backend change in this deploy (`public_title` on `Visa Tracking Status`,
`title` added to the public API payload — both at top level and per timeline
entry, per the exact shape recorded in session 13) is **backward-compatible**
on its own: it adds a field to a JSON response that the currently-deployed
frontend (`visa_tracker a6a07a9`) does not read. The current frontend will
continue to work unmodified after this backend deploy, ignoring the new
field.

The frontend change (TASK-017, not yet implemented) is **not**
backward-compatible in the other direction: once the frontend is built to
consume `title`, it requires the backend to already be serving it. Therefore:

- Backend can deploy **before** frontend, safely, with no frontend change
  required in the same window.
- Frontend must **never** deploy before backend once TASK-017 lands — doing
  so would ship a frontend expecting a field the live backend does not yet
  send.
- These two deploys do not need to be simultaneous, but they are not
  interchangeable in order. Backend-first is the only safe sequencing.

---

## 4. Fixture and custom-field steps

Covered inline in §2 step 4 (verification) and §3.2/§3.5 (what changes and
why). No additional fixture action beyond what `bench migrate` performs
automatically via `the_visaguy/hooks.py`'s fixture list (`Custom Field`,
`Property Setter`, `Client Script`, `Role`, `Custom DocPerm`,
`Visa Tracking Status`) — per the runbook, Frappe v15 imports every `*.json`
in the app's `fixtures/` folder regardless of the hooks.py list, and every
fixture record must carry `name`/`modified` or the whole migration aborts.

---

## 5. Queue worker restart requirements

Restated from §2 steps 5-6 because this is the single most-repeated failure
mode in this project's own history (the runbook calls it out explicitly, and
ADR-006/session records corroborate it): `bench start` restart is required
**after** migration, not merely recommended, because:

- `frappe.conf` — and therefore any newly set `site_config.json` key — is
  cached per long-lived process.
- Already-imported Python modules (including the new `status_resolution.py`,
  the new job functions, and the modified `response_service.py`) are not
  reloaded by `clear-cache` alone.
- The werkzeug reloader did not reliably respawn on edit in practice on this
  bench — a stale long-lived serve process with a newer `.py` than its
  `.pyc` is the signature symptom.

This applies identically to the RQ worker processes, not only the web
process — a worker that has already imported the old `jobs.py` will keep
running the old code until it, too, is restarted.

---

## 6. Frontend deployment artifact handoff

- Current artifact: `visa_tracker a6a07a9` on `main`, in sync with
  `origin/main`. This build does **not** include TASK-017 and is safe to
  deploy independently of the backend changes above (§3.6).
- When TASK-017 ships, the new artifact must not be deployed until the
  backend steps in §2 have completed on the target site — see §3.6 ordering
  constraint.
- No deployment target, CDN, or static-host decision has been made for
  `visa_tracker`; this remains a human infrastructure decision outside this
  task's scope, unchanged from the 2026-07-22 version of this plan.

---

## 7. Post-rollout smoke tests

Run these against `visaguy` after §2 completes, using only synthetic data
(`P0000000` / `1990-01-01` / `203.0.113.x` per the runbook), before
considering the rollout complete:

1. **Runbook's own post-deploy check** — table count (4), fixture count (6,
   confirm they are the **new** six codes, not the old ones), single CORS
   header via the curl probe.
2. **New-field check** — confirm `Visa Tracking Status.public_title` is
   populated for all 6 rows (not blank) and `Visa Tracker
   Settings.scope_maximum_failed_attempts` / `.scope_lockout_minutes` read
   back as expected (watch for the `0`-vs-`None` Single-field hazard noted
   in §2 step 3).
3. **Settings sanity** — `default_lead_status` and `process_file_created_status`
   resolve to valid, existing `Visa Tracking Status` names (§2 step 7, §3.2).
4. **Derived status, single record** — touch one real (non-synthetic
   preferred: pick a low-risk existing) Process File's `workflow_state` or
   `custom_form_submitted` in a way that constitutes a genuine change, and
   confirm exactly one new `Visa Tracking Status Log` row is created with a
   status from the new six, without recursion.
5. **Sweep, manual invocation (optional)** — per §3.3, there is no scheduler
   entry to re-enable; the sweep only ever runs when invoked by hand. If
   exercising it as part of this smoke test, run
   `reconcile_status_mismatches()` first (read-only), then, if desired,
   `repair_client_status_drift` or the full sweep, and confirm the result is
   consistent with the verified figures in §3.3 (0 linked Process Files, 0
   client statuses set, 2 tracking applications) — a large repair count
   here would itself be a signal something in those figures has changed and
   should be investigated before trusting the rest of this rollout.
6. **Rate limit, per-IP scope** — repeat the enumeration-style probe from
   ADR-009's proof (same passport, incrementing DOB) against `visaguy` and
   confirm it now locks out around attempt 21 with the correct
   `Retry-After`, closing risk 18 in reality (not just on the test site).
7. **Custom fields restored** — confirm the three Custom Fields from risk 25
   render correctly in the desk UI on `Lead` and `PF Process File`.
8. **`custom_client_status` read-only** — confirm ops can no longer hand-type
   it in the desk UI, and that this is communicated to ops before, not
   discovered by them after.
9. **End-to-end public lookup** — one fresh synthetic application created
   post-deploy, looked up publicly, confirming the whole chain (already
   runtime-verified once on 2026-08-01 pre-TASK-016; re-prove post-deploy
   since the status codes and payload shape have both changed).

---

## 8. Rollback plan

### 8.1 Feature disable — fastest kill switch, no data loss

The feature fails **closed** by design (runbook: `is_public_tracking_enabled()`
requires both `enabled` and `enable_public_tracking`; `lifecycle_service.py:192`
no-ops the Customer/PF Process File hooks on the same guard). This makes
disabling the two settings fields the fastest possible rollback, and it is
the recommended first response to any post-deploy problem before considering
code reversion:

1. `Visa Tracker Settings.enabled = 0` — stops FileFlo inspection,
   extraction orchestration, and **all** lifecycle automation including the
   TASK-016 hooks. The sweep itself is no longer scheduled (§3.3) so there
   is no unattended sweep run to worry about disabling; this guard still
   matters for anyone who manually invokes the sweep during or after
   rollback — the sweep's job body should itself check the guard before
   writing, confirm this at rollback time rather than assuming.
2. `Visa Tracker Settings.enable_public_tracking = 0` — public APIs
   immediately return the constant generic failure; no schema or data is
   touched.
3. No `Passport Extraction`, `Visa Tracking Application`,
   `Visa Tracking Status Log`, or `Visa Tracker Audit Log` row is modified or
   deleted by this step. Re-enabling resumes normal operation from wherever
   state was left.
4. This step alone does **not** address §8.3 below (dangling old status
   codes on rows created before rollback) — it only stops new writes.

### 8.2 Code reversion per app

Frappe migrations are forward-only; DocTypes/tables/fields created by this
deploy remain in the database after a code revert. Reverting code means
restoring each repository to a prior revision on the bench and running
`bench migrate` only after a verified backup:

| Repository | Revert target | Note |
|---|---|---|
| `the_visaguy` | `8254f93` (the pre-TASK-016/012/011 revision currently live on `visaguy`) or further back to `e690b5b` (pre-feature `main`) if a full feature rollback is required | See §8.3 for the specific hazard of reverting past ADR-010 |
| `visaguy_crm` | the pre-merge revision currently live (`b573e2c` approx.) | Reverting this also reverts unrelated content merged in from `main` (WhatsApp multi-zone, PF process file timer, insights work) — confirm with those workstreams' owners before reverting past this point, since this repository is shared beyond FEAT-001 |
| `passport_extractor` | `07b8cab` (scaffold) or uninstall the app | Unchanged since the 2026-07-22 plan; not touched by TASK-011/012/016 |
| `fileflo` | `6683010` | Unchanged since the 2026-07-22 plan |

### 8.3 Reverting `the_visaguy` past ADR-010 specifically

If code reversion targets a `the_visaguy` revision **before** TASK-016
(i.e. before the new six status codes and `resolve_client_status` existed),
every `Visa Tracking Application` row created or updated **after** the
forward deploy will reference status codes (`QUESTIONNAIRE_NOT_SUBMITTED`
etc.) that the reverted code and its status fixtures no longer define. This
is the mirror image of §3.2's forward-deploy hazard, and it is handled the
same way:

- The reverted code does not itself crash on a dangling Link value — Frappe
  does not re-validate existing Link fields on unrelated reads.
- Any report, resave, or the old (reactivated) hand-typing workflow that
  tries to display or re-set `current_status` against the old fixture set
  will not recognise the new codes and will need manual data correction —
  either restoring the six new `Visa Tracking Status` rows as **inert**
  records (so old code's Link validation passes even though nothing writes
  to them anymore) or accepting broken display for rows created during the
  forward-deployed window until they are manually corrected.
- **Recommended approach if this scenario is reached:** do not delete the
  six new `Visa Tracking Status` records as part of a code revert. Leave
  them in place (inert, unreferenced by reverted code, harmless) so that
  rows already pointing at them keep resolving. This avoids compounding one
  rollback with a second round of broken references.
- This is exactly why §8.1 (disable, not revert) is the preferred first
  response — it avoids this hazard entirely by never running the old code
  against post-TASK-016 data at all.

### 8.4 Redis session and rate-limit key clearing

To reset abuse/lockout state or invalidate all public sessions:

- Delete `visa_tracker:session:*` — invalidates all public SPA sessions;
  users must re-verify.
- Delete `visa_tracker:failed:*` — lifts per-identity lockouts and resets
  that counter.
- Delete `visa_tracker:failed_scope:*` — **new key family from ADR-009**;
  lifts per-IP-scope lockouts and resets that counter. Clearing only the
  original `failed:*` family and forgetting this one leaves the new per-IP
  lockout in effect even after an operator believes they have cleared all
  rate-limit state — call this out explicitly to whoever executes rollback,
  since the two-counter design is new since the last time anyone on this
  project cleared these keys.
- All keys are namespaced and contain only HMAC buckets, never raw
  passport/DOB/IP values — deletion is safe and non-exposing.

### 8.5 Approval authority

- Feature disable/enable (§8.1): operations owner + project owner.
- Redis key purges (§8.4): bench administrator with project-owner approval.
- Code reversion / site restore (§8.2-8.3): project owner approval, executed
  by the bench administrator, only after confirming the pre-migration backup
  from §1 gate 13 exists and is restorable.
- Any decision to revert `visaguy_crm` past its pending merge commit (§8.2):
  additionally requires sign-off from whoever owns the unrelated WhatsApp
  multi-zone / PF process file timer / insights work merged into that same
  commit, since reverting it affects them too.

---

## 9. Explicit non-authorisations

This plan does **not** authorise or perform: any git commit, push, merge, or
release; any production migration or app installation; any deployment or
static-host change; any worker restart; any DNS or CORS change; provisioning
or recording of any secret value; any rotation of
`visa_tracker_lookup_hmac_key`; or any use of real passport or production
data. It is a documented procedure for human approval and execution outside
this task, per TASK-010 §8.3. Everything in §0-§8 above describes what
*would* happen if and when the owner authorises each step — it authorises
none of them by existing.

---

## Superseded content

The version of this document dated 2026-07-22 assumed FEAT-001 had not yet
been deployed anywhere and was blocked on a `the_visaguy` migration defect
that has since been fixed and superseded twice over (by the 2026-07-22
deploy itself, and by TASK-011/012/016 since). Its SHA tables, its "current
state" checklist, and its rollback targets are all stale and have been
replaced in full above. It is not reproduced here; see version control
history for the prior text if needed.
