# Session Report — ADR-011 (Unkeyed Public Lookup Hash) and Dependants Feature Commit

> Date: 2026-09-03
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Phase: Owner-driven design change (drop the keyed HMAC for the public
> lookup hash) plus recording the earlier dependant-status-display feature's
> commit. Workspace documentation correction pass only — no application
> code was written in this repository.
> Backend: `the_visaguy` on `feat/visa-tracker`, committed as `219907d`
> (unkeyed lookup hash) and, separately, `7ec522f` (the ADR-010
> "Amendment (2026-09-03)" dependant status-display feature from session
> 13). Suite **358/358** on the unkeyed-lookup-hash commit, verified by the
> owner's own runs.

## 1. What changed and why

`verification_lookup_hash` is no longer HMAC-keyed. It is now an unkeyed
hash (SHA-256) over the same canonical passport-number + DOB input.
`visa_tracker_lookup_hmac_key` is no longer required for the public lookup
and no longer needs configuring on any site before creating tracking
applications there.

**The reason is a corrected threat model, not a weakened one.**
`Passport Extraction` already stores, in the same database, in plaintext:
`passport_number`, `passport_number_normalized`, `date_of_birth`, `surname`,
`given_names`, `mrz_line_1`, `mrz_line_2`, and a pointer to the passport
file. Anyone able to read a leaked `verification_lookup_hash` column is, by
the same leak, able to read the plaintext passport number and DOB directly
off `Passport Extraction` — the HMAC key never added resistance to that
scenario. Earlier documentation (ADR-005's "HMAC lookup" subsection, and
corresponding passages elsewhere) implied the key protected against a
database leak; that implication was wrong and is corrected in the new ADR.

What the key cost, recurring: every site needed it configured **before**
any tracking application was created, or the resulting `NULL` hash forced
`tracking_enabled` to `0` and the application became silently unlookupable
— exactly the failure that broke `VTA-2026-00575` in practice.

What is retained: no second plaintext copy of the passport number on `Visa
Tracking Application`, which is readable by more people than `Passport
Extraction` (whose raw fields sit behind permlevel 1) — that property
depends on the hash being one-way, not on it being keyed.

A migration patch, `the_visaguy/patches/recompute_lookup_hash_unkeyed.py`
(registered in `patches.txt`), recomputes `verification_lookup_hash` for
every existing `Visa Tracking Application` from its linked `Passport
Extraction`. It migrates rows off the old keyed scheme and repairs
pre-existing `NULL`-hash rows in the same pass, is idempotent, and counts
and skips (rather than guesses at) any row with no resolvable extraction.

**Runtime proof:** with `visa_tracker_lookup_hmac_key` removed entirely
from `site_config.json`, the full verify -> status round trip passes end to
end.

`visa_tracker_lookup_hmac_key` is still consulted, with an existing
fallback, by two unrelated consumers — `rate_limit_service` (cache-key
bucketing) and the audit path (client-IP hashing). Neither requires the key;
removing a previously-present key changes their derived values going
forward, which harmlessly resets rate-limit counters and means audit rows
written under the old value no longer match a teardown filter keyed on it.

## 2. Workspace documentation changes made this session

- **`decisions/ADR-011-unkeyed-public-lookup-hash.md`** (new) — narrows
  ADR-005's "HMAC lookup" subsection; records the decision, the corrected
  threat model, the recurring per-site cost that motivated the change, what
  is retained, the recompute patch, and the runtime proof.
- **`docs/risks-and-open-questions.md`** — risk 22 rewritten and marked
  resolved, pointing at ADR-011; all three of its original claims (key
  unrecoverable, rotation silently invalidates every application, no
  recompute seam) are now wrong. Risk 26 (`visaguy_crm`'s unconditional
  `frappe.db.commit()`) updated: no longer theoretical — confirmed root
  cause of 811 `Contact`, 509 `Lead`, and 1 `Customer` synthetic rows
  surviving test rollback and colliding on the test site; three still-unfixed
  call sites named (`form_disable_via_pf_action.py`,
  `allocated_to_process_file.py`, `file_collection_from_lead.py`), all
  outside the two Lead customer-sync hooks already fixed in `visaguy_crm
  51f608e`.
- **`docs/operations/visa-tracking-runbook.md`** — corrected in all three
  places that required the key: "Required server-side configuration" (key
  is now optional, table and warning rewritten to describe what it still
  affects), "Updating a staging or live site" (manual per-site item
  rewritten), and "Rebuilding the dedicated test site" (key-generation step
  removed, subsequent steps renumbered). The "cannot be repaired in place"
  line in the diagnostic-order section was replaced with the
  patch-on-migrate behaviour. A new subsection documents the
  `recompute_lookup_hash_unkeyed` patch running automatically on `bench
  migrate`.
