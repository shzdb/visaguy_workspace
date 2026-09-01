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
   plus the `visa_tracker` frontend).
   - If a worktree under `/home/shahzad/visa-tracker-worktrees/` holds the
     branch, `git -C <worktree> checkout --detach` first to free the name.
     Otherwise the checkout can only be done detached.
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

## Test execution

```bash
bench --site visa-tracker-test.localhost run-tests --app <app> --skip-test-records
```

`--skip-test-records` is required: without it the ERPNext fixture bootstrap dies
with `LinkValidationError: Could not find Warehouse Type: Transit`.

Baselines: `the_visaguy` 248, `passport_extractor` 63, `fileflo` 8,
frontend `visa_tracker` 41.

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
