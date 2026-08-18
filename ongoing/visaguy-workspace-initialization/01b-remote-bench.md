# RB — Remote bench and app reconnaissance

Generated: 2026-07-20. Source: read-only inspection of `/home/fasil/fasil-bench-v15`. 
No secrets, credentials, or production data are recorded; only key names and source metadata.

## Executive summary

- Bench host: `erpcode.tridz.in:2257` (read-only SSH).
- Bench CLI: `5.29.0`; Frappe `15.113.0`; ERPNext `15.106.0`; HRMS `15.45.2`; Python `3.10.12`; Node `v12.22.9` (socketio uses Node `v18.20.8` via `.nvm`).
- Site: `visaguy`; `sites/apps.txt` lists 29 bench-available apps, while `bench --site visaguy list-apps` confirms 27 are installed on the site.
- Coverage: all 29 bench app repositories inventoried; `employee_self_service` and `mansico_meta_integration` are bench-only and not installed on site `visaguy`.
- Dirty working trees: 5 (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`).
- Integration settings DocTypes observed: ~48 across apps.
- Verdict: bench is a heavily customized Frappe v15 stack with internal wrapper apps around CRM/Helpdesk/HRMS/Raven plus payment/OTP/WhatsApp/Meta integrations.

## RB1 — Bench/platform metadata

| Component | Version / value | Evidence |
|---|---|---|
| bench CLI | 5.29.0 | `bench --version` |
| Frappe | 15.113.0 | `apps/frappe/frappe/__init__.py`: `__version__` |
| ERPNext | 15.106.0 | `apps/erpnext/erpnext/__init__.py`: `__version__` |
| HRMS | 15.45.2 | `apps/hrms/hrms/__init__.py`: `__version__` |
| Python | 3.10.12 | `python3 --version` |
| Node (system) | v12.22.9 | `node -v` |
| Node (socketio) | v18.20.8 | `Procfile` references `.nvm/versions/node/v18.20.8/bin/node` |
| Site name | visaguy | `sites/visaguy` directory, `Procfile`/`common_site_config.json` keys |
| Bench app order | 29 apps | `sites/apps.txt` |
| Site-installed apps | 27 apps | `bench --site visaguy list-apps` |


### Config key names (values redacted)

Common site config keys: `background_workers`, `developer_mode`, `dns_multitenant`, `file_watcher_port`, `frappe_user`, `gunicorn_workers`, `live_reload`, `maintenance_mode`, `pause_scheduler`, `push_relay_server_url`, `rebase_on_pull`, `redis_cache`, `redis_queue`, `redis_socketio`, `restart_supervisor_on_update`, `restart_systemd_on_update`, `serve_default_site`, `server_script_enabled`, `shallow_clone`, `socketio_port`, `use_redis_auth`, `webserver_port`, `workers`.

Site config keys: `allow_cors`, `db_name`, `db_password`, `db_type`, `domains`, `encryption_key`, `host_name`, `hostname`, `ignore_csrf`, `mode`, `temp_host_name`, `user_type_doctype_limit`.


### Process topology (Procfile)

- Redis trio: `redis_cache`, `redis_socketio`, `redis_queue`.
- Web: `bench serve --port 8008`.
- SocketIO: Node v18 runtime for `apps/frappe/socketio.js`.
- Watch: `bench watch`.
- Schedule: `bench schedule`.
- Worker: `bench worker`.

## RB2 — Per-app inventory (compact rows)

| # | App | Class | Remote (primary) | Branch | HEAD | Ver | DT | Rpt | WF | Notif | Page | WWW | Tests | WL | Patches | Dirty |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | `frappe` | external | `https://github.com/frappe/frappe.git` | `version-15` | `01ea89c4e6` | 15.113.0 | 302 | 9 | 2 | 2 | 10 | 0 | 259 | 27 | 246 | 0 |
| 2 | `visaguy_business` | internal | `git@tridz:tridz-dev/visaguy_business.git` | `develop` | `301dbee` | 0.0.1 | 11 | 0 | 0 | 0 | 0 | 0 | 5 | 7 | 3 | 0 |
| 3 | `erpnext` | external | `https://github.com/frappe/erpnext.git` | `version-15` | `4dd9f0b255` | 15.106.0 | 565 | 180 | 0 | 2 | 6 | 0 | 352 | 27 | 433 | 0 |
| 4 | `visaguy_hrms` | internal | `git@tridz:tridz-dev/visaguy_hrms.git` | `main` | `94d341a` | 0.0.1 | 3 | 4 | 0 | 0 | 0 | 0 | 2 | 23 | 2 | 0 |
| 5 | `visaguy_crm` | internal | `git@tridz:tridz-dev/visaguy_crm.git` | `main` | `b59c3ef` | 0.0.1 | 69 | 15 | 0 | 0 | 1 | 0 | 17 | 27 | 4 | 0 |
| 6 | `payments` | external | `https://github.com/frappe/payments.git` | `version-15` | `68b54a7` | 0.0.1 | 9 | 0 | 0 | 0 | 0 | 0 | 7 | 22 | 0 | 0 |
| 7 | `india_compliance` | external | `https://github.com/resilient-tech/india-compliance.git` | `version-15` | `bde15f48` | 15.18.0 | 26 | 19 | 0 | 0 | 1 | 0 | 44 | 27 | 77 | 0 |
| 8 | `visaguy_helpdesk` | internal | `git@tridz:tridz-dev/visaguy_helpdesk.git` | `develop` | `1692b38` | 0.0.1 | 2 | 0 | 0 | 0 | 0 | 0 | 1 | 6 | 2 | 0 |
| 9 | `insights` | external | `https://github.com/frappe/insights.git` | `main` | `c9af45d` | 2.2.14 | 25 | 0 | 0 | 0 | 1 | 0 | 22 | 27 | 45 | 1 |
| 10 | `employee_self_service` | external | `https://github.com/nesscale-com/employee_self_service.git` | `version-15` | `f3c1e43` | 2.1.29 | 33 | 0 | 0 | 0 | 1 | 0 | 25 | 27 | 0 | 0 |
| 11 | `the_visaguy` | internal | `git@tridz:tvgglobal/the_visaguy.git` | `main` | `e690b5b` | 0.0.1 | 13 | 0 | 0 | 0 | 0 | 0 | 7 | 5 | 3 | 0 |
| 12 | `waflo` | internal | `git@tridz:tridz-dev/waflo.git` | `develop` | `2167958` | 0.0.1 | 6 | 0 | 0 | 0 | 0 | 0 | 4 | 1 | 2 | 0 |
| 13 | `fileflo` | internal | `git@tridz:tridz-dev/FileFlo.git` | `fix/mandatory-file` | `6683010` | 0.0.1 | 8 | 0 | 0 | 0 | 0 | 0 | 4 | 8 | 2 | 0 |
| 14 | `raven` | external | `git@tridz:The-Commit-Company/raven.git` | `main` | `dfde9b1e` | 2.7.1 | 35 | 0 | 0 | 0 | 0 | 0 | 24 | 27 | 17 | 0 |
| 15 | `helpdesk` | internal | `git@tridz:tridz-dev/helpdesk_frk.git` | `modification_develop_branch` | `a671e5f` | 0.10.0 | 38 | 4 | 0 | 0 | 0 | 0 | 26 | 27 | 18 | 0 |
| 16 | `crm` | internal | `git@tridz:tridz-dev/frappe-crm.git` | `tridz-dev` | `b3328bc9` | 2.0.0-dev | 32 | 0 | 0 | 0 | 0 | 0 | 26 | 27 | 10 | 0 |
| 17 | `visaguy_frappe_crm` | internal | `git@tridz:tridz-dev/visaguy_frappe_crm.git` | `develop` | `a1e22da` | 0.0.1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 4 | 2 | 1 |
| 18 | `non_profit` | external | `https://github.com/frappe/non_profit.git` | `develop` | `ea2c88d` | 0.0.1 | 17 | 1 | 0 | 0 | 0 | 0 | 14 | 18 | 1 | 0 |
| 19 | `frappe_conversions_api` | internal | `git@tridz:tridz-dev/frappe_conversions_api.git` | `develop` | `3a240c6` | 0.0.1 | 7 | 0 | 0 | 0 | 0 | 0 | 3 | 1 | 2 | 0 |
| 20 | `quick_kanban` | internal | `git@tridz:tridz-dev/quick_kanban.git` | `main` | `8ca57a6` | 0.0.1 | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 1 | 2 | 0 |
| 21 | `payment_integrations` | internal | `git@tridz:tridz-dev/payment_integrations.git` | `develop` | `c424a1b` | 0.0.1 | 3 | 0 | 0 | 0 | 0 | 0 | 3 | 6 | 2 | 0 |
| 22 | `mansico_meta_integration` | external | `git@tridz:Ahmed-Mansy-Mansico/mansico_meta_integration.git` | `master` | `8e595ea` | 1.2.1 | 5 | 0 | 0 | 0 | 0 | 0 | 3 | 7 | 2 | 1 |
| 23 | `frappe_notifier` | internal | `git@tridz:tridz-dev/frappe_notifier.git` | `develop` | `8da7603` | 0.0.1 | 5 | 0 | 0 | 0 | 0 | 0 | 4 | 9 | 3 | 0 |
| 24 | `visaguy_website` | internal | `git@tridz:tvgglobal/visaguy_website.git` | `develop` | `1466adf` | 0.0.1 | 17 | 0 | 0 | 0 | 0 | 0 | 7 | 5 | 2 | 0 |
| 25 | `frappe_whatsapp` | external | `https://github.com/shridarpatil/frappe_whatsapp.git` | `master` | `27f3438` | 1.0.12 | 15 | 1 | 0 | 0 | 0 | 0 | 10 | 22 | 4 | 0 |
| 26 | `otp_authentication` | internal | `git@tridz:tridz-dev/otp_authentication.git` | `email` | `f4409ba` | 0.0.1 | 1 | 0 | 0 | 0 | 0 | 0 | 2 | 7 | 2 | 0 |
| 27 | `hrms` | external | `https://github.com/frappe/hrms.git` | `version-15` | `5b3285fa` | 15.45.2 | 156 | 26 | 0 | 4 | 2 | 0 | 116 | 27 | 29 | 0 |
| 28 | `processflo` | internal | `git@tridz:tridz-dev/ProcessFlo.git` | `develop` | `2f2b565` | 0.0.1 | 6 | 0 | 0 | 0 | 0 | 0 | 4 | 5 | 2 | 1 |
| 29 | `visaguy_raven` | internal | `git@tridz:tridz-dev/visaguy_raven.git` | `develop` | `330fa1b` | 0.0.1 | 1 | 0 | 0 | 0 | 0 | 0 | 1 | 0 | 2 | 1 |


## RB2 — Per-app detail findings

### `frappe` (external)

- **Identity**: title=Frappe Framework, publisher=Frappe Technologies, version=15.113.0, license=MIT
- **Source**: `https://github.com/frappe/frappe.git` branch `version-15` HEAD `01ea89c4e6202843154f2f3818dde87eda55703e` (short `01ea89c4e6`); dirty files: 0
- **Hooks**: `/apps/frappe/frappe/hooks.py`
- **Purpose**: <div align="center"> \| <h1> \| <br> \| <a href="https://frappeframework.com"> \| <img src=".github/frappe-framework-logo.svg" height="50"> \| </a>
- **Node dependencies**: `@editorjs/editorjs`, `@frappe/esbuild-plugin-postcss2`, `@headlessui/vue`, `@popperjs/core`, `@redis/client`, `@sentry/browser`, `@vue-flow/background`, `@vue-flow/core`, `@vue/component-compiler`, `@vueuse/core`, `ace-builds`, `air-datepicker`, `autoprefixer`, `awesomplete`, `bootstrap`, `chalk`, `cliui`, `cookie`, `cropperjs`, `cssnano`, `driver.js`, `editorjs-undo`, `esbuild`, `esbuild-plugin-vue3`, `fast-deep-equal`, `fast-glob`, `frappe-charts`, `frappe-datatable`, `frappe-gantt`, `frappe-quill-image-resize`, `highlight.js`, `html5-qrcode`, `jquery`, `js-sha256`, `jsbarcode`, `launch-editor`, `localforage`, `md5`, `moment`, `moment-timezone`, `pinia`, `plyr`, `popper.js`, `postcss`, `quill`, `quill-magic-url`, `qz-tray`, `rtlcss`, `sass`, `showdown`, `socket.io`, `socket.io-client`, `sortablejs`, `superagent`, `touch`, `vue`, `vue-router`, `vuedraggable`, `vuex`, `yargs`
- **Override whitelisted methods**: `frappe.utils.file_manager.download_file`, `frappe.core.doctype.file.file.download_file`, `frappe.core.doctype.file.file.unzip_file`, `frappe.core.doctype.file.file.get_attached_images`, `frappe.core.doctype.file.file.get_files_in_folder`, `frappe.core.doctype.file.file.get_files_by_search_text`, `frappe.core.doctype.file.file.get_max_file_size`, `frappe.core.doctype.file.file.create_new_folder`, `frappe.core.doctype.file.file.move_file`, `frappe.core.doctype.file.file.zip_files`, `frappe.www.login.login_via_google`, `frappe.www.login.login_via_github`, `frappe.www.login.login_via_facebook`, `frappe.www.login.login_via_frappe`, `frappe.www.login.login_via_office365`, `frappe.www.login.login_via_salesforce`, `frappe.www.login.login_via_fairlogin`
- **Website route rules**: 5
- **Scheduler events**: `all`, `hourly`, `hourly_maintenance`, `daily`, `daily_maintenance`, `weekly_long`, `monthly`, `monthly_long`
- **Patches**: 246 (first: `[pre_model_sync]`, `frappe.patches.v16_0.enable_setup_complete #01-07-2025 re-run-patch`, `frappe.patches.v15_0.remove_implicit_primary_key`, `frappe.patches.v12_0.remove_deprecated_fields_from_doctype #3`, `execute:frappe.utils.global_search.setup_global_search_table()`)
- **Frontend bundles**: app_js=['libs.bundle.js', 'desk.bundle.js', 'list.bundle.js', 'form.bundle.js', 'controls.bundle.js', 'report.bundle.js', 'telemetry.bundle.js', 'billing.bundle.js'], app_css=['desk.bundle.css', 'report.bundle.css'], web_js=['website_script.js'], web_css=[]
- **Sample whitelisted methods**: `auth_webhook` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/push_notification.py:270), `subscribe` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/push_notification.py:283), `unsubscribe` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/push_notification.py:289), `revert` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/social/doctype/energy_point_log/energy_point_log.py:84), `add_review_points` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/social/doctype/energy_point_log/energy_point_log.py:233), `get_energy_points` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/social/doctype/energy_point_log/energy_point_log.py:239), `get_user_energy_and_review_points` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/social/doctype/energy_point_log/energy_point_log.py:245), `review` (/home/fasil/fasil-bench-v15/apps/frappe/frappe/social/doctype/energy_point_log/energy_point_log.py:288)
- **Cross-app imports sample**: `from frappe.utils.error import log_error` at `apps/frappe/frappe/__init__.py:...`, `from frappe.utils.print_utils import get` at `apps/frappe/frappe/__init__.py:...`, `import frappe` at `apps/frappe/frappe/__init__.py:...`, `from frappe.query_builder import (` at `apps/frappe/frappe/__init__.py:...`, `from frappe.utils.caching import request` at `apps/frappe/frappe/__init__.py:...`
- **Integration settings DocTypes**: `google_settings`, `s3_backup_settings`, `dropbox_settings`, `ldap_settings`, `push_notification_settings`, `oauth_provider_settings`, `sms_settings`
- **Hook `has_website_permission`**: `{"Address": "frappe.contacts.doctype.address.address.has_website_permission"}`
- **Hook `after_install`**: `"frappe.utils.install.after_install"`
- **Hook `before_install`**: `"frappe.utils.install.before_install"`
- **Hook `after_migrate`**: `["frappe.website.doctype.website_theme.website_theme.after_migrate", "frappe.search.sqlite_search.build_index_in_background"]`
- **Hook `before_migrate`**: `["frappe.core.doctype.patch_log.patch_log.before_migrate"]`
- **Hook `on_login`**: `"frappe.desk.doctype.note.note._get_unseen_notes"`
- **Hook `on_logout`**: `"frappe.core.doctype.session_default_settings.session_default_settings.clear_session_defaults"`
- **Hook `jinja`**: `{"methods": "frappe.utils.jinja_globals", "filters": ["frappe.utils.data.global_date_format", "frappe.utils.markdown", "frappe.website.utils.abs_url"]}`
- **Hook `extend_bootinfo`**: `["frappe.utils.telemetry.add_bootinfo", "frappe.core.doctype.user_permission.user_permission.send_user_permissions"]`
- **Hook `permission_query_conditions`**: `{"Event": "frappe.desk.doctype.event.event.get_permission_query_conditions", "ToDo": "frappe.desk.doctype.todo.todo.get_permission_query_conditions", "User": "frappe.core.doctype.user.user.get_permission_query_conditions", "Dashboard Settings": "frap ...`
- **Hook `has_permission`**: `{"Event": "frappe.desk.doctype.event.event.has_permission", "ToDo": "frappe.desk.doctype.todo.todo.has_permission", "Note": "frappe.desk.doctype.note.note.has_permission", "User": "frappe.core.doctype.user.user.has_permission", "Dashboard Chart": "fr ...`
- **Hook `doc_events`**: `{"*": {"on_update": ["frappe.desk.notifications.clear_doctype_notifications", "frappe.workflow.doctype.workflow_action.workflow_action.process_workflow_actions", "frappe.core.doctype.file.utils.attach_files_to_document", "frappe.automation.doctype.as ...`


