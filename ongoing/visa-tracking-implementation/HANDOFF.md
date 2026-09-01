# FEAT-001 Visa Tracking — SUPERSEDED (handoff as of 2026-07-22, end of day)

> **SUPERSEDED 2026-07-23. Read `ongoing/visa-tracker-branch-switch/STATE.md`
> and the feature's "Implementation reality" section first.**
>
> Two statements in §8 below are WRONG and have already caused an execution
> agent to refuse an authorised task:
>
> - **"Site `visaguy` is production and READ-ONLY; never migrate or test against
>   it."** `visaguy` is a **development bench** (owner, 2026-07-23), served at
>   `https://visaguy.erpcode.tridz.in`. FEAT-001 is deployed and migrated there.
>   See ADR-006.
> - **"Synthetic data only ... never real passport data."** Scoped by the owner
>   on 2026-07-23 to shared and production sites. A real document was
>   deliberately retained on `visaguy`, which is the owner's own site. Synthetic
>   data remains the rule for automated tests and probes.
>
> The repository/branch table below is also stale — all five repositories have
> moved on. §4 (rate limiting) remains accurate and open; it is now tracked as
> TASK-012 and risk 18.


You are picking up an in-flight feature. Read this file first, then `STATE.md`
in this directory (the decisions log at the bottom is the authoritative
narrative). Everything below is verified fact, not assumption.

## 1. One-paragraph situation

FEAT-001 (public visa tracking + passport extraction) is **functionally complete
and fully green across every automated tier**, but it is **NOT closed**. All four
repositories have local commits that have **never been pushed**. One security
finding is open and needs a product decision before the feature should be called
done. Nothing is deployed.

## 2. Exact repository state (all local, NOTHING PUSHED)

| Repo | Location | HEAD | Tree |
|---|---|---|---|
| `the_visaguy` | remote worktree `/home/shahzad/visa-tracker-worktrees/the_visaguy` | `910914e` | clean |
| `passport_extractor` | remote worktree `/home/shahzad/visa-tracker-worktrees/passport_extractor` | `3486fccd` | clean |
| `fileflo` | remote worktree `/home/shahzad/visa-tracker-worktrees/fileflo` | `fa1d6b38` | clean |
| `visa_tracker` (frontend) | LOCAL `/home/shzd/Projects/tridz/visa_tracker` | `a6a07a9a` | clean |

All four are on branch `feat/visa-tracker` (frontend on its own default branch).
**Push and deploy remain unauthorized — that is the user's decision.**

## 3. Test status (every number below was independently re-verified by the coordinator, not taken from an executor's report)

- `the_visaguy` on-site: **248 ran / 248 pass / 0 skip / 0 errors**, stable across three separate runs.
- `passport_extractor`: **61/61**.
- `fileflo`: **6/6**.
- Frontend `visa_tracker`: **41/41**, lint + tsc + build clean.
- Live HTTP wire-contract smoke vs the frontend contract: **zero mismatches**.

## 4. THE ONE OPEN BLOCKER — read before closing anything

**Rate limiting does not constrain credential enumeration.** Medium-high,
design-level, deliberately NOT fixed.

`the_visaguy/visa_tracking/api/verification.py:102` sets
`target_bucket = candidates[0][0]` — the passport+DOB lookup hash — so
`rate_limit_service.build_client_key(origin_scope, source_ip, target_bucket)`
scopes the failure counter per *exact credential pair*.

Proven empirically over real HTTP against real Redis:
- 7x the **identical** wrong pair → locks out at attempt 6, `Retry-After: 900`. Works as designed.
- 7x the same passport with an **incrementing DOB** → **never locks out (0/7)**.

So an attacker who knows a passport number can enumerate DOBs (~36,500
candidates for an adult) from one IP unthrottled. Because every failure returns
a byte-identical HTTP 200, there is no client-visible signal that throttling is
absent — which is why the 248-test suite and a passing live lockout probe both
missed it.

**Do not "fix" this by removing the per-identity bucket** — that bucket is
deliberate and prevents an attacker locking a legitimate applicant out of their
own record. The recommended fix is to ADD a complementary coarser per-IP (and
optionally per-origin) counter with a higher threshold, evaluated alongside the
existing one. This needs a **TASK-007 amendment and product sign-off** first.

Full write-up: `09j-live-wire-contract-smoke.md`, Appendix C.

## 5. Also still open

- **E2E matrix item 19, browser leg.** Wire conformance is proven, but no real
  browser has ever rendered against the live backend.
- **Item 18 (human visual parity)** — already accepted provisionally by the
  project owner, with polish deferred. No action needed unless you want polish.
