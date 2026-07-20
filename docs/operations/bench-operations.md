# Bench Operations

**Safety disclaimer:** every command below is documented from checked-in scripts, `Procfile`, `package.json`, accepted reconnaissance reports, and installed Bench 5.29.0 help. Read-only reconnaissance and CLI help were run; the operational or mutating commands below were not. Run them against a staging bench or with a verified backup first.

## Safe reconnaissance (read-only)

```bash
bench --version
bench --site visaguy list-apps
bench doctor --site visaguy
```

Inspect repository state per app:

```bash
# inside each apps/<app>/ directory
git status --short
git log --oneline -5
git rev-parse --abbrev-ref HEAD
```

Inspect scheduler/worker health:

```bash
sudo supervisorctl status   # only when Supervisor is the configured manager
# or inspect the explicitly configured systemd units
```

## Install / migrate / build

```bash
# 1. Add app to bench
bench get-app --branch <branch> <remote-url>

# 2. Install on site
bench --site visaguy install-app <app-name>

# 3. Run migrations and patches
bench --site visaguy migrate

# 4. Rebuild assets (required when bundles change)
bench build
# or, for development
bench watch

# 5. Restart the configured process manager
bench restart --supervisor
# or, for a systemd-managed deployment
bench restart --systemd
```

## Scheduler / workers / background jobs

```bash
# Inspect background workers and process manager
bench doctor --site visaguy
sudo supervisorctl status   # Supervisor deployments only

# Inspect registered scheduler hooks (read-only)
bench --site visaguy console
# then in console:
# frappe.get_hooks("scheduler_events")
```

Do **not** run `bench schedule` or `bench worker` manually on production; those are foreground processes already managed by the configured service manager.

Key scheduled jobs evidenced:

- `the_visaguy`: daily tmp-file clearing
- `frappe_notifier`: daily log cleanup
- `waflo`: cron every minute flow expiry, hourly retries
- `visaguy_raven`: daily timesheet reminders
- `helpdesk`: `all` search-index check
- `crm`: `after_migrate` settings
- `frappe_whatsapp`: frequent intervals

## Backup

```bash
bench --site visaguy backup --with-files
```

Record the generated database, public-file, private-file, and configuration backup paths; verify the artifacts are non-empty.

## Restore

```bash
bench --site visaguy restore <database-backup.sql.gz> \
  --with-public-files <public-files-backup.tar> \
  --with-private-files <private-files-backup.tar>
```

Supply `--encryption-key` only when required by the backup; obtain it through the approved secret-management process and never place it in this workspace or shell history.

Run `bench --site visaguy migrate` only if required for the restored code/schema combination. Then run `bench build` and `bench restart --supervisor` or `bench restart --systemd`.

## Validation

```bash
# Unit tests per app
bench --site visaguy run-tests --app <app>
```

Smoke tests (manual or scripted):

- eligibility checker: complete chat flow and verify Raw Lead created
- B2B portal: login, create order, request payment
- consumer portal: OTP login, create visa order, submit application
- helpdesk: create and assign ticket
- HRMS: submit leave / expense claim
- Raven: trigger a notification
- payments: complete a test transaction via gateway sandbox

## Dirty-tree handling

Affected repositories: `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`.

```bash
cd apps/<app>
git status --short
git diff --stat        # do not copy diff contents into runbook log
git stash list
```

Decision options:

1. Commit to a feature branch if changes are intentional.
2. Revert if changes are accidental.
3. Preserve in a named patch file for review.

Do not deploy from a dirty working tree.