### `visaguy_business` (internal)

- **Identity**: title=Visaguy Business, publisher=Fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_business.git` branch `develop` HEAD `301dbee040c613071a3c25e186e605d8fbd2e006` (short `301dbee`); dirty files: 0
- **Hooks**: `/apps/visaguy_business/visaguy_business/hooks.py`
- **Purpose**: ## Visaguy Business \| Visaguy B2B \| #### License \| mit
- **Fixtures (target DocTypes)**: `Account`, `Price List`, `Customer Group`, `Custom DocPerm`, `Role`, `Role Profile`, `Client Script`, `Custom Field`, `Property Setter`
- **Patches**: 3 (first: `[pre_model_sync]`, `[post_model_sync]`, `visaguy_business.patches.business_client_user`)
- **Sample whitelisted methods**: `generate_preliminary_documents` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/generate_preliminary_documents.py:7), `get_applicant_files` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/get_applicant_files.py:4), `get_invoice_items` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/get_invoice_items.py:6), `get_business_details` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/get_business_details.py:3), `get_visa_price` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/get_visa_price.py:5), `create_process_file` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:12), `request_payment_for_visa_order` (/home/fasil/fasil-bench-v15/apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:240)
- **Cross-app imports sample**: `import frappe` at `apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:...`, `from processflo.processflo.doctype.pf_pr` at `apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:...`, `from visaguy_business.functions.api.gene` at `apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:...`, `from erpnext.accounts.doctype.payment_re` at `apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:...`, `from erpnext.controllers.accounts_contro` at `apps/visaguy_business/visaguy_business/functions/api/create_process_file.py:...`
- **Integration settings DocTypes**: `business_client_settings`
- **Hook `permission_query_conditions`**: `{"Business Client Visa Order": "visaguy_business.visaguy_business.doctype.business_client_visa_order.business_client_visa_order.get_permission_query_conditions", "Sales Invoice": "visaguy_business.overrides.sales_invoice_query_permission.get_permissi ...`
- **Hook `has_permission`**: `{"Sales Invoice": "visaguy_business.overrides.sales_invoice_permission.has_permission"}`
- **Hook `doc_events`**: `{"Payment Entry": {"on_submit": "visaguy_business.functions.update_wallet_on_payment_submit.update_wallet_on_payment_submit"}, "PF Process File": {"on_update": "visaguy_business.functions.check_process_completion.check_process_completion"}, "FF File  ...`


### `erpnext` (external)

- **Identity**: title=ERPNext, publisher=Frappe Technologies Pvt. Ltd., version=15.106.0, license=GNU General Public License (v3)
- **Source**: `https://github.com/frappe/erpnext.git` branch `version-15` HEAD `4dd9f0b25545a034ae3cc2012dc5a1049449c5b7` (short `4dd9f0b255`); dirty files: 0
- **Hooks**: `/apps/erpnext/erpnext/hooks.py`
- **Purpose**: <div align="center"> \| <a href="https://erpnext.com"> \| <img src="https://raw.githubusercontent.com/frappe/erpnext/develop/erpnext/public/images/erpnext-logo.png" height="128"> \| </a> \| <h2>ERPNext</h2> \| <p align="center">
- **Node dependencies**: `onscan.js`
- **Override DocType classes**: `Address`
- **Override whitelisted methods**: `frappe.www.contact.send_message`
- **Website route rules**: 24
- **Scheduler events**: `hourly`, `hourly_maintenance`, `daily_maintenance`, `weekly`, `monthly_long`
- **Patches**: 433 (first: `[pre_model_sync]`, `erpnext.patches.v12_0.update_is_cancelled_field`, `erpnext.patches.v11_0.rename_production_order_to_work_order`, `erpnext.patches.v13_0.add_bin_unique_constraint`, `erpnext.patches.v11_0.refactor_naming_series`)
- **Sample whitelisted methods**: `declare_enquiry_lost` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/quotation/quotation.py:256), `make_sales_order` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/quotation/quotation.py:351), `make_sales_invoice` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/quotation/quotation.py:500), `get_ordered_items` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/quotation/quotation.py:624), `create_receiver_list` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/sms_center/sms_center.py:43), `send_sms` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/sms_center/sms_center.py:170), `get_customer_group_details` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/customer/customer.py:168), `make_quotation` (/home/fasil/fasil-bench-v15/apps/erpnext/erpnext/selling/doctype/customer/customer.py:431)
- **Cross-app imports sample**: `import frappe` at `apps/erpnext/erpnext/__init__.py:...`, `from frappe.utils.user import is_website` at `apps/erpnext/erpnext/__init__.py:...`, `from frappe.contacts.address_and_contact` at `apps/erpnext/erpnext/selling/doctype/customer/customer.py:...`, `from frappe.model.mapper import get_mapp` at `apps/erpnext/erpnext/selling/doctype/customer/customer.py:...`, `from frappe.model.naming import set_name` at `apps/erpnext/erpnext/selling/doctype/customer/customer.py:...`
- **Integration settings DocTypes**: `plaid_settings`, `crm_settings`, `voice_call_settings`, `incoming_call_settings`
- **Hook `has_website_permission`**: `{"Sales Order": "erpnext.controllers.website_list_for_contact.has_website_permission", "Quotation": "erpnext.controllers.website_list_for_contact.has_website_permission", "Sales Invoice": "erpnext.controllers.website_list_for_contact.has_website_perm ...`
- **Hook `after_install`**: `"erpnext.setup.install.after_install"`
- **Hook `before_install`**: `["erpnext.setup.install.check_frappe_version"]`
- **Hook `jinja`**: `{"methods": ["erpnext.stock.serial_batch_bundle.get_serial_or_batch_nos"]}`
- **Hook `extend_bootinfo`**: `["erpnext.support.doctype.service_level_agreement.service_level_agreement.add_sla_doctypes", "erpnext.startup.boot.bootinfo"]`
- **Hook `doc_events`**: `{"*": {"validate": ["erpnext.support.doctype.service_level_agreement.service_level_agreement.apply", "erpnext.setup.doctype.transaction_deletion_record.transaction_deletion_record.check_for_running_deletion_job"]}, "tuple(period_closing_doctypes)": { ...`
- **Hook `payment_gateway_enabled`**: `"erpnext.accounts.utils.create_payment_gateway_account"`
- **Hook `default_roles`**: `[{"role": "Customer", "doctype": "Contact", "email_field": "email_id"}, {"role": "Supplier", "doctype": "Contact", "email_field": "email_id"}]`


### `visaguy_hrms` (internal)

