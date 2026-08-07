# Risks and Open Questions

Each item uses the workspace evidence labels defined in `AGENTS.md`: **present**, **source-wired**, **configured-unverified**, or **runtime-verified**. A label describes the evidence supporting the risk or question, not whether the risk has been resolved.

## Deployment and upgrade risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 1 | Five dirty working trees on the bench (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`) block reproducible builds. | Deployment | runtime-verified |
| 46 | **Deliberate, temporary:** `visaguy_crm` on the bench is on branch `fix/whatsapp-trigger-detection` @ `1b28a82` with **uncommitted** changes to `lead_hooks.py` and `file_collection_from_lead.py`, applied 2026-08-06 for owner review. Restore with `git -C ~/bench/apps/visaguy_crm checkout -- . && git checkout main`. A sixth dirty tree until reviewed. | Deployment | runtime-verified |
| 2 | Non-standard / non-version-15 branches on `crm` (`tridz-dev`), `helpdesk` (`modification_develop_branch`), `fileflo` (`feat/visa-tracker`), `passport_extractor` (`feat/visa-tracker`), `otp_authentication` (`email`), plus external `insights`/`raven`/`frappe_whatsapp`/`non_profit`/`mansico_meta_integration`. | Upgrade | runtime-verified |
| 13 | Node v12 system runtime vs Node v18 socketio runtime split. | Infrastructure | runtime-verified |
| 24 | Three unmerged FEAT-001 `feat/visa-tracker` branches (`the_visaguy`, `fileflo`, `passport_extractor`), all pushed to upstream. `fileflo` and `passport_extractor` are checked out on the bench; `the_visaguy` is deliberately on `main` because unrelated work is in progress there, so the tracking code is intentionally inactive. Not a defect — but the bench is a mixed branch state and is not a reproducible build of any single configuration. | Deployment | runtime-verified |
| 25 | ~~Stale `the_visaguy/visa_tracking/**/__pycache__/` bytecode on the bench while the working tree is on `main`.~~ **Resolved 2026-08-06** — 23 orphaned `.pyc` files with no `.py` source removed; working tree still clean. | Deployment | runtime-verified |
| 26 | A second bench site, `visa-tracker-test.localhost`, carries a divergent app set and app versions recorded at install time that no longer match the checked-out branches. | Deployment | runtime-verified |

## Security risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 3 | Eligibility checker performs unauthenticated guest writes to `Raw Lead`/`Lead`. | Security | source-wired |
| 4 | FastAPI CORS `allow_origins=["*"]` with credentials enabled. | Security | source-wired |
| 5 | OAuth tokens and consumer API key/secret stored in browser `localStorage`. | Security | source-wired |
| 6 | Business-client admin gating relies on client-side `sessionStorage` only. | Security | source-wired |

## Functionality and quality risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 7 | Consumer `ProcessDetailsForm` Save button simulates a delay and makes no API call. | Functionality | source-wired |
| 8 | Consumer `/contact` is placeholder; `/careers` nav link has no route. | Functionality | present |
| 9 | No automated tests in any frontend; several maintained apps have minimal tests. | Quality | present |
| 10 | Business client disables ESLint and TypeScript errors during build. | Quality | source-wired |
| 11 | Mixed lockfiles in business client (`bun.lock` + `pnpm-lock.yaml`). | Build | present |
| 12 | Hard-coded fallback API URL in `visaguy_business_client/app/orders/[id]/page.tsx:32`. | Configuration | source-wired |

