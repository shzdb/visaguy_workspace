# Visa Tracking (FEAT-001) Operations Runbook

Evidence labels follow `AGENTS.md`. Everything below is **runtime-verified** on
bench `/home/shahzad/bench`, site `visaguy`, unless stated otherwise.

## Required server-side configuration

These are prerequisites, not optional tuning. The feature fails **silently** —
no error, no log — when they are absent.

| Key | Location | Required | Consequence if missing |
|---|---|---|---|
| `visa_tracker_lookup_hmac_key` | `sites/<site>/site_config.json` | **Yes** | `verification_lookup_hash` is never computed, so `tracking_enabled` is forced to `0` and **every public lookup fails** with the generic failure message. This exact gap broke `visaguy`. |
| `visa_tracker_audit_hash_key` | `sites/<site>/site_config.json` | No | Falls back to the lookup HMAC key for hashing client IPs in audit records. |
| `allow_cors` | `sites/<site>/site_config.json` | **Yes** | With ADR-008 the application no longer emits CORS headers. Removing this breaks **every** browser client of the tracker. |
| `visa_tracker_allow_localhost_origins` | `sites/<site>/site_config.json` | No | Development-only escape hatch for localhost origins. Not set on `visaguy`. |

Record key **names** only. Never commit values (`.agents/rules/project-rules.md`).

> **The lookup HMAC key must never change.** Every stored
> `verification_lookup_hash` derives from it. Rotating it silently invalidates
> the public lookup for every existing application, with no error and no
> migration path — only `lifecycle_service.py:243` writes that hash, and only at
> creation. There is no recompute seam.

Generate without echoing the value:

```bash
cd /home/shahzad/bench
KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))")
bench --site <site> set-config visa_tracker_lookup_hmac_key "$KEY"
```

## Required `Visa Tracker Settings`

The feature **fails closed** when unconfigured: `is_public_tracking_enabled()`
requires both `enabled` and `enable_public_tracking`, and
`lifecycle_service.py:192` no-ops the Customer / PF Process File hooks on the
same guard. An empty settings Single therefore renders the whole feature inert —
useful to know, both as a safety property and as a diagnosis.

| Field | Note |
|---|---|
| `enabled` | Master switch. Everything is inert without it. |
| `enable_public_tracking` | Opens the three public endpoints. |
| `enable_passport_extraction` | Enables the FileFlo inspection path. |
| `passport_field_ids` | **Must match `FF File Collection File.field_id` exactly.** Newline-separated. No wildcards. A wrong value fails silently — `jobs.py:57` returns `[]`. |
| `frontend_base_url` | The single approved CORS origin. One value means one environment. |
| `require_manual_verification` | Per ADR-007: unset means automatic verification. **Leave set in any real production environment.** |

## FileFlo template prerequisite

`field_id` must be set on the relevant `FF File Template File` row. It is copied
into the collection at creation (`fileflo/document_fetch.py`), and consumers
select passport rows by it.

Discovered the hard way: **no template in the system had `field_id` populated**,
so the selector the feature depends on was empty across all real data. Setting
it on the template alone is not enough — existing collections never pick up a
later template change, because `document_fetch` copies rows only into an empty
collection and otherwise throws "Document Already Exists".

## Deploy / update procedure

1. Back up first: `bench --site <site> backup`.
2. Check out `feat/visa-tracker` in each of the five repositories
   (`the_visaguy`, `fileflo`, `passport_extractor`, `visaguy_crm`,
   plus the `visa_tracker` frontend). As of 2026-09-01 these are the plain
   bench app checkouts at `~/bench/apps/<app>` — there are no separate
   worktrees to detach first. (An earlier layout held the branch in dedicated
   worktrees under `/home/shahzad/visa-tracker-worktrees/`; that directory no
   longer exists.)
3. `bench --site <site> migrate`. Note this migrates **all installed apps**, not
   only FEAT-001's.
4. `bench --site <site> clear-cache`.
5. **Restart `bench start`.** This is not optional and is the single most common
   cause of "the fix didn't work":
   - `frappe.conf` (and therefore any newly set `site_config` key) is cached per
     process;
   - Python modules are already imported and are not reloaded by `clear-cache`;
   - the werkzeug reloader did **not** reliably respawn on edit in practice —
     a `.py` newer than its `.pyc` with a long-lived serve process is the
     signature.
6. Verify per "Post-deploy verification" below.

## Post-deploy verification

