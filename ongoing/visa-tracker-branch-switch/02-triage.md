# Phase 2 — Triage (orchestrator)

Input: `01-recon.md`. Spot-checks re-run independently by the orchestrator
(branch/SHA of all three bench checkouts, `bench --site visaguy list-apps`).

## What recon established (runtime-verified)

| Fact | Evidence |
|---|---|
| All 3 apps ARE installed on production `visaguy` | `bench --site visaguy list-apps` |
| None is on the feature branch | `the_visaguy=main@e690b5b`, `passport_extractor=develop@07b8cab`, `fileflo=fix/mandatory-file@6683010` |
| All 3 bench checkouts are clean (0 dirty lines) | `git status --porcelain` |
| `feat/visa-tracker` is NOT an ancestor of any checkout HEAD | `merge-base --is-ancestor` ≠ 0 both directions |
| Production `visaguy` has 0 of 4 visa tracking tables | read-only `SHOW TABLES` |
| Test site `visa-tracker-test.localhost` has 4/4 tables | same probe |
| Feature commits exist only in `/home/shahzad/visa-tracker-worktrees/*`, never pushed | prior handoff + recon |

## The blocking issue with the request as stated

"Switch the repos to the visa tracking branch so I can test on my main visaguy
site" is not a test action on this bench. It is a **production deployment**:

1. The bench imports app code directly from `/home/shahzad/bench/apps/<app>`.
   Checking those out to `feat/visa-tracker` changes the code path for every
   live `visaguy` user immediately — there is no per-site code isolation.
2. Making the feature usable also requires `bench migrate --site visaguy`,
   which writes the 4 tracking tables into the production database.
3. `erpcode.tridz.in` is a shared host; a broken checkout affects other people's
   sites on the same bench.
4. The commits are **unpushed local-only work**. Switching production onto a
   branch that exists nowhere but one worktree leaves no recovery path via the
   remote.
5. `the_visaguy` would move `main -> feat/visa-tracker`, carrying every other
   change on that branch into production, not just visa tracking.
6. FEAT-001 has one **open medium-high security finding** (rate-limit does not
   constrain DOB enumeration — `HANDOFF.md` §4), deliberately unfixed pending
   product sign-off.

## The alternative that needs no production change

`visa-tracker-test.localhost` on the same bench is already migrated at `910914e`
with 4/4 tables and configured settings, and the full suite is green there
(248/248 + 61/61 + 6/6 + 41/41 frontend). It is the intended test surface and
is ready to drive now.

## Decision required from the user

Whether to (A) test on the existing test site, (B) deploy to production
`visaguy`, or (C) something in between. Phase 3 stays blocked until answered.