## Architecture and configuration questions

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 14 | Overlapping CRM layers (`crm`, `visaguy_crm`, `visaguy_frappe_crm`) — runtime precedence unclear. | Architecture | present |
| 15 | Overlapping helpdesk layers (`helpdesk`, `visaguy_helpdesk`) — runtime precedence unclear. | Architecture | present |
| 16 | Overlapping Raven layers (`raven`, `visaguy_raven`) — runtime precedence unclear. | Architecture | present |
| 17 | Active payment gateway configuration (TotalPay / MyFatoorah / upstream gateways) not verified. | Integration | configured-unverified |
| 18 | Active WhatsApp / Twilio / Exotel / OTP / FCM provider traffic not verified. | Integration | configured-unverified |
| 19 | Active Meta / Google Conversions API event forwarding not verified. | Integration | configured-unverified |
| 20 | Backup jobs (S3 / Dropbox) and retention not verified. | Operations | configured-unverified |
| 21 | GST / India Compliance active configuration not verified. | Compliance | configured-unverified |
| 22 | Consumer website order → `PF Process File` / payment join is unresolved at the frontend source level. | Workflow | source-wired |
| 23 | `visaguy_website` does not invoke `visaguy_business.create_process_file` in the frontend evidence. | Workflow | source-wired |
| 27 | FEAT-001 commit `8254f93` auto-verifies passport extractions, while the feature excludes automatic use of unverified extraction data. Promotion criteria unreviewed. | Architecture | source-wired |
| 28 | PaddleOCR model availability to production workers is unconfirmed; no live OCR run recorded. Extraction remains source-wired, not runtime-verified. | Integration | configured-unverified |
| 29 | No frontend repository is cloned on the active workstation, so all recorded frontend HEADs, versions, and risks (#3–#12) are unverified since 2026-07. | Quality | present |

## WhatsApp messaging risks

Found 2026-08-06 while assessing multi-company readiness. Planned in [FEAT-002](../features/ongoing/multi-zone-whatsapp/README.md) and [FEAT-003](../features/ongoing/waflo-correctness/README.md).

**Status as of 2026-08-06.** Risks **30, 31, 32, 36, 37 and 38 are fixed on branch `feat/waflo-correctness` @ `56899f2`** (20/20 tests pass on the `visaguy` dev site) but are **not merged and not deployed**. They remain open here until [TASK-017](../tasks/blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md) records both deployment gates — this register describes the running system, not a branch.

Risks 33, 34, 35, 39 and 40 belong to FEAT-002 and are **not** addressed by that branch.

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 30 | `waflo/flow/processor.py:61` raises `NameError` (`doc` out of scope), swallowed by a broad `except`. `create_active_flow` never runs, so new conversations get no `WF Active Chat Flow` and the initial step can be re-sent on every subsequent inbound message — a customer-visible message loop. | Functionality | source-wired |
| 31 | The waflo rate limiter never increments on flow paths and is therefore inert whenever the flow engine is enabled. Outbound event messages are not rate limited at all. | Functionality | source-wired |
| 32 | Rate limit check-then-act is non-atomic (`cache.get_value` then `set_value`), so concurrent workers can exceed the limit under exactly the burst conditions it targets. | Functionality | source-wired |
| 33 | `waflo/messaging/send.py:29` always resolves the global default outgoing WhatsApp account; `send_whatsapp_template` has no account parameter. All companies would send from one number. | Architecture | runtime-verified |
| 34 | WhatsApp configuration is looked up by passing `custom_zone` (Link → Zone) into `Whatsapp Default.company` (Link → Company). It resolves only because Zone and Company names currently coincide, and breaks on any zone rename. The callers are correct; the field is wrong. Resolved in design by [ADR-007](../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md) — rekey to Zone. | Architecture | runtime-verified |
| 39 | Code that scopes data must choose Zone or Company deliberately ([ADR-006](../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md)). Three of four names coincide, so keying the wrong axis appears to work until a back-office record (`custom_zone = TVG`, `custom_company = TVG  India`) passes through it. | Architecture | runtime-verified |
| 40 | Company `TVG  India` contains a double space. Harmless once lookups key on Zone, but it will break any name-based matching or trimmed comparison. | Configuration | runtime-verified |
| 35 | Six `[x for x in event_template if ...][0]` call sites raise `IndexError` for any company that has not configured every event type. | Functionality | source-wired |
| 36 | `WF Settings.limit_after` is declared under the Rate Limiting tab but read by no code — a configuration surface that does nothing. | Configuration | source-wired |
| 37 | `send.py:112` references `frappe.flags.integration_request` in an except block; when a send fails before the request is issued this raises `AttributeError` and masks the original error. | Quality | source-wired |
| 38 | Rate limiting is scoped per `(account, mobile_no)` with no account-level ceiling, leaving fan-out unbounded against Meta tier limits. | Integration | source-wired |
| 41 | A rate-limited transactional message is deferred to the **hourly** `schedule_retry_message`, so it can arrive up to an hour late. Never dropped, per the owner's decision, but the dev site is configured at 3 sends per 30s and `the_visaguy._send_payment_received` alone sends two messages back to back. `max_replies_per_window` needs a deliberate value before deployment. | Functionality | source-wired |
| 42 | No deferred-then-retried WhatsApp message has ever been delivered end to end on a real site. The most serious defect found while implementing FEAT-003 — silent message loss — lived in exactly that seam and was caught by code reading, not by a test. All FEAT-003 tests mock Redis, the queue, and the Meta API. | Quality | source-wired |
| 43 | FEAT-002 multi-zone routing is proven only by unit tests. With one `WhatsApp Account` configured, every runtime path still resolves to `Visaguy UAE`; routing is exercised by mocks, not two real accounts. First genuine test is TASK-020. | Quality | source-wired |
| 44 | `the_visaguy` tests require `bench run-tests --skip-test-records` on this bench: a pre-existing `visaguy_crm`/`visaguy_hrms` custom field makes `custom_display_name` mandatory on Company, breaking Frappe's stock test-record bootstrap for every app. Worked around, not fixed. | Quality | runtime-verified |
| 45 | `bench migrate` emits `Skipping fixture syncing from custom_field.json. Reason: No module named 'helpdesk.helpdesk.doctype.hd_settings.helpers'` — a pre-existing `helpdesk` fork issue unrelated to current work. | Deployment | runtime-verified |

## Notes

- Do not mark a `present`, `source-wired`, or `configured-unverified` question as settled without the follow-up evidence required to answer it.
- Dirty-tree diffs were intentionally not inspected; reconciliation is a prerequisite to any upgrade.