```bash
# 4 tables expected; Visa Tracker Settings is a Single and correctly has none
bench --site <site> mariadb -e "SHOW TABLES LIKE 'tabVisa Track%';"

# 6 status fixtures expected
bench --site <site> mariadb -e "SELECT name FROM \`tabVisa Tracking Status\`;"

# exactly ONE header expected (see ADR-008)
curl -s -i -X POST '<base>/api/method/the_visaguy.visa_tracking.api.verification.verify_identity' \
  -H 'Origin: <frontend_base_url>' -H 'Content-Type: application/json' \
  -d '{"passport_number":"P0000000","date_of_birth":"1990-01-01"}' \
  | grep -ci 'access-control-allow-origin'
```

Use synthetic values (`P0000000`, `1990-01-01`, `203.0.113.x`) for probes.

## Shared-host safety

`erpcode.tridz.in` is shared. `bench serve`/gunicorn processes belonging to
`anwar`, `safwan`, `jezlan`, `swafa`, `shahalakv`, `vaishna`, `vyshnav`,
`sandra` and others run on the same box. **Verify `ps` ownership is `shahzad`
before signalling anything.** Ours is the bench under `/home/shahzad/bench`,
proxied by `/etc/nginx/conf.d/shzd.conf` → `127.0.0.1:8008`.

Beware self-matching process polls: `pgrep -f "site <x> migrate"` matches the
polling shell itself, so a wait loop never terminates. This produced a false
"still running" report during the 2026-07-22 deploy.

## Updating a staging or live site

This section covers deploying the dependant-status-display change (ADR-010
"Amendment (2026-09-03)", TASK-016) and, more generally, any change spanning
this feature's five repositories. It references rather than duplicates the
"Deploy / update procedure" above and the test-site rebuild recipe below —
read both first.

**Apps to update:** `the_visaguy`, `visaguy_crm`, `fileflo`,
`passport_extractor`, plus the `visa_tracker` frontend. `processflo` is
unchanged by this feature and needs no action.

**Check out the branch in each app, then run `bench migrate` ONCE** — per
step 3 of "Deploy / update procedure" above, this migrates *all* installed
apps on the site, not only these five, so there is no per-app migrate step
to repeat.

### What `bench migrate` brings automatically (fixtures)

`bench migrate` syncs DocType schema, runs patches, then syncs fixtures, in
that order. The following are shipped as fixtures in the relevant app and
therefore load **automatically** on migrate — no separate action needed:

- **`the_visaguy`:** custom fields (present in both `custom_field.json` and
  `custom_fields.json` — see risk 29 in
  `docs/risks-and-open-questions.md`, both currently load), **custom
  docperms**, **property setters**, roles, client scripts, workspace,
  Insights charts/queries, and the `visa_tracking_status` fixture (the six
  status records, including `public_title`).
- **`visaguy_crm`:** custom fields, **custom docperms**, **property
  setters**, roles, **workflows plus workflow states/actions**, client
  scripts, email templates, print formats, reports, workspace.

Custom fields and permissions are called out explicitly here because this
was the owner's specific question: yes, both custom fields and permission
(docperm/property setter) fixtures sync automatically with `bench migrate`
on both apps — no manual field-by-field or permission-by-permission
restoration is needed on a clean deploy. (Contrast with `visaguy` in its
*current* state, where three of these Custom Fields are missing not because
fixture sync failed, but because they were deleted out-of-band afterward —
see risk 25. A fresh `bench migrate` restores them; the missing state on
`visaguy` today is drift to be corrected by running migrate, not evidence
that fixture sync itself is unreliable.)

**`fileflo` and `passport_extractor` ship no fixtures** — their schema lives
entirely in DocType JSON, so `bench migrate`'s schema-sync step (not its
fixture-sync step) is what brings their changes in. No fixture-related
action is needed for either app.

### What is NOT automatic — manual, per site