- **Identity**: title=Visaguy Hrms, publisher=Tridz, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_hrms.git` branch `main` HEAD `94d341ae86e0ee1a084e02a6ae255aa85779a43c` (short `94d341a`); dirty files: 0
- **Hooks**: `/apps/visaguy_hrms/visaguy_hrms/hooks.py`
- **Purpose**: ## Visaguy Hrms \| HR module Customizatios for visa guy \| #### License \| mit
- **Override DocType classes**: `Interview`, `Expense Claim`, `Employee`
- **Override whitelisted methods**: `hrms.api.get_leave_types`, `frappe.core.doctype.communication.email.make`
- **Fixtures (target DocTypes)**: `Workflow`, `Workflow State`, `Notification`, `Appointment Letter Template`, `Interview Type`, `Email Template`, `Server Script`, `Client Script`, `Role`, `Designation`, `Insights Query`, `Insights Chart`, `Insights Dashboard`, `Print Format`, `Custom HTML Block`, `Leave Type`, `Salary Component`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `get_leave_types` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/api/get_leave_types.py:4), `make_override` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/email_send_override.py:25), `get_employee_local_date` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/timesheet_server_scripts.py:102), `calculate_taxes` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/expense_claim_doctype_class_override.py:310), `make_bank_entry` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/expense_claim_doctype_class_override.py:439), `get_expense_claim_account_and_cost_center` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/expense_claim_doctype_class_override.py:483), `get_expense_claim_account` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/expense_claim_doctype_class_override.py:491), `get_advances` (/home/fasil/fasil-bench-v15/apps/visaguy_hrms/visaguy_hrms/custom_scripts/expense_claim_doctype_class_override.py:507)
- **Cross-app imports sample**: `import frappe` at `apps/visaguy_hrms/visaguy_hrms/api/get_leave_types.py:...`, `from frappe.utils import getdate` at `apps/visaguy_hrms/visaguy_hrms/api/get_leave_types.py:...`, `import frappe` at `apps/visaguy_hrms/visaguy_hrms/custom_scripts/appointment_letter_server_scripts.py:...`, `from frappe import _` at `apps/visaguy_hrms/visaguy_hrms/custom_scripts/appointment_letter_server_scripts.py:...`, `from fileflo.document_fetch import` at `apps/visaguy_hrms/visaguy_hrms/custom_scripts/appointment_letter_server_scripts.py:...`
- **Integration settings DocTypes**: `tvg_hr_settings`
- **Hook `permission_query_conditions`**: `{"Appraisal Record": "visaguy_hrms.overrides.appraisal_record_permission_query.get_permission_query_conditions", "Leave Application": "visaguy_hrms.overrides.leave_application_permission_query.get_permission_query_conditions", "Timesheet": "visaguy_h ...`
- **Hook `has_permission`**: `{"Notification Settings": "visaguy_hrms.custom_scripts.notification_settings_server_scripts.has_permission"}`
- **Hook `doc_events`**: `{"Interview": {"after_insert": "visaguy_hrms.custom_scripts.interview_server_scripts.send_interview_emails", "before_save": "visaguy_hrms.custom_scripts.interview_server_scripts.set_full_resume_url", "before_submit": "visaguy_hrms.custom_scripts.inte ...`


### `visaguy_crm` (internal)

- **Identity**: title=Visaguy Crm, publisher=Visaguy Crm, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_crm.git` branch `main` HEAD `b59c3ef2ce25a3156f13a5e06f11dbd305763fbf` (short `b59c3ef`); dirty files: 0
- **Hooks**: `/apps/visaguy_crm/visaguy_crm/hooks.py`
- **Purpose**: ## Visaguy Crm \| Visaguy Crm \| #### License \| mit
- **Override DocType classes**: `Payment Request`
- **Override whitelisted methods**: `fileflo.data_collection.fetch_form_data`, `fileflo.data_collection.add_form_data`, `fileflo.form_generation.generate_form`
- **Fixtures (target DocTypes)**: `Workflow`, `Workflow State`, `Workflow Action Master`, `Client Script`, `Insights Dashboard`, `Insights Query`, `Insights Chart`, `Role`, `Print Format`, `Custom HTML Block`, `Workspace`
- **Patches**: 4 (first: `[pre_model_sync]`, `[post_model_sync]`, `visaguy_crm.patches.fix_lead_assignment_mismatch`, `visaguy_crm.patches.remove_lead_designated_without_assignment`)
- **Frontend bundles**: app_js=['visaguy_crm.bundle.js'], app_css=[], web_js=[], web_css=[]
- **Sample whitelisted methods**: `generate_form` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/form_generation_override.py:6), `(inline)` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/overrides/user_search_query_override.py:4), `fetch_actions` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/visaguy_crm/doctype/process_file/process_file.py:80), `get_lead_managers` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/visaguy_crm/report/lead_manager_incentive_report/lead_manager_incentive_report.py:107), `update_applicant_details` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/api/update_applicant_details.py:5), `create_process_file` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/allocated_to_process_file.py:48), `document_fetch_from_template` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/allocated_to_process_file.py:442), `fetch_form_details` (/home/fasil/fasil-bench-v15/apps/visaguy_crm/visaguy_crm/data_collecting_form.py:8)
- **Cross-app imports sample**: `import frappe` at `apps/visaguy_crm/visaguy_crm/form_generation_override.py:...`, `from fileflo.form_generation import gene` at `apps/visaguy_crm/visaguy_crm/form_generation_override.py:...`, `import frappe` at `apps/visaguy_crm/visaguy_crm/overrides/allocate_lead.py:...`, `import frappe` at `apps/visaguy_crm/visaguy_crm/overrides/ff_file_collection_on_trash.py:...`, `import frappe` at `apps/visaguy_crm/visaguy_crm/overrides/ff_file_collection_restrictions.py:...`
- **Integration settings DocTypes**: `tvg_crm_settings`
- **Hook `permission_query_conditions`**: `{"Lead": "visaguy_crm.overrides.lead_restriction.lead_restriction", "PF Process File": "visaguy_crm.pf_department_restriction.get_permission_query_conditions", "Sales Order": "visaguy_crm.overrides.sales_order_restrictions.sales_order_permission_quer ...`
- **Hook `has_permission`**: `{"Lead": "visaguy_crm.overrides.lead_permission.has_permission"}`
- **Hook `doc_events`**: `{"Lead": {"before_insert": ["visaguy_crm.customer_creation.customer_creation"], "after_insert": ["visaguy_crm.server_scripts.lead.lead_hooks.auto_assign_lead_to_consultant"], "validate": ["visaguy_crm.customer_creation.validate_payment_confirmed", "v ...`


### `payments` (external)

- **Identity**: title=Payments, publisher=Frappe Technologies, version=0.0.1, license=MIT
- **Source**: `https://github.com/frappe/payments.git` branch `version-15` HEAD `68b54a752f41e9138af000e0b87915361172095c` (short `68b54a7`); dirty files: 0
- **Hooks**: `/apps/payments/payments/hooks.py`
- **Purpose**: # Payments \| A payments app for frappe. \| ## Installation \| 1. Install [bench & frappe](https://frappeframework.com/docs/v14/user/en/installation). \| 2. Once setup is complete, add the payments app to your bench by running \| ```
- **Override DocType classes**: `Web Form`
- **Override whitelisted methods**: `frappe.website.doctype.web_form.web_form.accept`
- **Scheduler events**: `all`
- **Sample whitelisted methods**: `(inline)` (/home/fasil/fasil-bench-v15/apps/payments/payments/overrides/payment_webform.py:56), `make_payment` (/home/fasil/fasil-bench-v15/apps/payments/payments/templates/pages/stripe_checkout.py:79), `check_mandate` (/home/fasil/fasil-bench-v15/apps/payments/payments/templates/pages/gocardless_checkout.py:54), `make_payment` (/home/fasil/fasil-bench-v15/apps/payments/payments/templates/pages/braintree_checkout.py:56), `make_payment` (/home/fasil/fasil-bench-v15/apps/payments/payments/templates/pages/razorpay_checkout.py:66), `confirm_payment` (/home/fasil/fasil-bench-v15/apps/payments/payments/templates/pages/gocardless_confirmation.py:34), `get_checkout_url` (/home/fasil/fasil-bench-v15/apps/payments/payments/utils/utils.py:28), `get_express_checkout_details` (/home/fasil/fasil-bench-v15/apps/payments/payments/payment_gateways/doctype/paypal_settings/paypal_settings.py:265)
- **Cross-app imports sample**: `from frappe import _` at `apps/payments/payments/config/desktop.py:...`, `import frappe` at `apps/payments/payments/overrides/payment_webform.py:...`, `from frappe.core.doctype.file.utils impo` at `apps/payments/payments/overrides/payment_webform.py:...`, `from frappe.rate_limiter import rate_lim` at `apps/payments/payments/overrides/payment_webform.py:...`, `from frappe.utils import flt` at `apps/payments/payments/overrides/payment_webform.py:...`
- **Service keyword hits**: `razorpay`
- **Integration settings DocTypes**: `paypal_settings`, `razorpay_settings`, `paytm_settings`, `braintree_settings`, `gocardless_settings`, `stripe_settings`, `mpesa_settings`
- **Hook `after_install`**: `"payments.utils.make_custom_fields"`
- **Hook `before_install`**: `"payments.utils.before_install"`


### `india_compliance` (external)

- **Identity**: title=India Compliance, publisher=Resilient Tech, version=15.18.0, license=GNU General Public License (v3)
- **Source**: `https://github.com/resilient-tech/india-compliance.git` branch `version-15` HEAD `bde15f489844fb635690cff26715273ca617cbd8` (short `bde15f48`); dirty files: 0
- **Hooks**: `/apps/india_compliance/india_compliance/hooks.py`
- **Purpose**: <div align="center"> \| <h1><a href="https://indiacompliance.app">India Compliance</a></h1> \| Simple, yet powerful compliance solutions for Indian businesses \| [![Server Tests](https://github.com/resilient-tech/india-compliance/actions/workflows/server-tests.yml/badge.svg)](https://github.com/resilient-tech/india-compliance/actions/workflows/server-tests.yml) \| </div> \| ## Introduction
- **Required apps**: `frappe/erpnext`
- **Override DocType classes**: `Customize Form`
- **Override whitelisted methods**: `erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents`
- **Patches**: 77 (first: `[pre_model_sync]`, `execute:import frappe; frappe.delete_doc_if_exists("DocType", "GSTIN")`, `india_compliance.patches.v15.remove_duplicate_web_template`, `[post_model_sync]`, `india_compliance.patches.v14.set_default_for_overridden_accounts_setting`)
- **Sample whitelisted methods**: `fetch_to_customize` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/overrides/customize_form.py:14), `save_customization` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/overrides/customize_form.py:25), `get_audit_trail_doctypes` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/utils.py:9), `disable_audit_trail_notification` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/utils.py:21), `enable_audit_trail` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/utils.py:26), `get_relevant_doctypes` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/audit_trail/report/audit_trail/audit_trail.py:406), `get_party_details_for_subcontracting` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/gst_india/overrides/transaction.py:933), `get_gst_details` (/home/fasil/fasil-bench-v15/apps/india_compliance/india_compliance/gst_india/overrides/transaction.py:964)
- **Cross-app imports sample**: `import frappe` at `apps/india_compliance/india_compliance/audit_trail/overrides/accounts_settings.py:...`, `from frappe import _` at `apps/india_compliance/india_compliance/audit_trail/overrides/accounts_settings.py:...`, `from india_compliance.audit_trail.se` at `apps/india_compliance/india_compliance/audit_trail/overrides/accounts_settings.py:...`, `import frappe` at `apps/india_compliance/india_compliance/audit_trail/overrides/customize_form.py:...`, `from frappe import _` at `apps/india_compliance/india_compliance/audit_trail/overrides/customize_form.py:...`
- **Integration settings DocTypes**: `gst_settings`
- **Hook `after_install`**: `"india_compliance.install.after_install"`
- **Hook `before_install`**: `"india_compliance.patches.check_version_compatibility.execute"`
- **Hook `after_migrate`**: `"india_compliance.audit_trail.setup.after_migrate"`
- **Hook `before_migrate`**: `"india_compliance.patches.check_version_compatibility.execute"`
- **Hook `jinja`**: `{"methods": ["india_compliance.gst_india.utils.get_state", "india_compliance.gst_india.utils.jinja.add_spacing", "india_compliance.gst_india.utils.jinja.get_supply_type", "india_compliance.gst_india.utils.jinja.get_sub_supply_type", "india_compliance ...`
- **Hook `doc_events`**: `{"Address": {"validate": ["india_compliance.gst_india.overrides.address.validate", "india_compliance.gst_india.overrides.party.set_docs_with_previous_gstin"], "on_update": ["india_compliance.gst_india.overrides.address.update_party_gstin_and_gst_cate ...`
- **Install script**: `install.py` present


### `visaguy_helpdesk` (internal)

- **Identity**: title=Visaguy Helpdesk, publisher=fasil@tridz.com, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_helpdesk.git` branch `develop` HEAD `1692b383e6254208265c38f4a7aeec40b6a4275d` (short `1692b38`); dirty files: 0
- **Hooks**: `/apps/visaguy_helpdesk/visaguy_helpdesk/hooks.py`
- **Purpose**: ### Visaguy Helpdesk \| Customizations for visaguy \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Override DocType classes**: `HD Ticket`
- **Fixtures (target DocTypes)**: `Role`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `assign_agent` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:418), `get_last_communication` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:472), `new_comment` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:523), `reply_via_agent` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:540), `(inline)` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:675), `mark_seen` (/home/fasil/fasil-bench-v15/apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:802)
- **Cross-app imports sample**: `from frappe.core.page.permission_ma` at `apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:...`, `from frappe.desk.form.assign_to imp` at `apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:...`, `from frappe.desk.form.assign_to imp` at `apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:...`, `from frappe.desk.form.assign_to imp` at `apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:...`, `from frappe.model.document import D` at `apps/visaguy_helpdesk/visaguy_helpdesk/server_scripts/hd_ticket_class_override.py:...`
- **Integration settings DocTypes**: `tvg_hd_settings`
- **Hook `permission_query_conditions`**: `{"HD Ticket": "visaguy_helpdesk.server_scripts.hd_ticket_restriction.get_permission_query_conditions"}`
- **Hook `doc_events`**: `{"ToDo": {"validate": "visaguy_helpdesk.server_scripts.todo_hooks.validate_todo"}, "HD Ticket": {"before_insert": "visaguy_helpdesk.server_scripts.hd_ticket_hooks.set_agent_group", "before_save": "visaguy_helpdesk.server_scripts.hd_ticket_hooks.set_a ...`


### `insights` (external)

- **Identity**: title=Frappe Insights, publisher=Frappe Technologies Pvt. Ltd., version=2.2.14, license=GNU GPLv3
- **Source**: `https://github.com/frappe/insights.git` branch `main` HEAD `c9af45de73b3c71de053f33f78629407a2943bb3` (short `c9af45d`); dirty files: 1
- **Hooks**: `/apps/insights/insights/hooks.py`
- **Purpose**: <div align="center" markdown="1"> \| <img src=".github/new-logo.svg" alt="Frappe Insights logo" width="124"/> \| <h1>Frappe Insights</h1> \| **Simple. Crafted. Powerful. Data Analysis.** \| ![GitHub issues](https://img.shields.io/github/issues/frappe/insights) \| ![GitHub license](https://img.shields.io/github/license/frappe/insights)
- **Website route rules**: 1
- **Fixtures (target DocTypes)**: `Insights Data Source`
- **Scheduler events**: `all`
- **Patches**: 45 (first: `[pre_model_sync]`, `insights.patches.rename_doctypes`, `insights.patches.convert_duration_to_float`, `execute:frappe.delete_doc('DocType', 'Query Filter', ignore_missing=True)`, `execute:frappe.delete_doc('DocType', 'Query Field', ignore_missing=True)`)
- **Sample whitelisted methods**: `reset_insights_cache` (/home/fasil/fasil-bench-v15/apps/insights/insights/cache_utils.py:31), `(inline)` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/__init__.py:11), `(inline)` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/__init__.py:17), `(inline)` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/__init__.py:43), `(inline)` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/queries.py:9), `(inline)` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/queries.py:55), `create_chart` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/queries.py:79), `pivot` (/home/fasil/fasil-bench-v15/apps/insights/insights/api/queries.py:86)
- **Cross-app imports sample**: `import frappe` at `apps/insights/insights/api/__init__.py:...`, `from frappe.integrations.utils import ma` at `apps/insights/insights/api/__init__.py:...`, `from frappe.rate_limiter import rate_lim` at `apps/insights/insights/api/__init__.py:...`, `from insights.decorators import check_ro` at `apps/insights/insights/api/__init__.py:...`, `import frappe` at `apps/insights/insights/api/alerts.py:...`
- **Integration settings DocTypes**: `insights_settings`
- **Hook `has_permission`**: `{"Insights Data Source": "insights.overrides.has_permission", "Insights Table": "insights.overrides.has_permission", "Insights Query": "insights.overrides.has_permission", "Insights Dashboard": "insights.overrides.has_permission"}`


### `employee_self_service` (external)

