# Development bench: sync procedure and state

The development bench is `ssh erpcode`, `/home/shahzad/bench`. Sites:
`visaguy` (development copy of live; the owner migrates and tests it) and
`visa-tracker-test.localhost` (the test site agents migrate and test on).

Start every new feature session with this sync, so work begins from what is
merged.

## Procedure

1. Fetch every app (only updates remote refs):
   `cd ~/bench/apps && for a in *; do git -C $a fetch -q --prune upstream; done`
2. For each **own app** (table below), fast-forward its current branch:
   `git merge --ff-only upstream/<branch>`. Never reset, stash or discard a
   local edit. If the app has uncommitted edits, first check that the incoming
   commits do not touch those files:
   `comm -12 <(git status --short | sed 's/^...//' | sort) <(git diff --name-only HEAD upstream/<branch> | sort)`.
   If they do, skip the app and report it.
3. Do not pull the **third-party apps** (framework upgrades). Report how far
   behind they are; the owner decides.
4. Check that every app still imports (catches a pulled app that needs a newer
   dependency):
   `cd ~/bench/sites && ~/bench/env/bin/python -c "import importlib; [importlib.import_module(a) or importlib.import_module(a + '.hooks') for a in open('apps.txt').read().split()]"`
5. Migrate and test the **test site only**:
   `bench --site visa-tracker-test.localhost migrate`, then
   `bench --site visa-tracker-test.localhost run-tests --app <app> --skip-test-records`.
   Never migrate or run anything on `visaguy`; tell the owner it needs a
   migrate.
6. Delete merged task branches and worktrees (`/home/shahzad/sl-worktrees`,
   and the Mac clones under `~/Projects/tridz/worktrees/visa-soft-launch`).
   Keep long-lived branches (`main`, `develop`, `master_backup`, …).
7. Update the state table below and commit.

This bench's redis cache and queue (ports 13008, 11008) are not always
running. `bench migrate` stops with "Service redis_cache is not running";
start them with `redis-server config/redis_cache.conf` and
`redis-server config/redis_queue.conf` from `~/bench` (background). Other
tenants' benches share the host: only stop processes you started.

## Apps

Own apps (pull): `crm` (tridz-dev/frappe-crm), `fileflo`,
`frappe_conversions_api`, `frappe_notifier`, `helpdesk` (tridz-dev/helpdesk_frk),
`otp_authentication`, `passport_extractor`, `payment_integrations`,
`processflo`, `quick_kanban`, `the_visaguy`, `visaguy_business`, `visaguy_crm`,
`visaguy_frappe_crm`, `visaguy_helpdesk`, `visaguy_hrms`, `visaguy_raven`,
`visaguy_website`, `waflo`.

Third-party (owner decision): `frappe`, `erpnext`, `hrms`, `india_compliance`,
`payments`, `lms`, `insights`, `telephony`, `non_profit`, `raven`,
`frappe_whatsapp`, `employee_self_service`, `mansico_meta_integration`.

## State (2026-10-19)

| App | Branch | Head | Note |
|---|---|---|---|
| `the_visaguy` | `main` | `4f3d063` | includes TASK-044 (#47); now tracks `upstream/main` |
| `passport_extractor` | `main` | `a2f5a4a` | includes TASK-042–045 (#5); was on `perf/passport-extraction-speed` |
| `fileflo` | `main` | `955e490` | up to date |
| `visaguy_crm` | `main` | `daa863e` | pulled from `bdfc8fe` |
| `waflo` | `develop` | `c705be5` | up to date (WhatsApp retry) |
| `frappe_notifier` | `develop` | `c5903a2` | pulled |
| `visaguy_business` | `develop` | `0460732` | pulled; local edit in `functions/api/generate_preliminary_documents.py` kept |
| `visaguy_hrms` | `main` | `2ad70fe` | pulled |
| `visaguy_website` | `develop` | `17d3496` | pulled |
| `visaguy_helpdesk` | `develop` | `1692b38` | **held 3 behind**: `upstream/develop` (`c560901`, commit `f013307`) imports `helpdesk.helpdesk.doctype.hd_settings.helpers`, which tridz-dev/helpdesk_frk `modification_develop_branch` does not have; pulling it breaks every bench command. Do not deploy it to live until `helpdesk` is upgraded |
| `visaguy_frappe_crm` | `develop` | `a1e22da` | **held 110 behind**: local edit in `fixtures/property_setter.json` conflicts with incoming changes; owner decides |
| `visaguy_raven` | `develop` | `330fa1b` | **held 11 behind**: local edit in `fixtures/raven_bot.json` conflicts with incoming changes; owner decides |
| `processflo` | `develop` | `2f2b565` | up to date; local edit in `generate_file_collection.py` kept |
| `crm`, `helpdesk`, `frappe_conversions_api`, `payment_integrations`, `quick_kanban` | — | — | up to date |
| `otp_authentication` | `email` | `f4409ba` | no tracking branch; not changed |

Third-party apps behind their upstream branch (not pulled): `frappe`
15.113.0 → 15.123.1 (1109 commits), `hrms` 7506, `india_compliance` 5670,
`raven` 4467, `payments` 451, `employee_self_service` 306, `lms` 138,
`frappe_whatsapp` 21, `telephony` 4, `insights` 1. `erpnext` could not be
fetched: `apps/erpnext/.git/refs/remotes` is not writable by `shahzad`.

After the sync: all 32 apps import; test site migrated; on-site
`passport_extractor` 189 OK, `the_visaguy` 819 OK. Merged task branches and
all task worktrees removed on the bench and on the Mac. `visaguy` was not
migrated: the owner should migrate it before using it.