- **Workspace closure** — move TASK-002 and TASK-010 from
  `tasks/in-progress/visa-tracking/` to `completed/`, set FEAT-001
  `status: completed`. **Do NOT do this while §4 is open.**

## 6. Why this feature needed so many corrective phases (important context)

The feature was previously reported as "static gates green, runtime deferred,"
which read as nearly done. It was not. Runtime execution found **five** genuine
defects that a 197-test, fully-green static tier had completely missed —
because those tests mocked the very seams that were broken:

1. **Settings loader dead on every real site** (`table_exists` guard on a Single
   DocType) — the entire feature failed closed at runtime. Fixed, `ccbd6324`.
2. **`enqueue_passport_extraction` crashed on every extraction** (`job.id` on the
   `None` that `enqueue_after_commit=True` returns). Fixed, `ccbd6324`.
3. **Autoname collision** — unbraced `format:` strings meant only ONE row could
   ever exist per DocType per site. Fixed, `910914e`.
4. **`NameError` in `get_public_display_timeline`** — the public status endpoint
   failed for every real application. Fixed, `910914e`.
5. **The rate-limit enumeration gap** — still open, see §4.

**Lesson to carry forward: on this feature, a green static suite has been wrong
five times. Trust runtime evidence over in-process test counts.**

## 7. How to work here (conventions that are working)

- Pattern is orchestrator/executor (skill: `orchestrator-executor`). Every
  dispatched prompt is saved in `prompts/` and is re-runnable. Reports are
  numbered `NN-<phase>.md` in this directory.
- **Executor invocation:** `kimi -p "$(cat prompts/<file>)" --add-dir <workspace>`.
  Note `kimi -p` REJECTS both `--auto` and `--yolo` — do not add them.
  Claude Sonnet executors were used for security-sensitive or judgment-heavy
  fixes; Kimi for bulk/exploratory work. That split worked well.
- **Always give executors this rule:** if observed behavior disagrees with the
  contract, write the test to the contract, STOP, and report evidence — never
  edit application logic to make a test pass, never weaken a test to match a
  defect. This rule is what surfaced defects 1–4.
- **Review executor claims personally.** Mutation-testing the frontend privacy
  assertions and re-proving D1/D3 at runtime each caught things a report alone
  would have hidden.
- Before judging an executor stalled, **check whether its output report file
  exists** — a quiet stdout log is not proof of no progress (this misread
  happened on 2026-07-22).

## 8. Environment facts (verified — do not re-derive)

- SSH: `ssh -p 2257 shahzad@erpcode.tridz.in`. Bench `/home/shahzad/bench`.
  Use bare `bench` with an explicit `--site`. Never `which bench` /
  `bench --version` / `bench --help`.
- Dedicated test site: **`visa-tracker-test.localhost`** — fully migrated at
  `910914e`, settings configured, redis running. Site **`visaguy` is production
  and READ-ONLY**; never migrate or test against it. Original app checkouts and
  `processflo` are read-only.
- Worktree-first PYTHONPATH for every bench command:
  `PYTHONPATH=/home/shahzad/visa-tracker-worktrees/the_visaguy:/home/shahzad/visa-tracker-worktrees/fileflo:/home/shahzad/visa-tracker-worktrees/passport_extractor`
- the_visaguy suites need `--app the_visaguy --skip-test-records`.
- **`erpcode.tridz.in` is a SHARED host.** The `bench serve` processes running
  there belong to OTHER users (swafa, shahala, ameen, jezlan, vaishna, sanjusha,
  fathima, vyshnav). **Verify `ps` ownership is `shahzad` before killing
  anything.** This nearly caused an incident on 2026-07-22.
- To drive the live HTTP surface: start werkzeug on a free loopback port from
  `/home/shahzad/bench/sites` running `frappe.app:application`, then `curl` with
  an explicit `Host: visa-tracker-test.localhost` header. Stop it when done.
- Synthetic data only: `P0000000`, `1990-01-01`, `203.0.113.x`. Never real
  passport data.
- `.staging/` and `staging/` are gitignored app-source scratch space — 15MB of
  clones. Application code does not belong in this workspace.

## 9. Suggested next session, in order

1. Decide the §4 rate-limit question with the user; if approved, write the
   TASK-007 amendment, then dispatch the fix + a regression test that asserts
   the varying-DOB case now locks out.
2. Optionally close the browser leg of item 19.
3. Ask the user about pushing the four repositories (still unauthorized).
4. Only then run workspace closure (§5, third bullet).