- **Identity**: title=Employee Self Service, publisher=Nesscale Solutions Private Limited, version=2.1.29, license=MIT
- **Source**: `https://github.com/nesscale-com/employee_self_service.git` branch `version-15` HEAD `f3c1e43e93465656e7d9aba16f6418ff855f2081` (short `f3c1e43`); dirty files: 0
- **Hooks**: `/apps/employee_self_service/employee_self_service/hooks.py`
- **Purpose**: # Employee Self Service \| ## Description \| Employee Self-Service is a Frappe app that allows employees to access and manage their own HR-related information and perform various self-service tasks. This app requires ERPNext and HRMS to be installed and running. Additionally, the chat feature of Frappe (Frappe's Chat application) is required for certain functionalities. \| ## Installation \| 1. **Prerequisites** \| Before installing the Employee Self-Service app, make sure you have the following requirements met:
- **Python requirements**: `wrapt`, `pyfcm`
- **Fixtures (target DocTypes)**: `ESS Notification`, `ESS Notification Template`
- **Scheduler events**: `daily`
- **Sample whitelisted methods**: `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/visit.py:17), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/visit.py:64), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/visit.py:83), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/visit.py:114), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/location.py:36), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/translation.py:11), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/translation.py:30), `(inline)` (/home/fasil/fasil-bench-v15/apps/employee_self_service/employee_self_service/mobile/order.py:19)
- **Cross-app imports sample**: `from employee_self_service.utils import` at `apps/employee_self_service/employee_self_service/background_jobs/__init__.py:...`, `import frappe` at `apps/employee_self_service/employee_self_service/background_jobs/__init__.py:...`, `from frappe.utils import (` at `apps/employee_self_service/employee_self_service/background_jobs/__init__.py:...`, `from frappe import _` at `apps/employee_self_service/employee_self_service/config/desktop.py:...`, `import frappe` at `apps/employee_self_service/employee_self_service/constants/custom_fields.py:...`
- **Service keyword hits**: `fcm`
- **Integration settings DocTypes**: `employee_self_service_settings`, `ess_notification_settings`
- **Hook `after_install`**: `"employee_self_service.setup.after_install"`
- **Hook `after_migrate`**: `"employee_self_service.setup.after_install"`
- **Hook `jinja`**: `{"methods": ["employee_self_service.utils.strip_and_clean_html"]}`
- **Hook `doc_events`**: `{"*": {"after_insert": "employee_self_service.send_notification.notification", "on_update": "employee_self_service.send_notification.notification", "on_submit": "employee_self_service.send_notification.notification", "before_cancel": "employee_self_s ...`


### `the_visaguy` (internal)

- **Identity**: title=The Visa Guy, publisher=Fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tvgglobal/the_visaguy.git` branch `main` HEAD `e690b5b1ac897874fb33439fa429e2aee103cc3e` (short `e690b5b`); dirty files: 0
- **Hooks**: `/apps/the_visaguy/the_visaguy/hooks.py`
- **Purpose**: ### The Visa Guy \| The Visa Guy customizations \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Fixtures (target DocTypes)**: `Custom Field`, `Workspace`, `Custom HTML Block`, `Insights Query`, `Insights Chart`
- **Scheduler events**: `daily`
- **Patches**: 3 (first: `[pre_model_sync]`, `[post_model_sync]`, `the_visaguy.patches.enable_whatsapp_in_customer`)
- **Sample whitelisted methods**: `get_invoice_items` (/home/fasil/fasil-bench-v15/apps/the_visaguy/the_visaguy/tvg_business/api/get_invoice_items.py:6), `get_visa_price` (/home/fasil/fasil-bench-v15/apps/the_visaguy/the_visaguy/tvg_business/api/get_visa_price.py:4), `convert_to_crm_lead` (/home/fasil/fasil-bench-v15/apps/the_visaguy/the_visaguy/tvg_crm/doctype/raw_lead/raw_lead.py:19), `get_visa_types` (/home/fasil/fasil-bench-v15/apps/the_visaguy/the_visaguy/tvg_core/doctype/destination_configuration/destination_configuration.py:25), `get_visa_types_for_nationalites` (/home/fasil/fasil-bench-v15/apps/the_visaguy/the_visaguy/tvg_core/doctype/destination_configuration/destination_configuration.py:42)
- **Cross-app imports sample**: `from frappe.tests.utils` at `apps/the_visaguy/the_visaguy/communications/doctype/whatsapp_default/test_whatsapp_default.py:...`, `import frappe` at `apps/the_visaguy/the_visaguy/communications/doctype/whatsapp_default/whatsapp_default.py:...`, `from frappe.model.document im` at `apps/the_visaguy/the_visaguy/communications/doctype/whatsapp_default/whatsapp_default.py:...`, `from frap` at `apps/the_visaguy/the_visaguy/communications/doctype/whatsapp_default_templates/whatsapp_default_templates.py:...`, `from frap` at `apps/the_visaguy/the_visaguy/communications/doctype/whatsapp_feedback_defaults/whatsapp_feedback_defaults.py:...`
- **Service keyword hits**: `whatsapp`, `sap`
- **Hook `permission_query_conditions`**: `{"Raw Lead": "the_visaguy.tvg_crm.doctype.raw_lead.raw_lead.permission_query"}`
- **Hook `doc_events`**: `{"WhatsApp Message": {"after_insert": ["the_visaguy.handlers.receive_feedback.receive_feedback"]}, "Lead": {"on_update": "the_visaguy.handlers.whatsapp_message.send_lead_updates"}, "CRM Lead": {"on_update": ["the_visaguy.handlers.whatsapp_message.sen ...`


### `waflo` (internal)

- **Identity**: title=WAFlo, publisher=Tridz Technologies Pvt. Ltd., version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/waflo.git` branch `develop` HEAD `2167958816b55743c13a81fb94ce5673dd9834a3` (short `2167958`); dirty files: 0
- **Hooks**: `/apps/waflo/waflo/hooks.py`
- **Purpose**: # WhatsApp Flo (WAFlo) \| **WAFlo** is a Frappe-based custom app that automates WhatsApp template messaging using a step-by-step conversational flow engine. It enables dynamic, condition-based conversations with users over WhatsApp \| --- \| ## 🚀 Features \| - Define WhatsApp message flows using DocTypes \| - Trigger messages based on exact text, regex, contains, or any keyword
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `retry_message` (/home/fasil/fasil-bench-v15/apps/waflo/waflo/waflo/messaging/retry_message.py:5)
- **Cross-app imports sample**: `import frappe` at `apps/waflo/waflo/utils.py:...`, `from frappe.utils import get_url` at `apps/waflo/waflo/utils.py:...`, `from frappe.tests.utils import FrappeTe` at `apps/waflo/waflo/waflo/doctype/wf_account_settings/test_wf_account_settings.py:...`, `from frappe.model.document import Docume` at `apps/waflo/waflo/waflo/doctype/wf_account_settings/wf_account_settings.py:...`, `from frappe.tests.utils import FrappeTe` at `apps/waflo/waflo/waflo/doctype/wf_active_chat_flow/test_wf_active_chat_flow.py:...`
- **Service keyword hits**: `whatsapp`, `sap`
- **Integration settings DocTypes**: `wf_account_settings`, `wf_settings`
- **Hook `doc_events`**: `{"WhatsApp Message": {"after_insert": ["waflo.waflo.flow.processor.process_incoming_whatsapp_message"]}, "WhatsApp Notification Log": {"after_insert": ["waflo.waflo.doctype.wf_settings.wf_settings.process_retry_message"]}}`


### `fileflo` (internal)

- **Identity**: title=Fileflo, publisher=jishnusunip@gmail.com, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/FileFlo.git` branch `fix/mandatory-file` HEAD `6683010e89d9209363e6ba3881f4a90a47420bd2` (short `6683010`); dirty files: 0
- **Hooks**: `/apps/fileflo/fileflo/hooks.py`
- **Purpose**: ## Fileflo \| FileFlo is an app designed to simplify the process of adding, organizing, and managing your documents, ensuring efficient and hassle-free document handling. \| #### License \| mit
- **Website route rules**: 1
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Frontend bundles**: app_js=['/assets/fileflo/js/form_creation.js', '/assets/fileflo/js/document_fetch.js', '/assets/fileflo/js/download_zip.js'], app_css=[], web_js=[], web_css=[]
- **Sample whitelisted methods**: `get_settings` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/settings.py:4), `generate_form` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/form_generation.py:4), `download_files_as_zip` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/download_file.py:9), `document_fetch` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/document_fetch.py:8), `fetch_form_data` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/data_collection.py:5), `get_header_footer` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/data_collection.py:114), `add_form_data` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/data_collection.py:126), `add_form_data` (/home/fasil/fasil-bench-v15/apps/fileflo/fileflo/data_collection.py:137)
- **Cross-app imports sample**: `import frappe` at `apps/fileflo/fileflo/data_collection.py:...`, `import frappe` at `apps/fileflo/fileflo/document_fetch.py:...`, `import frappe` at `apps/fileflo/fileflo/download_file.py:...`, `from frappe import _` at `apps/fileflo/fileflo/download_file.py:...`, `from frappe.utils import get_files_path,` at `apps/fileflo/fileflo/download_file.py:...`
- **Integration settings DocTypes**: `fileflo_settings`


### `raven` (external)

- **Identity**: title=Raven, publisher=The Commit Company (Algocode Technologies Pvt. Ltd.), version=2.7.1, license=AGPLv3
- **Source**: `git@tridz:The-Commit-Company/raven.git` branch `main` HEAD `dfde9b1e4a8e1da526a63891e78b5d31404b38d7` (short `dfde9b1e`); dirty files: 0
- **Hooks**: `/apps/raven/raven/hooks.py`
- **Purpose**: <p align="center"> \| <a href="https://github.com/The-Commit-Company/raven"> \| <img src="raven_logo.png" alt="Raven logo" height="100" /> \| </a> \| <hr /> \| <p align="center">Enterprise-first messaging platform that seamlessly integrates with your ERP
- **Website route rules**: 2
- **Scheduler events**: `daily_maintenance`
- **Patches**: 17 (first: `[pre_model_sync]`, `[post_model_sync]`, `raven.patches.v1_2.create_raven_users`, `raven.patches.v1_3.create_raven_message_indexes #23`, `raven.patches.v1_3.update_all_messages_to_include_message_content #2`)
- **Sample whitelisted methods**: `get_document_ai_processors` (/home/fasil/fasil-bench-v15/apps/raven/raven/ai/google_ai.py:10), `get_list_of_processors` (/home/fasil/fasil-bench-v15/apps/raven/raven/ai/google_ai.py:128), `get_available_processor_types` (/home/fasil/fasil-bench-v15/apps/raven/raven/ai/google_ai.py:224), `create_document_processor` (/home/fasil/fasil-bench-v15/apps/raven/raven/ai/google_ai.py:232), `delete_document_processor` (/home/fasil/fasil-bench-v15/apps/raven/raven/ai/google_ai.py:286), `get_instruction_preview` (/home/fasil/fasil-bench-v15/apps/raven/raven/api/ai_features.py:7), `get_saved_prompts` (/home/fasil/fasil-bench-v15/apps/raven/raven/api/ai_features.py:18), `get_open_ai_version` (/home/fasil/fasil-bench-v15/apps/raven/raven/api/ai_features.py:35)
- **Cross-app imports sample**: `from raven.raven_integrations.doctype.ra` at `apps/raven/raven/__init__.py:...`, `import frappe` at `apps/raven/raven/ai/agents_integration.py:...`, `from frappe import _` at `apps/raven/raven/ai/agents_integration.py:...`, `import frappe` at `apps/raven/raven/ai/ai.py:...`, `from raven.ai.agents_integration import ` at `apps/raven/raven/ai/ai.py:...`
- **Integration settings DocTypes**: `raven_settings`
- **Hook `after_install`**: `"raven.install.after_install"`
- **Hook `on_logout`**: `"raven.api.user_availability.set_user_inactive"`
- **Hook `extend_bootinfo`**: `"raven.boot.boot_session"`
- **Hook `permission_query_conditions`**: `{"Raven Channel": "raven.permissions.raven_channel_query", "Raven Message": "raven.permissions.raven_message_query", "Raven Poll": "raven.permissions.raven_poll_query", "Raven Poll Vote": "raven.permissions.raven_poll_vote_query", "Raven Workspace":  ...`
- **Hook `has_permission`**: `{"Raven Channel": "raven.permissions.channel_has_permission", "Raven Channel Member": "raven.permissions.channel_member_has_permission", "Raven Message": "raven.permissions.message_has_permission", "Raven Poll Vote": "raven.permissions.raven_poll_vot ...`
- **Hook `doc_events`**: `{"*": {"after_insert": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_document_notification", "on_update": "raven.raven_integrations.doctype.raven_document_notification.raven_document_notification.run_do ...`
- **Install script**: `install.py` present


### `helpdesk` (internal)

- **Identity**: title=Helpdesk, publisher=Frappe Technologies, version=0.10.0, license=AGPLv3
- **Source**: `git@tridz:tridz-dev/helpdesk_frk.git` branch `modification_develop_branch` HEAD `a671e5f5a4ed5c878efc9fde738026c69479bbb1` (short `a671e5f`); dirty files: 0
- **Hooks**: `/apps/helpdesk/helpdesk/hooks.py`
- **Purpose**: <div align="center" markdown="1"> \| <a href="https://frappedesk.com/"> \| <img src=".github/hd-logo.svg" height="128" alt="Frappe Helpdesk Logo"> \| </a> \| <h2>Frappe Helpdesk</h2> \| <p align="center">
- **Node dependencies**: `@typescript-eslint/eslint-plugin`, `@typescript-eslint/parser`, `eslint`, `eslint-config-prettier`, `eslint-plugin-json`, `eslint-plugin-prettier`, `eslint-plugin-tailwindcss`, `eslint-plugin-vue`, `husky`, `lint-staged`, `prettier`, `tailwindcss`, `typescript`
- **Website route rules**: 1
- **Scheduler events**: `all`
- **Patches**: 18 (first: `[pre_model_sync]`, `helpdesk.patches.change_app_name_to_helpdesk`, `helpdesk.patches.rename_doctypes_prefix_with_hd`, `helpdesk.patches.rename_frappedesk_module_references`, `helpdesk.patches.naming_autoincrement`)
- **Sample whitelisted methods**: `search_text` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/templates/components/search/search.py:4), `get_breadcrumbs` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/templates/components/breadcrumbs/breadcrumbs.py:5), `get_config` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/config.py:4), `get_preset_filters` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/general.py:5), `is_enabled` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/telemetry.py:4), `get_credentials` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/telemetry.py:13), `search` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/article.py:3), `signup` (/home/fasil/fasil-bench-v15/apps/helpdesk/helpdesk/api/account.py:9)
- **Cross-app imports sample**: `import frappe` at `apps/helpdesk/helpdesk/api/account.py:...`, `from frappe.core.doctype.user.user impor` at `apps/helpdesk/helpdesk/api/account.py:...`, `import frappe` at `apps/helpdesk/helpdesk/api/agent.py:...`, `import frappe` at `apps/helpdesk/helpdesk/api/article.py:...`, `import frappe` at `apps/helpdesk/helpdesk/api/auth.py:...`
- **Integration settings DocTypes**: `hd_settings`
- **Hook `after_install`**: `"helpdesk.setup.install.after_install"`
- **Hook `before_install`**: `"helpdesk.setup.install.before_install"`
- **Hook `after_migrate`**: `"helpdesk.search.build_index_in_background"`
- **Hook `permission_query_conditions`**: `{"HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.permission_query"}`
- **Hook `has_permission`**: `{"HD Ticket": "helpdesk.helpdesk.doctype.hd_ticket.hd_ticket.has_permission"}`
- **Hook `doc_events`**: `{"Contact": {"before_insert": "helpdesk.helpdesk.hooks.contact.before_insert"}, "Assignment Rule": {"on_trash": "helpdesk.overrides.on_assignment_rule_trash"}}`