- **`ongoing/visa-tracking-implementation/10-task-010-planning.md`** —
  pre-rollout checklist item 9 (key configured on `visaguy`) rewritten to
  reflect that the gate no longer applies; §2 step 3 (migrate) now notes the
  recompute patch runs in the same `bench migrate` invocation.
- **`tasks/ready/visa-tracking/TASK-015-unscoped-assertion-audit.md`** — an
  "Extension (2026-09-03)" section added: `test_audit_rows_contain_no_pii`
  and `test_invalid_combination_matches_not_found_shape` in
  `TestPublicApiSecurity` still count `Visa Tracker Audit Log` rows globally
  and were not caught by this task's original sweep. Recorded as an
  extension of this task's scope, not a new risk, since it is test
  fragility rather than a product defect.

## 3. The dependant-status-display feature's commit (`7ec522f`)

Separately from the above, the ADR-010 "Amendment (2026-09-03)" dependant
status-display feature designed and implemented in session 13
(`13-session-2026-09-02-task-016.md`) — a primary applicant's public lookup
now also returns their dependants, and dependants display the primary's
status rather than their own — has been committed as `7ec522f`. This
session did not re-verify that feature's behaviour beyond confirming the
commit exists; see session 13 and ADR-010 for the full design, the
temporary-override rationale, and the removal condition.

## 4. Honest caveat — one unexplained, unreproduced test failure

A single test failure was observed in one of five consecutive full-suite
runs during this work. It could not be reproduced across nine subsequent
runs. The specific test name was not captured at the time and is not
recorded anywhere in this workspace or in the owner's own notes. This is
recorded here as an open, unresolved oddity — not dismissed as flake, not
elevated to a risk entry, because there is not enough evidence (no test
name, no reproduction) to characterise it as either. If it recurs, capture
the test name and the exact failure output before doing anything else.

## 5. Remaining actions, in order

1. TASK-016 and FEAT-001 remain **not** marked completed in this workspace
   — this session did not close either, consistent with standing practice
   of not closing on implementation evidence alone.
2. The rollout plan (`10-task-010-planning.md`) still requires committing
   and pushing the remaining uncommitted/unpushed work described in its §0
   and §1 before a `visaguy` deploy; this session's ADR-011 change is
   additional scope for that same eventual deploy, not a substitute for it.
3. TASK-015's extended scope (§2 above) should be picked up before TASK-015
   is considered done — the original sweep's twice-in-a-row validation run
   must also cover the two newly found tests.
4. TASK-018 (`visaguy_crm` unconditional commit) is unblocked and now has
   confirmed, named call sites to fix, per the updated risk 26.

## 6. TASK-017 moved to in-progress (frontend `title` + `dependants`)

`tasks/ready/visa-tracking/TASK-017-frontend-status-public-title.md` moved
to `tasks/in-progress/visa-tracking/` this session. Both halves of its
required behaviour are implemented in `visa_tracker`, on `main`, committed
but not pushed: `title` (commits `b25df4a`, `204f563`) and `dependants`
(commits `dc3ba23`, `f773f93` — a new `DependantsList` component rendering
one row per dependant, masked name / type / status-toned badge / that
entry's own title and message, nothing rendered when the array is empty).
`npm run verify` reported green by the owner: 64 tests across 9 files (up
from the 41-test baseline), lint clean bar one pre-existing unrelated
warning, typecheck clean, build succeeds. Full detail, including the
presentation rationale for the dependants list layout, is recorded in
TASK-017's own "Completion evidence (2026-09-03)" section.

Two outstanding checks kept the task at `in-progress` rather than
`completed`, matching this workspace's standing practice of not closing on
implementation evidence alone:

- **No human has visually verified the rendering.** `StatusPage` requires a
  live backend token to reach and MSW mocking is test-only in this repo, so
  the new `title`/`dependants` UI has never actually been looked at
  on-screen — only exercised through component tests against the wire
  fixtures. Flagged explicitly because this is a visual, design-sensitive
  change.
- **Deployment ordering.** The backend `dependants` payload
  (`the_visaguy` `7ec522f`, `219907d`, also committed-not-pushed) is
  additive/backward-compatible, but the frontend now consumes it, so the
  backend must deploy before the frontend. Neither is deployed, and the
  frontend itself is still unpushed on `visa_tracker` `main` (4 commits
  ahead of `origin/main`).
