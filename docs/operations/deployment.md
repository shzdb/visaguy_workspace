# Deployment

**Safety disclaimer:** every command below is documented from checked-in scripts, `Procfile`, `package.json`, Jenkinsfile, GitHub Actions workflow, accepted reconnaissance reports, and installed Bench 5.29.0 help. Read-only reconnaissance and CLI help were run; no deployment, backup, restore, migration, build, test, or restart command was run. Validate the procedure in staging and take a verified backup before production use.

## Evidenced topology

- Remote bench host: `erpcode.tridz.in:2257`
- Bench root: `/home/shahzad/bench`
- Site: `visaguy`
- Process manager: Supervisor (or systemd, per `common_site_config.json` keys)
- Business client deploys via Docker Compose + Jenkins + GitHub Actions.
- Consumer website and eligibility checker have no repo-level production deployment config evidenced.

## Pre-deploy checkpoint

```bash
# 1. Backup
bench --site visaguy backup --with-files

# 2. Record HEADs
cd /home/shahzad/bench
for app in apps/*/; do
  echo "$app: $(git -C "$app" rev-parse HEAD)"
done

# 3. Record dirty apps
# insights, mansico_meta_integration, processflo, visaguy_frappe_crm, visaguy_raven
```

## Backend update sequence

1. Update apps in dependency order:
   - `frappe`
   - `erpnext`
   - `hrms` / `payments`
   - `india_compliance`
   - remaining apps
2. Migrate and build:
   ```bash
   bench --site visaguy migrate
   bench build
   bench restart --supervisor   # or --systemd, matching the deployment
   ```
3. Run wrapper tests between each major step.

## Frontend deployment

### Business client

```bash
# Jenkinsfile equivalent
docker compose down
docker compose up -d --build
```

GitHub Actions builds and pushes a Docker image on pushes to the `dev` branch.

### Consumer website and eligibility checker

No repo-level production deployment config was evidenced. READMEs point to standard Next.js/Vercel and Vite hosting patterns.

## Rollback

1. Stop the configured bench services and preserve the failed state for investigation.
2. Revert each app to the recorded pre-change commit.
3. Restore the site using the exact generated artifacts:
   ```bash
   bench --site visaguy restore <database-backup.sql.gz> \
     --with-public-files <public-files-backup.tar> \
     --with-private-files <private-files-backup.tar>
   ```
4. Supply `--encryption-key` only when required by the backup; obtain it through the approved secret-management process.
5. Run `bench --site visaguy migrate` only if required for the restored code/schema combination.
6. Run `bench build`, then `bench restart --supervisor` or `bench restart --systemd`.

## Post-deploy validation

- `bench doctor --site visaguy`
- `bench --site visaguy run-tests --app <app>` for updated apps
- Frontend build and lint for each updated frontend
- Representative smoke tests (login, order creation, payment redirect, ticket creation, leave submission)

## Unresolved production details

- Exact Supervisor vs systemd configuration was not inspected.
- Backup retention, off-site storage, and restore drill frequency were not verified.
- Eligibility checker and consumer website deployment pipelines are not documented in their repositories.