### `crm` (internal)

- **Identity**: title=Frappe CRM, publisher=Frappe Technologies Pvt. Ltd., version=2.0.0-dev, license=AGPLv3
- **Source**: `git@tridz:tridz-dev/frappe-crm.git` branch `tridz-dev` HEAD `b3328bc92af9e31c083e611ebe0ba578d29bbcec` (short `b3328bc9`); dirty files: 0
- **Hooks**: `/apps/crm/crm/hooks.py`
- **Purpose**: <div align="center" markdown="1"> \| <a href="https://frappe.io/products/crm"> \| <img src=".github/logo.svg" height="80" alt="Frappe CRM Logo"> \| </a> \| <h1>Frappe CRM</h1> \| **Simplify Sales, Amplify Relationships**
- **Override DocType classes**: `Contact`, `Email Template`
- **Website route rules**: 1
- **Patches**: 10 (first: `[pre_model_sync]`, `crm.patches.v1_0.move_crm_note_data_to_fcrm_note`, `crm.patches.v1_0.rename_twilio_settings_to_crm_twilio_settings`, `[post_model_sync]`, `crm.patches.v1_0.create_email_template_custom_fields`)
- **Sample whitelisted methods**: `restore_defaults` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/fcrm_settings/fcrm_settings.py:12), `get_call_log` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:137), `create_lead_from_call_log` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:192), `add_contact` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.py:211), `remove_contact` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.py:222), `set_primary_contact` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.py:233), `create_deal` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_deal/crm_deal.py:308), `get_deal` (/home/fasil/fasil-bench-v15/apps/crm/crm/fcrm/doctype/crm_deal/api.py:7)
- **Cross-app imports sample**: `import frappe` at `apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:...`, `from frappe.model.document import Docume` at `apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:...`, `from crm.integrations.api import get_con` at `apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:...`, `from crm.utils import seconds_to_duratio` at `apps/crm/crm/fcrm/doctype/crm_call_log/crm_call_log.py:...`, `from frappe.tests import UnitTestCase` at `apps/crm/crm/fcrm/doctype/crm_call_log/test_crm_call_log.py:...`
- **Service keyword hits**: `whatsapp`, `sap`
- **Integration settings DocTypes**: `crm_twilio_settings`, `erpnext_crm_settings`, `crm_exotel_settings`, `fcrm_settings`, `crm_global_settings`, `crm_view_settings`
- **Hook `after_install`**: `"crm.install.after_install"`
- **Hook `before_install`**: `"crm.install.before_install"`
- **Hook `after_migrate`**: `["crm.fcrm.doctype.fcrm_settings.fcrm_settings.after_migrate"]`
- **Hook `doc_events`**: `{"Contact": {"validate": ["crm.api.contact.validate"]}, "ToDo": {"after_insert": ["crm.api.todo.after_insert"], "on_update": ["crm.api.todo.on_update"]}, "Comment": {"on_update": ["crm.api.comment.on_update"]}, "WhatsApp Message": {"validate": ["crm. ...`
- **Install script**: `install.py` present


### `visaguy_frappe_crm` (internal)

- **Identity**: title=Visaguy Frappe Crm, publisher=fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_frappe_crm.git` branch `develop` HEAD `a1e22da20247d027db3dce1188f2e77b4e43399c` (short `a1e22da`); dirty files: 1
- **Hooks**: `/apps/visaguy_frappe_crm/visaguy_frappe_crm/hooks.py`
- **Purpose**: ## Visaguy Frappe Crm \| Visaguy Frappe CRM \| #### License \| mit
- **Fixtures (target DocTypes)**: `CRM Fields Layout`, `CRM Global Settings`, `Property Setter`, `Custom DocPerm`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `handle_lead_send_form` (/home/fasil/fasil-bench-v15/apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/lead_file_collection.py:11), `get_zone_details` (/home/fasil/fasil-bench-v15/apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/apis/get_zone_details.py:4), `check_duplicate_lead` (/home/fasil/fasil-bench-v15/apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/apis/check_duplicate_lead.py:3), `get_details_of_session_user` (/home/fasil/fasil-bench-v15/apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/session_user.py:2)
- **Cross-app imports sample**: `from frappe.utils import today` at `apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/add_payment_date.py:...`, `from visaguy_frappe_crm.functions.check_` at `apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/add_payment_date.py:...`, `import frappe` at `apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/add_zone.py:...`, `from visaguy_frappe_crm.functions.sessio` at `apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/add_zone.py:...`, `from visaguy_frappe_crm.functions.check_` at `apps/visaguy_frappe_crm/visaguy_frappe_crm/functions/add_zone.py:...`
- **Integration settings DocTypes**: `crm_migration_settings`
- **Hook `permission_query_conditions`**: `{"CRM Lead": "visaguy_frappe_crm.functions.lead_restrictions.lead_restrictions", "Department": "visaguy_frappe_crm.functions.restrict_department_listing.restrict_department_listing"}`
- **Hook `doc_events`**: `{"CRM Lead": {"before_insert": ["visaguy_frappe_crm.functions.add_zone.add_zone", "visaguy_frappe_crm.functions.customer_creation.customer_creation"], "before_save": ["visaguy_frappe_crm.functions.update_number_of_applicants.update_number_of_applican ...`


### `non_profit` (external)

- **Identity**: title=Non Profit, publisher=Frappe, version=0.0.1, license=MIT
- **Source**: `https://github.com/frappe/non_profit.git` branch `develop` HEAD `ea2c88ddb04d60e7a81bfae58a1307d5f6496487` (short `ea2c88d`); dirty files: 0
- **Hooks**: `/apps/non_profit/non_profit/hooks.py`
- **Purpose**: ## Non Profit \| A Non profit app built on top of Frappe framework & ERPNext. \| People who change the world need the tools to do it! The Non Profit Modules of ERPNext is designed for a non-profit organization, so that they can deliver well on their noble cause of a better world. \| ### Installation \| Using bench, [install ERPNext](https://github.com/frappe/bench#installation) as mentioned here. \| Once ERPNext is installed, add non_profit app to your bench by running
- **Required apps**: `erpnext`
- **Override DocType classes**: `Payment Entry`
- **Scheduler events**: `daily`
- **Patches**: 1 (first: `non_profit.patches.rename_non_profit_fields`)
- **Sample whitelisted methods**: `leave` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/chapter/chapter.py:40), `send_grant_review_emails` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/grant_application/grant_application.py:40), `generate_webhook_secret` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/non_profit_settings/non_profit_settings.py:12), `revoke_key` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/non_profit_settings/non_profit_settings.py:25), `get_plans_for_membership` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/non_profit_settings/non_profit_settings.py:34), `set_company_address` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/tax_exemption_80g_certificate/tax_exemption_80g_certificate.py:44), `get_payments` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/tax_exemption_80g_certificate/tax_exemption_80g_certificate.py:65), `make_customer_and_link` (/home/fasil/fasil-bench-v15/apps/non_profit/non_profit/non_profit/doctype/member/member.py:58)
- **Cross-app imports sample**: `from frappe import _` at `apps/non_profit/non_profit/config/desktop.py:...`, `from frappe import _` at `apps/non_profit/non_profit/hooks.py:...`, `from erpnext.accounts.doctype.payment_en` at `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:...`, `from erpnext.accounts.party import get_p` at `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:...`, `from erpnext.accounts.utils import get_a` at `apps/non_profit/non_profit/non_profit/custom_doctype/payment_entry.py:...`
- **Integration settings DocTypes**: `non_profit_settings`
- **Hook `after_install`**: `"non_profit.setup.setup_non_profit"`


### `frappe_conversions_api` (internal)

- **Identity**: title=Frappe Conversions Api, publisher=fasil@tridz.com, version=0.0.1, license=agpl-3.0
- **Source**: `git@tridz:tridz-dev/frappe_conversions_api.git` branch `develop` HEAD `3a240c6492444f678328f6b1d04ecae246a83d53` (short `3a240c6`); dirty files: 0
- **Hooks**: `/apps/frappe_conversions_api/frappe_conversions_api/hooks.py`
- **Purpose**: ### Frappe Conversions Api \| Frappe App for Conversions API Integration in providers like Meta, Google \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `webhook` (/home/fasil/fasil-bench-v15/apps/frappe_conversions_api/frappe_conversions_api/api/meta/webhook.py:4)
- **Cross-app imports sample**: `import frappe` at `apps/frappe_conversions_api/frappe_conversions_api/api/meta/__init__.py:...`, `import frappe` at `apps/frappe_conversions_api/frappe_conversions_api/api/meta/webhook.py:...`, `/home/fasil/fasil-bench-v15/apps/frappe_conversi` at `apps/frappe_conversions_api/frappe_conversions_api/frappe_conversions_api/doctype/conversion_account/conversion_account.:...`, `/home/fasil/fasil-bench-v15/apps/frappe_conversi` at `apps/frappe_conversions_api/frappe_conversions_api/frappe_conversions_api/doctype/conversion_account/test_conversion_acc:...`, `4` at `apps/frappe_conversions_api/frappe_conversions_api/frappe_conversions_api/doctype/conversion_event/conversion_event.py:...`
- **Service keyword hits**: `meta`, `google`
- **Hook `after_install`**: `"frappe_conversions_api.install.after_install"`
- **Install script**: `install.py` present


### `quick_kanban` (internal)

- **Identity**: title=Quick-Kanban, publisher=tridz, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/quick_kanban.git` branch `main` HEAD `8ca57a621591aae46a9c18035fae60448ba0bcf6` (short `8ca57a6`); dirty files: 0
- **Hooks**: `/apps/quick_kanban/quick_kanban/hooks.py`
- **Purpose**: # Quick Kanban \| Quick Kanban is a Frappe app designed to enhance the default Kanban view in Frappe/ERPNext by replacing it with a Vue-based Kanban. This app aims to provide better performance and an improved user experience, especially for instances with a high volume of Kanban cards and frequent updates. \| ## Objective \| - **Vue-based Kanban View**: Improved performance and user interface. \| - **Optimized for Large Data**: Handles hundreds of cards efficiently. \| - **Seamless Integration**: Works seamlessly within the Frappe framework.
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `get_kanban_config` (/home/fasil/fasil-bench-v15/apps/quick_kanban/quick_kanban/get_beta _users.py:4)
- **Cross-app imports sample**: `import frappe` at `apps/quick_kanban/quick_kanban/get_beta _users.py:...`, `from frappe.model` at `apps/quick_kanban/quick_kanban/quick_kanban/doctype/kanban_board_highlight/kanban_board_highlight.py:...`


### `payment_integrations` (internal)

- **Identity**: title=Payment Integrations, publisher=Tridz Technologies Private Ltd, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/payment_integrations.git` branch `develop` HEAD `c424a1b8802175086e028d571837efb56dfc5f09` (short `c424a1b`); dirty files: 0
- **Hooks**: `/apps/payment_integrations/payment_integrations/hooks.py`
- **Purpose**: ### Payment Integrations \| For Payment Integration Implementations \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Required apps**: `erpnext`, `payments`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `handle_webhook` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/payment_integrations/doctype/totalpay_settings/totalpay_settings.py:168), `payment_success` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/payment_integrations/doctype/totalpay_settings/totalpay_settings.py:256), `payment_cancel` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/payment_integrations/doctype/totalpay_settings/totalpay_settings.py:266), `identify_site` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/payment_integrations/doctype/totalpay_settings/totalpay_settings.py:274), `handle_webhook` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/webhook/myfatoorah.py:5), `handle_webhook` (/home/fasil/fasil-bench-v15/apps/payment_integrations/payment_integrations/payment_gateways/totalpay.py:39)
- **Cross-app imports sample**: `import frappe` at `apps/payment_integrations/payment_integrations/install.py:...`, `import frappe` at `apps/payment_integrations/payment_integrations/integrations.py:...`, `from erpnext.selling.doctype.sales_order` at `apps/payment_integrations/payment_integrations/integrations.py:...`, `from erpnext.accounts.doctype.payment_en` at `apps/payment_integrations/payment_integrations/integrations.py:...`, `import frappe` at `apps/payment_integrations/payment_integrations/payment_gateways/totalpay.py:...`
- **Integration settings DocTypes**: `myfatoorah_settings`, `totalpay_settings`
- **Hook `after_install`**: `"payment_integrations.install.after_install"`
- **Hook `doc_events`**: `{"Payment Request": {"on_update_after_submit": "payment_integrations.integrations.on_update_after_submit"}}`
- **Install script**: `install.py` present


### `mansico_meta_integration` (external)