- **`Visa Tracker Settings`** — a Single; its field values are
  configuration, not fixtures, and are never synced by migrate. Set by hand
  per site (see "Required `Visa Tracker Settings`" above, and the
  environment-specific values table under "Rebuilding the dedicated test
  site" below for what differs between `visaguy` and a test site).
- **`visa_tracker_lookup_hmac_key`** in `sites/<site>/site_config.json` —
  generate per site (see "Required server-side configuration" above).
  **Never rotate an existing site's key** — every stored
  `verification_lookup_hash` derives from it and there is no recompute path;
  rotating it silently breaks every existing application's public lookup.
- **`allow_cors`** in `sites/<site>/site_config.json` — required since
  ADR-008; without it the application emits no CORS headers and breaks
  every browser client (see "Required server-side configuration" above).
- **`field_id`** on `FF File Template File` rows — this is data, not a
  fixture, and is not brought in by migrate (see "FileFlo template
  prerequisite" above).
- **The frontend build** — `visa_tracker` is a standalone SPA; deploying it
  is a separate build/publish step from the bench-side `bench migrate`, not
  covered by it.

### Sequence for this deployment

1. Follow "Deploy / update procedure" above (backup, check out branches in
   all five repositories, `bench migrate` once, `clear-cache`, **restart
   `bench start`**, verify).
2. Confirm the manual, per-site items above are already set on the target
   site (they should already be present from the original FEAT-001 rollout;
   this deployment does not introduce any new manual per-site value — the
   dependant-display change is entirely fixture/code, no new settings
   field).
3. Run "Post-deploy verification" above, plus a targeted check that a
   primary with dependants returns a non-empty `dependants` array and that
   a dependant's own lookup returns `dependants: []` with status fields
   matching their primary's current status (see ADR-010's "Amendment
   (2026-09-03)" for the exact payload shape to expect).
4. Frontend: deploy `visa_tracker` separately once its `title` rendering
   (already shipped, commits `b25df4a`/`204f563`) and — once complete —
   its `dependants` rendering (TASK-017, not yet started) are ready. The
   backend change is independently deployable and does not require the
   frontend to be updated first; until the frontend ships `dependants`
   rendering, the SPA will silently ignore the new array in the response.

## Rebuilding the dedicated test site

The site `visa-tracker-test.localhost` was dropped on 2026-09-01 (`bench.log`
records three `drop-site` calls ending in `--force`) and **no backup existed**.
It was rebuilt from scratch the same day. This recipe exists so the next rebuild
is a copy-paste rather than a rediscovery — getting the suites green took two
rounds of configuration archaeology.

> **Do NOT mirror `visaguy`'s `Visa Tracker Settings` wholesale.** Two values are
> test-site-specific and the integration tests assert them directly. Copying the
> `visaguy` values produced 8 failures + 1 error on an otherwise correct build.

1. `bench new-site visa-tracker-test.localhost`. The `root_password` key in
   `sites/common_site_config.json` is required and is picked up automatically —
   never print it. Set a throwaway Administrator password; the site is reachable
   only through an explicit `Host` header on loopback.

2. Install apps in this order (each earlier app supplies something a later one
   needs — `PF Process File` from `processflo`, `FF File Collection` from
   `fileflo`, `CRM Lead` from `crm`, `Salary Component` from `hrms`):

   ```bash
   erpnext  crm  insights  hrms  processflo  fileflo  visaguy_crm  passport_extractor  the_visaguy
   ```

   > **`visaguy_crm` and `hrms` are not optional, and omitting them produces a
   > site that looks fine and silently lies.** The first rebuild (2026-09-01)
   > left both out and the suite went green anyway — because `visaguy_crm` owns
   > the customisations that make `PF Process File` behave like production:
   >
   > - `workflow_state` (Link → Workflow State) and the **active**
   >   `Process File Workflow`. Without it the field does not exist at all, and
   >   the TASK-016 client-status resolver has nothing to read.
   > - `custom_form_submitted` (Check) — the durable questionnaire signal.
   > - The mandatory fields `custom_department` (Link → Department) and
   >   `process_` (Link → PF Process Template).
   >
   > `hrms` is required only because `visaguy_crm`'s `Company` customisation
   > references `Salary Component`; without it the `visaguy_crm` install aborts
   > partway, leaving its hooks active but its fields missing — a worse state
   > than not installing it at all. Install `hrms` first.
   >
   > Installing these two turned 28 previously-passing tests red, all with one
   > root cause: fixtures were building `PF Process File` and `Lead` documents
   > that could never exist in production. That cascade
   > (`custom_department` → `Department.company` → `Company.{currency, country,
   > abbr, gst_category}` → `Lead.{mobile_no, custom_zone, custom_lead_source,
   > custom_destination}` → `Customer.naming_series` via `Zone`) is now handled
   > by the shared `the_visaguy/visa_tracking/tests/fixtures.py` helper. Reuse
   > it rather than hand-building these documents.

   **Known remaining divergence:** `CRM Migration Settings` exists on `visaguy`
   but is not installed by any app here, so creating a `Lead` as a user holding
   "Consultant Role" (including Administrator) hits `visaguy_crm`'s auto-assign
   path and fails. The test fixtures sidestep this by inserting Leads as a
   dedicated unprivileged user.

3. `bench --site visa-tracker-test.localhost migrate` until clean.

4. Generate the lookup HMAC key without echoing its value:

   ```bash
   KEY=$(python3 -c "import secrets;print(secrets.token_urlsafe(48))")
   bench --site visa-tracker-test.localhost set-config visa_tracker_lookup_hmac_key "$KEY"
   ```

5. Apply `Visa Tracker Settings`. The two rows marked **differs** are the ones
   that must NOT be copied from `visaguy`:

   | Field | Test-site value | Note |
   |---|---|---|
   | `frontend_base_url` | `https://tracker-test.example.com` | **differs** from `visaguy` (`http://localhost:5173/`); asserted by `test_cors_against_live_settings` |
   | `support_link` | `https://tracker-test.example.com/support` | **differs**; asserted by `test_status_payload_against_live_documents` |
   | `passport_field_ids` | `passport_front` + `passport_back`, newline-separated | **differs** from `visaguy` (`passport`); required by the FileFlo inspection and reconciliation integration tests. This value was undocumented before 2026-09-02 and had to be recovered from a test fixture comment |
   | `enabled` / `enable_public_tracking` / `enable_passport_extraction` | `1` | |
   | `auto_create_tracking_application` / `auto_link_verified_passport` | `1` | |
   | `require_manual_verification` | `0` | ADR-007 |
   | `generic_failure_message` | `Unable to verify. Please check your details and try again.` | must equal the contract default |
   | `session_expiry_minutes` / `max_session_lifetime_minutes` | `15` / `60` | |
   | `maximum_failed_attempts` / `lockout_minutes` | `5` / `15` | per-identity counter, ADR-009 |
   | `status_history_limit` | `20` | |
   | `default_lead_status` / `process_file_created_status` | `APPLICATION_RECEIVED` / `WORKING_ON_APPLICATION` | superseded once TASK-016 lands; see ADR-010 |

   `scope_maximum_failed_attempts` and `scope_lockout_minutes` (ADR-009) may be
   left unset — their getters fall back to the safe defaults 20 and 60.

6. PaddleOCR models live in `~/.paddlex`, which is user-level and **survives site
   deletion** — no re-download needed. Confirm they are present before running
   the `passport_extractor` suite.

7. Verify against the baselines in *Test execution* below. Matching them is what
   proves the rebuild is faithful; a mismatch means the site build differs, not
   that the code is wrong.

   App installs and migrations here run for minutes and outlive an SSH session,
   so run them detached and poll. **Do not poll with `pgrep -f "<the command>"`:**
   over SSH the polling shell's own command line contains that string, so the
   loop matches itself and never terminates. This is the same trap recorded
   under *Shared-host safety*, and it recurred twice during the 2026-09-02
   rebuild. Poll on a captured PID (`kill -0 "$PID"`), or have the background
   command append a `DONE_MARKER` to its log and grep for that.

Fixture sync on a fresh site recreates the visa-tracking Custom Fields cleanly,
including `PF Process File-custom_client_status`. Their absence on `visaguy` is
external damage (risk 25), not a defect in the fixture.

## Test execution

```bash
bench --site visa-tracker-test.localhost run-tests --app <app> --skip-test-records
```

`--skip-test-records` is required: without it the ERPNext fixture bootstrap dies
with `LinkValidationError: Could not find Warehouse Type: Transit`.

Baselines at `the_visaguy` `53b0f28` (2026-09-02): `the_visaguy` **298**,
`passport_extractor` 63, `fileflo` 8, frontend `visa_tracker` 41. The
`the_visaguy` figure was 248 before TASK-011, TASK-012 and the merge of
`main` added tests.

## Diagnostic order for "no tracking application was created"

Each stage has failed at least once in practice. Check in order:

1. `FF File Collection File.field_id` populated on the **uploaded** row?
2. RQ job for `enqueue_fileflo_inspection` enqueued? (Requires `bench start`'s
   worker to be running.)
3. `Passport Extraction` created, and what `status`?
   - `Failed` / `NO_MRZ_FOUND` → extraction problem.
   - `Extracted` → verification gate (ADR-007); check
     `require_manual_verification`.
   - `Needs Review` → check digits, missing fields, or low confidence.
4. `Visa Tracking Application` created with a **non-NULL**
   `verification_lookup_hash` and `tracking_enabled = 1`? A NULL hash means the
   HMAC key was missing at creation time — and it cannot be repaired in place.
5. Public lookup failing with a correct passport/DOB while the application
   exists is stage 4, not stage 1.
