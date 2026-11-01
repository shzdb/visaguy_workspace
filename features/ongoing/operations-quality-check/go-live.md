# FEAT-006 go-live checklist: process file quality check

Replace `<site>` with the live site. Run from the live bench folder. The owner
does every step here. Tested on `visa-tracker-test.localhost`; not yet run on
live.

## Before you start

- [ ] PR tvgglobal/the_visaguy#51 is merged to `main`, and it includes commit
      `feat: set up the quality check agent and Schengen template on migrate`.
- [ ] A real check has passed as an operations user on the dev site (not only
      as Administrator).
- [ ] The OpenAI plan does not train on inputs (passports and visas are sent).
- [ ] You have an OpenAI API key that can use `gpt-5.4-mini`.
- [ ] Off-peak window: installing huf takes time and restarts the bench.

## 1. Back up and record package versions

- [ ] Back up:
      ```bash
      bench --site <site> backup --with-files
      ```
- [ ] Record Python packages, so drift can be seen and undone:
      ```bash
      ./env/bin/pip freeze > ~/pip-before-huf.txt
      ```
- [ ] Record current conflicts:
      ```bash
      ./env/bin/pip check > ~/pip-check-before-huf.txt
      ```

## 2. Install huf at the pinned version

Install huf **before** migrating `the_visaguy`. The role and setup patches run
only once, and they skip if huf is missing.

- [ ] Get the app at the tag:
      ```bash
      bench get-app --branch v1.0.0-beta.4 https://github.com/tridz-dev/huf
      ```
- [ ] Compare packages. Expected: huf's new packages only, and no upgraded
      Frappe, ERPNext or other app packages. If existing packages moved, stop
      and restore them from `~/pip-before-huf.txt` before going on.
      ```bash
      ./env/bin/pip check | diff ~/pip-check-before-huf.txt -
      ```
- [ ] Check that pyOpenSSL still loads (S3 backups depend on it):
      ```bash
      ./env/bin/python -c "import OpenSSL; print(OpenSSL.__version__)"
      ```
- [ ] Install on the site:
      ```bash
      bench --site <site> install-app huf
      ```
- [ ] Keep `bench update` away from huf:
      ```bash
      bench exclude-app huf
      ```

## 3. Deploy `the_visaguy` and migrate

- [ ] Pull `main` in `apps/the_visaguy`.
- [ ] Migrate:
      ```bash
      bench --site <site> migrate
      ```
- [ ] In the migrate output, confirm these lines:
      - `Executing the_visaguy.patches.v1_0.grant_huf_user_role`
      - `Process file QC setup done: agent Operation QC, template …, N destinations linked.`
      If it says skipped or failed, fix the cause, then run:
      ```bash
      bench --site <site> execute the_visaguy.quality_check.setup.setup_process_file_qc
      ```
- [ ] Restart:
      ```bash
      bench restart
      ```

The patches do this for you:

- **Huf User** role for all enabled desk users.
- Agent **Operation QC**: OpenAI, `gpt-5.4-mini`, Persist Conversation off,
  allowed roles `Operations Associate` and `Operations Team Lead`.
- Prompt template **Schengen QC** (category Operation Quality Check).
- The template linked on the Schengen destinations listed below.
- Visaguy AI Settings: agent, sidebar attachments on, 60 documents, 100 MB,
  restart after 30 minutes. Shared rules stay empty, so the built-in rules
  are used.

They only add what is missing and never overwrite existing values.

## 4. Manual setup (cannot be scripted)

- [ ] Huf → **AI Provider → OpenAI** → paste the API key. Keys are never stored
      in code.

## 5. Verify

- [ ] Visaguy AI Settings shows QC Agent = Operation QC.
- [ ] Destination **Switzerland** → AI tab → QC Prompt Template = Schengen QC.
- [ ] Destination **Turkey** → AI tab → blank.
- [ ] Workers are running and the `long` queue is not backed up (QC shares it
      until the dedicated queue is added):
      ```bash
      bench doctor
      ```

## 6. Smoke test as an operations user

Use one Operations Associate and one Team Lead, not Administrator.

- [ ] Open a Schengen process file: **Check QC** shows.
- [ ] Click it. Status becomes Processing, and last updated changes.
- [ ] Within a few minutes: Completed, with the report in the Quality Check tab.
- [ ] Document keys open the files. Applicant links open the process files.
      Copy works.
- [ ] On a primary with dependants: the dialog offers this file or the whole
      group, and every file in the group gets the report.
- [ ] A non-Schengen destination shows no button.
- [ ] A user outside operations sees no button.
- [ ] huf → Agent Run shows the run under the user who clicked, with its cost.

## After go-live

- [ ] Users created later need the **Huf User** role added by hand.
- [ ] New Schengen destinations need the template set on their AI tab.
- [ ] Watch the `long` queue and OpenAI cost for the first days.
- [ ] Dedicated `process_file_qc` queue: do soon (FEAT-006 follow-ups).

## If something goes wrong

- **Turn QC off without a deploy:** clear QC Agent in Visaguy AI Settings. The
  button disappears everywhere. Nothing else depends on it.
- **A file is stuck in Processing:** after 30 minutes, Check QC can be run again.
- **"You do not have access to run this agent":** the user lacks Huf User, or
  the agent's Allowed Roles lack their role.
- **Provider error in the tab:** check the key in AI Provider, and the Error Log.

## Destinations

Linked: Schengen, Austria, Belgium, Bulgaria, Croatia, Czech Republic, Denmark,
Estonia, Finland, France, Germany, Greece, Hungary, Iceland, Italy, Latvia,
Liechtenstein, Lithuania, Luxembourg, Malta, Netherlands, Norway, Poland,
Portugal, Romania, Slovakia, Slovenia, Spain, Sweden, Switzerland.

Handled by the Schengen departments but **not** linked, because they are not in
the Schengen area: Albania, Armenia, Cyprus, Ireland, South Africa, Turkey. To
enable one, set a suitable template on its AI tab.