- **Identity**: title=Mansico Meta Integration, publisher=Mansy, version=1.2.1, license=mit
- **Source**: `git@tridz:Ahmed-Mansy-Mansico/mansico_meta_integration.git` branch `master` HEAD `8e595ea601d0d01e147303d82c8bc72d2ba749d2` (short `8e595ea`); dirty files: 1
- **Hooks**: `/apps/mansico_meta_integration/mansico_meta_integration/hooks.py`
- **Purpose**: # Mansico Meta Integration \| <div align="center"> \| <img src="https://github.com/splinter-NGoH/mansico_meta_integration/assets/73743592/4080cbd5-6f5f-48fe-877d-e28e5e795bf8" height="128"> \| <h2>Seamlessly Sync Facebook Leads with ERPNext</h2> \| </div> \| **Mansico Meta Integration** is an open-source application designed to automate the synchronization of Facebook leads with ERPNext. When clients fill out Facebook Ads instant forms, the app automatically fetches the newly created leads and generates corresponding entries in ERPNext's **Lead** doctype. Additionally, when the Lead Status is updated in ERPNext, the new status is sent back to the Meta Pixel for real-time tracking and analytics.
- **Required apps**: `erpnext`
- **Scheduler events**: `all`, `daily`, `hourly`, `weekly`, `monthly`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `get_credentials` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/sync_new_add/sync_new_add.py:8), `fetch_leads` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/sync_new_add/sync_new_add.py:242), `all` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/tasks.py:7), `daily` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/tasks.py:14), `hourly` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/tasks.py:21), `weekly` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/tasks.py:28), `monthly` (/home/fasil/fasil-bench-v15/apps/mansico_meta_integration/mansico_meta_integration/tasks.py:35)
- **Cross-app imports sample**: `/home/fasil/fasil-bench-v15/apps/mansico_meta_in` at `apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/map_lead_field/map_lead_field.py:...`, `/home/fasil/fasil-bench-v15/apps/mansico_meta_in` at `apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/meta_facebook_settings/meta_face:...`, `/home/fasil/fasil-bench-v15/apps/mansico_meta_in` at `apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/meta_facebook_settings/test_meta:...`, `from` at `apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/meta_forms/meta_forms.py:...`, `from frappe` at `apps/mansico_meta_integration/mansico_meta_integration/mansico_meta_integration/doctype/page_id/page_id.py:...`
- **Service keyword hits**: `meta`, `facebook`
- **Integration settings DocTypes**: `meta_facebook_settings`
- **Hook `doc_events`**: `{"Lead": {"validate": "mansico_meta_integration.overrides.validate_lead"}}`


### `frappe_notifier` (internal)

- **Identity**: title=Frappe Notifier, publisher=Fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/frappe_notifier.git` branch `develop` HEAD `8da76034795f5cb0d7500c9ecefcb05ff67e84dc` (short `8da7603`); dirty files: 0
- **Hooks**: `/apps/frappe_notifier/frappe_notifier/hooks.py`
- **Purpose**: # Frappe Notifier \| Push Notifications setup through Frappe Relay server \| ## Prerequisites \| - [Google Cloud Authentication](https://cloud.google.com/docs/authentication/provide-credentials-adc#how-to) \| - Firebase project with Firebase Cloud Messaging (FCM) enabled \| - Frappe Bench environment
- **Override whitelisted methods**: `notification_relay.api.get_config`, `notification_relay.api.token.add`, `notification_relay.api.token.delete`, `notification_relay.api.send_notification.user`, `notification_relay.api.send_notification.topic`, `notification_relay.api.topic.add`, `notification_relay.api.topic.remove`, `notification_relay.api.topic.subscribe`, `notification_relay.api.topic.unsubscribe`
- **Fixtures (target DocTypes)**: `Role`, `Custom DocPerm`
- **Scheduler events**: `daily`
- **Patches**: 3 (first: `[pre_model_sync]`, `[post_model_sync]`, `frappe_notifier.patches.set_active_tokens`)
- **Sample whitelisted methods**: `(inline)` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/token.py:5), `(inline)` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/token.py:21), `topic` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/send_notification.py:196), `user` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/send_notification.py:266), `get_config` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/get_config.py:6), `add` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/topic.py:7), `(inline)` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/topic.py:20), `(inline)` (/home/fasil/fasil-bench-v15/apps/frappe_notifier/frappe_notifier/api/topic.py:47)
- **Cross-app imports sample**: `import frappe` at `apps/frappe_notifier/frappe_notifier/api/get_config.py:...`, `import frappe` at `apps/frappe_notifier/frappe_notifier/api/send_notification.py:...`, `from frappe_notifier.utils.normalize_to_` at `apps/frappe_notifier/frappe_notifier/api/send_notification.py:...`, `from frappe_notifier.utils.normalize_top` at `apps/frappe_notifier/frappe_notifier/api/send_notification.py:...`, `from frappe_notifier.utils.firebase impo` at `apps/frappe_notifier/frappe_notifier/api/send_notification.py:...`
- **Service keyword hits**: `google`, `firebase`, `fcm`
- **Integration settings DocTypes**: `frappe_notifier_settings`
- **Hook `after_install`**: `"frappe_notifier.setup.setup_users"`


### `visaguy_website` (internal)

- **Identity**: title=Visaguy Website, publisher=Fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tvgglobal/visaguy_website.git` branch `develop` HEAD `1466adf8a4d1c5102c959a691940fbb3e0fd8ee2` (short `1466adf`); dirty files: 0
- **Hooks**: `/apps/visaguy_website/visaguy_website/hooks.py`
- **Purpose**: ### Visaguy Website \| Configurations for Visaguy Next Js Website \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Fixtures (target DocTypes)**: `Custom Field`, `Role`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `get_applicant_files` (/home/fasil/fasil-bench-v15/apps/visaguy_website/visaguy_website/api/get_applicant_files.py:4), `get_file_template` (/home/fasil/fasil-bench-v15/apps/visaguy_website/visaguy_website/api/get_file_template.py:10), `create_visa_order` (/home/fasil/fasil-bench-v15/apps/visaguy_website/visaguy_website/api/create_visa_order.py:11), `get_destination_items` (/home/fasil/fasil-bench-v15/apps/visaguy_website/visaguy_website/api/get_destination_items.py:10), `submit_application` (/home/fasil/fasil-bench-v15/apps/visaguy_website/visaguy_website/api/submit_application.py:14)
- **Cross-app imports sample**: `import frappe` at `apps/visaguy_website/visaguy_website/api/create_visa_order.py:...`, `import frappe` at `apps/visaguy_website/visaguy_website/api/get_applicant_files.py:...`, `from frappe import _` at `apps/visaguy_website/visaguy_website/api/get_applicant_files.py:...`, `import frappe` at `apps/visaguy_website/visaguy_website/api/get_destination_items.py:...`, `import frappe` at `apps/visaguy_website/visaguy_website/api/get_file_template.py:...`
- **Hook `permission_query_conditions`**: `{"Visaguy Website Visa Order": "visaguy_website.permissions.visa_order_permission"}`
- **Hook `doc_events`**: `{"FF File Collection": {"on_update": "visaguy_website.website_integrations.check_awaiting_action.check_awaiting_action"}, "PF Process File": {"on_update": "visaguy_website.website_integrations.check_process_completion.check_process_completion"}}`


### `frappe_whatsapp` (external)

- **Identity**: title=Frappe Whatsapp, publisher=Shridhar Patil, version=1.0.12, license=MIT
- **Source**: `https://github.com/shridarpatil/frappe_whatsapp.git` branch `master` HEAD `27f3438c2051cc7930ce845d6af2c5b54838884b` (short `27f3438`); dirty files: 0
- **Hooks**: `/apps/frappe_whatsapp/frappe_whatsapp/hooks.py`
- **Purpose**: <div align="right"> \| <a href="https://frappecloud.com/marketplace/apps/frappe_whatsapp" target="_blank"> \| <picture> \| <source media="(prefers-color-scheme: dark)" srcset="https://frappe.io/files/try-on-fc-white.png"> \| <img src="https://frappe.io/files/try-on-fc-black.png" alt="Try on Frappe Cloud" height="28" /> \| </picture>
- **Python requirements**: `python-magic`
- **Scheduler events**: `all`, `hourly`, `hourly_long`, `daily`, `daily_long`, `weekly`, `weekly_long`, `monthly`, `monthly_long`
- **Patches**: 4 (first: `[pre_model_sync]`, `[post_model_sync]`, `frappe_whatsapp.patches.set_default_in_whatsapp_settings`, `frappe_whatsapp.patches.migrate_to_multi_account`)
- **Sample whitelisted methods**: `get_progress` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/utils/bulk_messaging.py:6), `retry_failed` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/utils/bulk_messaging.py:12), `import_recipients` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/utils/bulk_messaging.py:19), `schedule_bulk_messages` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/utils/bulk_messaging.py:34), `webhook` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/utils/webhook.py:12), `handle_flow_request` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/api/flow_endpoint.py:11), `call_trigger_notifications` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/doctype/whatsapp_notification/whatsapp_notification.py:363), `fetch` (/home/fasil/fasil-bench-v15/apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/doctype/whatsapp_templates/whatsapp_templates.py:252)
- **Cross-app imports sample**: `import frappe` at `apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/api/flow_endpoint.py:...`, `from frappe import _` at `apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/api/flow_endpoint.py:...`, `import fra` at `apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/doctype/bulk_whatsapp_message/bulk_whatsapp_message.py:...`, `from frapp` at `apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/doctype/bulk_whatsapp_message/bulk_whatsapp_message.py:...`, `from frapp` at `apps/frappe_whatsapp/frappe_whatsapp/frappe_whatsapp/doctype/bulk_whatsapp_message/bulk_whatsapp_message.py:...`
- **Service keyword hits**: `whatsapp`, `sap`
- **Integration settings DocTypes**: `whatsapp_settings`
- **Hook `doc_events`**: `{"*": {"before_insert": "frappe_whatsapp.utils.run_server_script_for_doc_event", "after_insert": "frappe_whatsapp.utils.run_server_script_for_doc_event", "before_validate": "frappe_whatsapp.utils.run_server_script_for_doc_event", "validate": "frappe_ ...`


### `otp_authentication` (internal)

- **Identity**: title=Otp Authentication, publisher=jishnup@tridz.com, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/otp_authentication.git` branch `email` HEAD `f4409ba8dfc66913f9e526b320737dfd76028946` (short `f4409ba`); dirty files: 0
- **Hooks**: `/apps/otp_authentication/otp_authentication/hooks.py`
- **Purpose**: ## Otp Authentication \| otp authentication \| #### License \| mit
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Sample whitelisted methods**: `otp_verification` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_verification.py:9), `generate_api_credentials` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_verification.py:85), `check_customer_verification` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_verification.py:127), `update_customer_details` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/www/customer-details/index.py:5), `get_auth_config` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_generation.py:10), `otp_creation_and_storing` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_generation.py:21), `user_check_otp_send` (/home/fasil/fasil-bench-v15/apps/otp_authentication/otp_authentication/otp_generation.py:55)
- **Cross-app imports sample**: `import frappe` at `apps/otp_authentication/otp_authentication/config/otp_settings.py:...`, `from frappe import _` at `apps/otp_authentication/otp_authentication/config/otp_settings.py:...`, `from frappe.model.d` at `apps/otp_authentication/otp_authentication/otp_authentication/doctype/otp_settings/otp_settings.py:...`, `from frappe.te` at `apps/otp_authentication/otp_authentication/otp_authentication/doctype/otp_settings/test_otp_settings.py:...`, `import frappe` at `apps/otp_authentication/otp_authentication/otp_authentication/web_form/customer_test/customer_test.py:...`
- **Service keyword hits**: `otp`
- **Integration settings DocTypes**: `otp_settings`


### `hrms` (external)

- **Identity**: title=Frappe HR, publisher=Frappe Technologies Pvt. Ltd., version=15.45.2, license=GNU General Public License (v3)
- **Source**: `https://github.com/frappe/hrms.git` branch `version-15` HEAD `5b3285fa89658a3146bb324f33cd92aad514998c` (short `5b3285fa`); dirty files: 0
- **Hooks**: `/apps/hrms/hrms/hooks.py`
- **Purpose**: <div align="center"> \| <a href="https://frappehr.com"> \| <img src="https://raw.githubusercontent.com/frappe/hrms/develop/hrms/public/images/frappe-hr-logo.png" height="128" alt="Frappe HR Logo"> \| </a> \| <h2>Frappe HR</h2> \| <p align="center">
- **Required apps**: `frappe/erpnext`
- **Node dependencies**: `html2canvas`
- **Override DocType classes**: `Employee`, `Timesheet`, `Payment Entry`, `Project`
- **Website route rules**: 2
- **Scheduler events**: `all`, `hourly`, `hourly_long`, `daily`, `daily_long`, `weekly`, `monthly`
- **Patches**: 29 (first: `[pre_model_sync]`, `hrms.patches.v15_0.check_version_compatibility_with_frappe #2023-06-27`, `[post_model_sync]`, `hrms.patches.post_install.set_payroll_entry_status`, `hrms.patches.v1_0.rearrange_employee_fields`)
- **Frontend bundles**: app_js=['hrms.bundle.js'], app_css=[], web_js=[], web_css=[]
- **Sample whitelisted methods**: `get_timeline_data` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/overrides/employee_master.py:108), `get_retirement_date` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/overrides/employee_master.py:134), `get_payment_entry_for_employee` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/overrides/employee_payment_entry.py:74), `get_payment_reference_details` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/overrides/employee_payment_entry.py:214), `get_reference_details_for_employee` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/overrides/employee_payment_entry.py:226), `get_current_user_info` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/api/__init__.py:30), `get_current_employee_info` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/api/__init__.py:41), `get_all_employees` (/home/fasil/fasil-bench-v15/apps/hrms/hrms/api/__init__.py:62)
- **Cross-app imports sample**: `import frappe` at `apps/hrms/hrms/__init__.py:...`, `import frappe` at `apps/hrms/hrms/api/__init__.py:...`, `from frappe import _` at `apps/hrms/hrms/api/__init__.py:...`, `from frappe.model import get_permitted_f` at `apps/hrms/hrms/api/__init__.py:...`, `from frappe.model.workflow import get_wo` at `apps/hrms/hrms/api/__init__.py:...`
- **Integration settings DocTypes**: `payroll_settings`, `hr_settings`
- **Hook `after_install`**: `"hrms.install.after_install"`
- **Hook `after_migrate`**: `"hrms.setup.update_select_perm_after_install"`
- **Hook `jinja`**: `{"methods": ["hrms.utils.get_country"]}`
- **Hook `doc_events`**: `{"User": {"validate": "erpnext.setup.doctype.employee.employee.validate_employee_role", "on_update": "erpnext.setup.doctype.employee.employee.update_user_permissions"}, "Company": {"validate": "hrms.overrides.company.validate_default_accounts", "on_u ...`
- **Install script**: `install.py` present


### `processflo` (internal)

- **Identity**: title=Processflo, publisher=jishnusunip@gmail.com, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/ProcessFlo.git` branch `develop` HEAD `2f2b5657d20a778159dce0b2268c2a676ad66627` (short `2f2b565`); dirty files: 1
- **Hooks**: `/apps/processflo/processflo/hooks.py`
- **Purpose**: ## Processflo \| ProcessFlo is an app designed to simplify your process flows and actions, ensuring smooth and efficient workflow management. \| #### License \| mit
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Frontend bundles**: app_js=[], app_css=[], web_js=['/assets/processflo/js/fetch_action.js', 'assets/processflo/js/create_file_collection.js'], web_css=[]
- **Sample whitelisted methods**: `generate_file_collection` (/home/fasil/fasil-bench-v15/apps/processflo/processflo/generate_file_collection.py:6), `generate_file_collection_lead` (/home/fasil/fasil-bench-v15/apps/processflo/processflo/generate_file_collection.py:30), `generate_file_collection_process_file` (/home/fasil/fasil-bench-v15/apps/processflo/processflo/generate_file_collection.py:71), `create_process_deliverables` (/home/fasil/fasil-bench-v15/apps/processflo/processflo/processflo/doctype/pf_process_file/pf_process_file.py:42), `fetch_actions` (/home/fasil/fasil-bench-v15/apps/processflo/processflo/processflo/doctype/pf_process_file/pf_process_file.py:62)
- **Cross-app imports sample**: `import frappe` at `apps/processflo/processflo/generate_file_collection.py:...`, `from fileflo.form_generation import gene` at `apps/processflo/processflo/generate_file_collection.py:...`, `from frappe.model.document import` at `apps/processflo/processflo/processflo/doctype/pf_process_action/pf_process_action.py:...`, `from frappe.tests.utils impo` at `apps/processflo/processflo/processflo/doctype/pf_process_action/test_pf_process_action.py:...`, `from frappe.model.doc` at `apps/processflo/processflo/processflo/doctype/pf_process_deliverables/pf_process_deliverables.py:...`


### `visaguy_raven` (internal)

- **Identity**: title=Visaguy Raven, publisher=Fasil, version=0.0.1, license=mit
- **Source**: `git@tridz:tridz-dev/visaguy_raven.git` branch `develop` HEAD `330fa1b5dfb209eb061f7e6e1c355e1d98efcd9c` (short `330fa1b`); dirty files: 1
- **Hooks**: `/apps/visaguy_raven/visaguy_raven/hooks.py`
- **Purpose**: ### Visaguy Raven \| Raven configuration for The Visa Guy \| ### Installation \| You can install this app using the [bench](https://github.com/frappe/bench) CLI: \| ```bash \| cd $PATH_TO_YOUR_BENCH
- **Fixtures (target DocTypes)**: `Raven Bot`, `Raven User`, `Raven Document Notification`
- **Scheduler events**: `daily`
- **Patches**: 2 (first: `[pre_model_sync]`, `[post_model_sync]`)
- **Cross-app imports sample**: `import frappe` at `apps/visaguy_raven/visaguy_raven/functions/send_assignment.py:...`, `from visaguy_raven.functions.send_bot_me` at `apps/visaguy_raven/visaguy_raven/functions/send_assignment.py:...`, `import frappe` at `apps/visaguy_raven/visaguy_raven/functions/send_bot_message.py:...`, `from visaguy_raven.functions.validate_ra` at `apps/visaguy_raven/visaguy_raven/functions/send_bot_message.py:...`, `import frappe` at `apps/visaguy_raven/visaguy_raven/functions/send_business.py:...`
- **Integration settings DocTypes**: `visaguy_raven_settings`
- **Hook `doc_events`**: `{"Lead": {"on_update": "visaguy_raven.functions.send_form_submission.send_lead_form_submission"}, "CRM Lead": {"on_update": "visaguy_raven.functions.send_form_submission.send_lead_form_submission"}, "PF Process File": {"on_update": "visaguy_raven.fun ...`


## RB3 — Internal app provenance classification

| App | Classification | Rationale |
|---|---|---|
| `visaguy_business` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_business.git` |
| `visaguy_hrms` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_hrms.git` |
| `visaguy_crm` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_crm.git` |
| `visaguy_helpdesk` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_helpdesk.git` |
| `the_visaguy` | original | tridz-dev/tvgglobal remote without upstream fork indicator; remote `git@tridz:tvgglobal/the_visaguy.git` |
| `waflo` | original | tridz-dev/tvgglobal remote without upstream fork indicator; remote `git@tridz:tridz-dev/waflo.git` |
| `fileflo` | original | tridz-dev/tvgglobal remote without upstream fork indicator; remote `git@tridz:tridz-dev/FileFlo.git` |
| `helpdesk` | maintained fork | remote path tridz-dev/helpdesk_frk.git; remote `git@tridz:tridz-dev/helpdesk_frk.git` |
| `crm` | maintained fork | remote path tridz-dev/frappe-crm.git; remote `git@tridz:tridz-dev/frappe-crm.git` |
| `visaguy_frappe_crm` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_frappe_crm.git` |
| `frappe_conversions_api` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/frappe_conversions_api.git` |
| `quick_kanban` | original | tridz-dev/tvgglobal remote without upstream fork indicator; remote `git@tridz:tridz-dev/quick_kanban.git` |
| `payment_integrations` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/payment_integrations.git` |
| `frappe_notifier` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/frappe_notifier.git` |
| `visaguy_website` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tvgglobal/visaguy_website.git` |
| `otp_authentication` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/otp_authentication.git` |
| `processflo` | original | tridz-dev/tvgglobal remote without upstream fork indicator; remote `git@tridz:tridz-dev/ProcessFlo.git` |
| `visaguy_raven` | integration/custom app | app-specific settings/DoTypes/fixtures wrapping external product; remote `git@tridz:tridz-dev/visaguy_raven.git` |


External apps are: `employee_self_service`, `erpnext`, `frappe`, `frappe_whatsapp`, `hrms`, `india_compliance`, `insights`, `mansico_meta_integration`, `non_profit`, `payments`, `raven`.

## RB4 — Cross-app dependencies and integrations

### Declared `required_apps`

- `india_compliance` → `frappe/erpnext`
- `non_profit` → `erpnext`
- `payment_integrations` → `erpnext`, `payments`
- `mansico_meta_integration` → `erpnext`
- `hrms` → `frappe/erpnext`

### Import/reference evidence

- `frappe` imports: `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`
- `visaguy_business` imports: `create_process_file.py`, `create_process_file.py`, `create_process_file.py`, `create_process_file.py`, `create_process_file.py`
- `erpnext` imports: `__init__.py`, `__init__.py`, `customer.py`, `customer.py`, `customer.py`
- `visaguy_hrms` imports: `get_leave_types.py`, `get_leave_types.py`, `appointment_letter_server_scripts.py`, `appointment_letter_server_scripts.py`, `appointment_letter_server_scripts.py`
- `visaguy_crm` imports: `form_generation_override.py`, `form_generation_override.py`, `allocate_lead.py`, `ff_file_collection_on_trash.py`, `ff_file_collection_restrictions.py`
- `payments` imports: `desktop.py`, `payment_webform.py`, `payment_webform.py`, `payment_webform.py`, `payment_webform.py`
- `india_compliance` imports: `accounts_settings.py`, `accounts_settings.py`, `accounts_settings.py`, `customize_form.py`, `customize_form.py`
- `visaguy_helpdesk` imports: `hd_ticket_class_override.py`, `hd_ticket_class_override.py`, `hd_ticket_class_override.py`, `hd_ticket_class_override.py`, `hd_ticket_class_override.py`
- `insights` imports: `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `alerts.py`
- `employee_self_service` imports: `__init__.py`, `__init__.py`, `__init__.py`, `desktop.py`, `custom_fields.py`
- `the_visaguy` imports: `test_whatsapp_default.py`, `whatsapp_default.py`, `whatsapp_default.py`, `whatsapp_default_templates.py`, `whatsapp_feedback_defaults.py`
- `waflo` imports: `utils.py`, `utils.py`, `test_wf_account_settings.py`, `wf_account_settings.py`, `test_wf_active_chat_flow.py`
- `fileflo` imports: `data_collection.py`, `document_fetch.py`, `download_file.py`, `download_file.py`, `download_file.py`
- `raven` imports: `__init__.py`, `agents_integration.py`, `agents_integration.py`, `ai.py`, `ai.py`
- `helpdesk` imports: `account.py`, `account.py`, `agent.py`, `article.py`, `auth.py`
- `crm` imports: `crm_call_log.py`, `crm_call_log.py`, `crm_call_log.py`, `crm_call_log.py`, `test_crm_call_log.py`
- `visaguy_frappe_crm` imports: `add_payment_date.py`, `add_payment_date.py`, `add_zone.py`, `add_zone.py`, `add_zone.py`
- `non_profit` imports: `desktop.py`, `hooks.py`, `payment_entry.py`, `payment_entry.py`, `payment_entry.py`
- `frappe_conversions_api` imports: `__init__.py`, `webhook.py`, `conversion_account.`, `test_conversion_acc`, `conversion_event.py`
- `quick_kanban` imports: `get_beta _users.py`, `kanban_board_highlight.py`
- `payment_integrations` imports: `install.py`, `integrations.py`, `integrations.py`, `integrations.py`, `totalpay.py`
- `mansico_meta_integration` imports: `map_lead_field.py`, `meta_face`, `test_meta`, `meta_forms.py`, `page_id.py`
- `frappe_notifier` imports: `get_config.py`, `send_notification.py`, `send_notification.py`, `send_notification.py`, `send_notification.py`
- `visaguy_website` imports: `create_visa_order.py`, `get_applicant_files.py`, `get_applicant_files.py`, `get_destination_items.py`, `get_file_template.py`
- `frappe_whatsapp` imports: `flow_endpoint.py`, `flow_endpoint.py`, `bulk_whatsapp_message.py`, `bulk_whatsapp_message.py`, `bulk_whatsapp_message.py`
- `otp_authentication` imports: `otp_settings.py`, `otp_settings.py`, `otp_settings.py`, `test_otp_settings.py`, `customer_test.py`
- `hrms` imports: `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`, `__init__.py`
- `processflo` imports: `generate_file_collection.py`, `generate_file_collection.py`, `pf_process_action.py`, `test_pf_process_action.py`, `pf_process_deliverables.py`
- `visaguy_raven` imports: `send_assignment.py`, `send_assignment.py`, `send_bot_message.py`, `send_bot_message.py`, `send_business.py`

### Noted overlaps (potential duplicate/customization layers)

- `crm` (maintained fork) + `visaguy_crm` (legacy custom CRM) + `visaguy_frappe_crm` (Frappe CRM wrapper/customization).
- `helpdesk` (maintained fork) + `visaguy_helpdesk`.
- `hrms` (upstream) + `visaguy_hrms`.
- `raven` (upstream) + `visaguy_raven`.
- `payments` (upstream) + `payment_integrations` (custom payment gateways).

## RB5 — Customizations to standard Frappe/ERPNext/HRMS/CRM/Helpdesk/Raven behavior

### Fixtures shipped (custom fields, roles, workflows, dashboards)

- `visaguy_business`: `Account`, `Price List`, `Customer Group`, `Custom DocPerm`, `Role`, `Role Profile`, `Client Script`, `Custom Field`, `Property Setter`
- `visaguy_hrms`: `Workflow`, `Workflow State`, `Notification`, `Appointment Letter Template`, `Interview Type`, `Email Template`, `Server Script`, `Client Script`, `Role`, `Designation`, `Insights Query`, `Insights Chart`, `Insights Dashboard`, `Print Format`, `Custom HTML Block` ...
- `visaguy_crm`: `Workflow`, `Workflow State`, `Workflow Action Master`, `Client Script`, `Insights Dashboard`, `Insights Query`, `Insights Chart`, `Role`, `Print Format`, `Custom HTML Block`, `Workspace`
- `visaguy_helpdesk`: `Role`
- `insights`: `Insights Data Source`
- `employee_self_service`: `ESS Notification`, `ESS Notification Template`
- `the_visaguy`: `Custom Field`, `Workspace`, `Custom HTML Block`, `Insights Query`, `Insights Chart`
- `visaguy_frappe_crm`: `CRM Fields Layout`, `CRM Global Settings`, `Property Setter`, `Custom DocPerm`
- `frappe_notifier`: `Role`, `Custom DocPerm`
- `visaguy_website`: `Custom Field`, `Role`
- `visaguy_raven`: `Raven Bot`, `Raven User`, `Raven Document Notification`

### DocType class / whitelisted method overrides

- `frappe`: methods: `frappe.utils.file_manager.download_file`, `frappe.core.doctype.file.file.download_file`, `frappe.core.doctype.file.file.unzip_file`, `frappe.core.doctype.file.file.get_attached_images`, `frappe.core.doctype.file.file.get_files_in_folder`, `frappe.core.doctype.file.file.get_files_by_search_text`, `frappe.core.doctype.file.file.get_max_file_size`, `frappe.core.doctype.file.file.create_new_folder`, `frappe.core.doctype.file.file.move_file`, `frappe.core.doctype.file.file.zip_files`, `frappe.www.login.login_via_google`, `frappe.www.login.login_via_github`, `frappe.www.login.login_via_facebook`, `frappe.www.login.login_via_frappe`, `frappe.www.login.login_via_office365`, `frappe.www.login.login_via_salesforce`, `frappe.www.login.login_via_fairlogin`
- `erpnext`: classes: `Address`; methods: `frappe.www.contact.send_message`
- `visaguy_hrms`: classes: `Interview`, `Expense Claim`, `Employee`; methods: `hrms.api.get_leave_types`, `frappe.core.doctype.communication.email.make`
- `visaguy_crm`: classes: `Payment Request`; methods: `fileflo.data_collection.fetch_form_data`, `fileflo.data_collection.add_form_data`, `fileflo.form_generation.generate_form`
- `payments`: classes: `Web Form`; methods: `frappe.website.doctype.web_form.web_form.accept`
- `india_compliance`: classes: `Customize Form`; methods: `erpnext.accounts.doctype.payment_entry.payment_entry.get_outstanding_reference_documents`
- `visaguy_helpdesk`: classes: `HD Ticket`
- `crm`: classes: `Contact`, `Email Template`
- `non_profit`: classes: `Payment Entry`
- `frappe_notifier`: methods: `notification_relay.api.get_config`, `notification_relay.api.token.add`, `notification_relay.api.token.delete`, `notification_relay.api.send_notification.user`, `notification_relay.api.send_notification.topic`, `notification_relay.api.topic.add`, `notification_relay.api.topic.remove`, `notification_relay.api.topic.subscribe`, `notification_relay.api.topic.unsubscribe`
- `hrms`: classes: `Employee`, `Timesheet`, `Payment Entry`, `Project`

### Frontend bundles / desk JS

- `frappe`: app_js=['libs.bundle.js', 'desk.bundle.js', 'list.bundle.js', 'form.bundle.js', 'controls.bundle.js', 'report.bundle.js', 'telemetry.bundle.js', 'billing.bundle.js'], app_css=['desk.bundle.css', 'report.bundle.css'], web_js=['website_script.js'], web_css=[]
- `visaguy_crm`: app_js=['visaguy_crm.bundle.js'], app_css=[], web_js=[], web_css=[]
- `fileflo`: app_js=['/assets/fileflo/js/form_creation.js', '/assets/fileflo/js/document_fetch.js', '/assets/fileflo/js/download_zip.js'], app_css=[], web_js=[], web_css=[]
- `hrms`: app_js=['hrms.bundle.js'], app_css=[], web_js=[], web_css=[]
- `processflo`: app_js=[], app_css=[], web_js=['/assets/processflo/js/fetch_action.js', 'assets/processflo/js/create_file_collection.js'], web_css=[]

### Scheduler / background jobs

- `frappe`: `all`, `hourly`, `hourly_maintenance`, `daily`, `daily_maintenance`, `weekly_long`, `monthly`, `monthly_long`
- `erpnext`: `hourly`, `hourly_maintenance`, `daily_maintenance`, `weekly`, `monthly_long`
- `payments`: `all`
- `insights`: `all`
- `employee_self_service`: `daily`
- `the_visaguy`: `daily`
- `raven`: `daily_maintenance`
- `helpdesk`: `all`
- `non_profit`: `daily`
- `mansico_meta_integration`: `all`, `daily`, `hourly`, `weekly`, `monthly`
- `frappe_notifier`: `daily`
- `frappe_whatsapp`: `all`, `hourly`, `hourly_long`, `daily`, `daily_long`, `weekly`, `weekly_long`, `monthly`, `monthly_long`
- `hrms`: `all`, `hourly`, `hourly_long`, `daily`, `daily_long`, `weekly`, `monthly`
- `visaguy_raven`: `daily`

### Migration / install hooks

- `frappe`: `after_install`, `before_install`, `after_migrate`, `before_migrate`
- `erpnext`: `after_install`, `before_install`
- `payments`: `after_install`, `before_install`
- `india_compliance`: `after_install`, `before_install`, `after_migrate`, `before_migrate`
- `employee_self_service`: `after_install`, `after_migrate`
- `raven`: `after_install`
- `helpdesk`: `after_install`, `before_install`, `after_migrate`
- `crm`: `after_install`, `before_install`, `after_migrate`
- `non_profit`: `after_install`
- `frappe_conversions_api`: `after_install`
- `payment_integrations`: `after_install`
- `frappe_notifier`: `after_install`
- `hrms`: `after_install`, `after_migrate`


## RB6 — Operational procedures evidenced

- **Installation**: standard `bench get-app` + `bench --site visaguy install-app <app>`; several apps include `install.py` hooks (`payment_integrations`, `crm`, `employee_self_service`, etc.).
- **Migrations**: `after_migrate`/`before_migrate` hooks in `crm`, `employee_self_service`, `payment_integrations`; `patches.txt` in many apps.
- **Build**: `Procfile` includes `watch: bench watch`; app bundles are declared via `app_include_js`/`web_include_js` in hooks.py.
- **Workers/scheduler**: `schedule: bench schedule`, `worker: bench worker` processes; scheduler_events registered in 13+ apps.
- **Backups**: Frappe `s3_backup_settings` and `dropbox_settings` DocTypes present in `frappe`; no custom backup scripts observed.
- **Deployment/update**: common_site_config keys `restart_supervisor_on_update`, `restart_systemd_on_update`, `rebase_on_pull`, `shallow_clone` indicate standard bench restart flow.
- **Validation**: test counts per app listed in RB2; no CI workflow files scanned in this phase.

## RB7 — External services and integrations (key names / settings DocTypes only)

| App | Integration / settings DocType | Evidence |
|---|---|---|
| `frappe` | `google_settings` | `apps/frappe/frappe/doctype/google_settings/google_settings.json` |
| `frappe` | `s3_backup_settings` | `apps/frappe/frappe/doctype/s3_backup_settings/s3_backup_settings.json` |
| `frappe` | `dropbox_settings` | `apps/frappe/frappe/doctype/dropbox_settings/dropbox_settings.json` |
| `frappe` | `ldap_settings` | `apps/frappe/frappe/doctype/ldap_settings/ldap_settings.json` |
| `frappe` | `push_notification_settings` | `apps/frappe/frappe/doctype/push_notification_settings/push_notification_settings.json` |
| `frappe` | `oauth_provider_settings` | `apps/frappe/frappe/doctype/oauth_provider_settings/oauth_provider_settings.json` |
| `frappe` | `sms_settings` | `apps/frappe/frappe/doctype/sms_settings/sms_settings.json` |
| `visaguy_business` | `business_client_settings` | `apps/visaguy_business/visaguybusiness/doctype/business_client_settings/business_client_settings.json` |
| `erpnext` | `plaid_settings` | `apps/erpnext/erpnext/doctype/plaid_settings/plaid_settings.json` |
| `erpnext` | `crm_settings` | `apps/erpnext/erpnext/doctype/crm_settings/crm_settings.json` |
| `erpnext` | `voice_call_settings` | `apps/erpnext/erpnext/doctype/voice_call_settings/voice_call_settings.json` |
| `erpnext` | `incoming_call_settings` | `apps/erpnext/erpnext/doctype/incoming_call_settings/incoming_call_settings.json` |
| `visaguy_hrms` | `tvg_hr_settings` | `apps/visaguy_hrms/visaguyhrms/doctype/tvg_hr_settings/tvg_hr_settings.json` |
| `visaguy_crm` | `tvg_crm_settings` | `apps/visaguy_crm/visaguycrm/doctype/tvg_crm_settings/tvg_crm_settings.json` |
| `payments` | `paypal_settings` | `apps/payments/payments/doctype/paypal_settings/paypal_settings.json` |
| `payments` | `razorpay_settings` | `apps/payments/payments/doctype/razorpay_settings/razorpay_settings.json` |
| `payments` | `paytm_settings` | `apps/payments/payments/doctype/paytm_settings/paytm_settings.json` |
| `payments` | `braintree_settings` | `apps/payments/payments/doctype/braintree_settings/braintree_settings.json` |
| `payments` | `gocardless_settings` | `apps/payments/payments/doctype/gocardless_settings/gocardless_settings.json` |
| `payments` | `stripe_settings` | `apps/payments/payments/doctype/stripe_settings/stripe_settings.json` |
| `payments` | `mpesa_settings` | `apps/payments/payments/doctype/mpesa_settings/mpesa_settings.json` |
| `india_compliance` | `gst_settings` | `apps/india_compliance/indiacompliance/doctype/gst_settings/gst_settings.json` |
| `visaguy_helpdesk` | `tvg_hd_settings` | `apps/visaguy_helpdesk/visaguyhelpdesk/doctype/tvg_hd_settings/tvg_hd_settings.json` |
| `insights` | `insights_settings` | `apps/insights/insights/doctype/insights_settings/insights_settings.json` |
| `employee_self_service` | `employee_self_service_settings` | `apps/employee_self_service/employeeselfservice/doctype/employee_self_service_settings/employee_self_service_settings.json` |
| `employee_self_service` | `ess_notification_settings` | `apps/employee_self_service/employeeselfservice/doctype/ess_notification_settings/ess_notification_settings.json` |
| `waflo` | `wf_account_settings` | `apps/waflo/waflo/doctype/wf_account_settings/wf_account_settings.json` |
| `waflo` | `wf_settings` | `apps/waflo/waflo/doctype/wf_settings/wf_settings.json` |
| `fileflo` | `fileflo_settings` | `apps/fileflo/fileflo/doctype/fileflo_settings/fileflo_settings.json` |
| `raven` | `raven_settings` | `apps/raven/raven/doctype/raven_settings/raven_settings.json` |
| `helpdesk` | `hd_settings` | `apps/helpdesk/helpdesk/doctype/hd_settings/hd_settings.json` |
| `crm` | `crm_twilio_settings` | `apps/crm/crm/doctype/crm_twilio_settings/crm_twilio_settings.json` |
| `crm` | `erpnext_crm_settings` | `apps/crm/crm/doctype/erpnext_crm_settings/erpnext_crm_settings.json` |
| `crm` | `crm_exotel_settings` | `apps/crm/crm/doctype/crm_exotel_settings/crm_exotel_settings.json` |
| `crm` | `fcrm_settings` | `apps/crm/crm/doctype/fcrm_settings/fcrm_settings.json` |
| `crm` | `crm_global_settings` | `apps/crm/crm/doctype/crm_global_settings/crm_global_settings.json` |
| `crm` | `crm_view_settings` | `apps/crm/crm/doctype/crm_view_settings/crm_view_settings.json` |
| `visaguy_frappe_crm` | `crm_migration_settings` | `apps/visaguy_frappe_crm/visaguyfrappecrm/doctype/crm_migration_settings/crm_migration_settings.json` |
| `non_profit` | `non_profit_settings` | `apps/non_profit/nonprofit/doctype/non_profit_settings/non_profit_settings.json` |
| `payment_integrations` | `myfatoorah_settings` | `apps/payment_integrations/paymentintegrations/doctype/myfatoorah_settings/myfatoorah_settings.json` |
| `payment_integrations` | `totalpay_settings` | `apps/payment_integrations/paymentintegrations/doctype/totalpay_settings/totalpay_settings.json` |
| `mansico_meta_integration` | `meta_facebook_settings` | `apps/mansico_meta_integration/mansicometaintegration/doctype/meta_facebook_settings/meta_facebook_settings.json` |
| `frappe_notifier` | `frappe_notifier_settings` | `apps/frappe_notifier/frappenotifier/doctype/frappe_notifier_settings/frappe_notifier_settings.json` |
| `frappe_whatsapp` | `whatsapp_settings` | `apps/frappe_whatsapp/frappewhatsapp/doctype/whatsapp_settings/whatsapp_settings.json` |
| `otp_authentication` | `otp_settings` | `apps/otp_authentication/otpauthentication/doctype/otp_settings/otp_settings.json` |
| `hrms` | `payroll_settings` | `apps/hrms/hrms/doctype/payroll_settings/payroll_settings.json` |
| `hrms` | `hr_settings` | `apps/hrms/hrms/doctype/hr_settings/hr_settings.json` |
| `visaguy_raven` | `visaguy_raven_settings` | `apps/visaguy_raven/visaguyraven/doctype/visaguy_raven_settings/visaguy_raven_settings.json` |

Additional service keyword hits from README/requirements/hooks:

- `payments`: `razorpay`
- `employee_self_service`: `fcm`
- `the_visaguy`: `whatsapp`, `sap`
- `waflo`: `whatsapp`, `sap`
- `crm`: `whatsapp`, `sap`
- `frappe_conversions_api`: `meta`, `google`
- `mansico_meta_integration`: `meta`, `facebook`
- `frappe_notifier`: `google`, `firebase`, `fcm`
- `frappe_whatsapp`: `whatsapp`, `sap`
- `otp_authentication`: `otp`


## RB8 — Risks, stale branches, dirty trees, gaps

### Dirty working trees

- `insights`: 1 modified/untracked file(s). Exact diffs not inspected per policy.
- `visaguy_frappe_crm`: 1 modified/untracked file(s). Exact diffs not inspected per policy.
- `mansico_meta_integration`: 1 modified/untracked file(s). Exact diffs not inspected per policy.
- `processflo`: 1 modified/untracked file(s). Exact diffs not inspected per policy.
- `visaguy_raven`: 1 modified/untracked file(s). Exact diffs not inspected per policy.

### Stale / non-standard branches

- `fileflo` on branch `fix/mandatory-file`
- `helpdesk` on branch `modification_develop_branch`
- `crm` on branch `tridz-dev`
- `otp_authentication` on branch `email`

### Low test coverage / small apps

- `visaguy_hrms`: only 2 test file(s) for 69 .py files.
- `visaguy_helpdesk`: only 1 test file(s) for 16 .py files.
- `visaguy_frappe_crm`: only 1 test file(s) for 27 .py files.
- `quick_kanban`: no test files found (11 .py files).
- `otp_authentication`: only 2 test file(s) for 24 .py files.
- `visaguy_raven`: only 1 test file(s) for 23 .py files.

### Potential overlap / duplicate logic

- Multiple CRM layers (`crm`, `visaguy_crm`, `visaguy_frappe_crm`) increase maintenance surface; verify which is active.
- Multiple helpdesk layers (`helpdesk`, `visaguy_helpdesk`).
- Multiple Raven layers (`raven`, `visaguy_raven`).
- Payment gateways split across `payments` (Frappe upstream) and `payment_integrations` (custom MyFatoorah/TotalPay).

### Unresolved questions

- All overlapping CRM, Helpdesk, HRMS, Raven, and payment layers are installed on site `visaguy`; the runtime responsibility and precedence of each layer still needs to be clarified.
- Why are `insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, and `visaguy_raven` dirty on a production bench?
- Node v12 system vs v18 socketio runtime mismatch may affect build toolchain.
- Several internal apps have no README or no test files; documentation and validation gaps.

---

*End of report.*
