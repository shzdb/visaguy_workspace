# Risks and Open Questions

Each item uses the workspace evidence labels defined in `AGENTS.md`: **present**, **source-wired**, **configured-unverified**, or **runtime-verified**. A label describes the evidence supporting the risk or question, not whether the risk has been resolved.

## Deployment and upgrade risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 1 | Five dirty working trees on the bench (`insights`, `mansico_meta_integration`, `processflo`, `visaguy_frappe_crm`, `visaguy_raven`) block reproducible builds. | Deployment | runtime-verified |
| 2 | Non-standard / non-version-15 branches on `crm` (`tridz-dev`), `helpdesk` (`modification_develop_branch`), `fileflo` (`fix/mandatory-file`), `otp_authentication` (`email`), plus external `insights`/`raven`/`frappe_whatsapp`/`non_profit`/`mansico_meta_integration`. | Upgrade | runtime-verified |
| 13 | Node v12 system runtime vs Node v18 socketio runtime split. | Infrastructure | runtime-verified |

## Security risks

| # | Risk / open question | Category | Label |
|---|---|---|---|
| 3 | Eligibility checker performs unauthenticated guest writes to `Raw Lead`/`Lead`. | Security | source-wired |
| 4 | FastAPI CORS `allow_origins=["*"]` with credentials enabled. | Security | source-wired |
| 5 | OAuth tokens and consumer API key/secret stored in browser `localStorage`. | Security | source-wired |
| 6 | Business-client admin gating relies on client-side `sessionStorage` only. | Security | source-wired |
| 18 | **STILL LIVE as deployed: FEAT-001 rate limiting on site `visaguy` does not constrain credential enumeration.** `verification.py:102` sets `target_bucket = candidates[0][0]`, scoping the failure counter per exact passport+DOB pair. Originally proven over real HTTP: 7x an identical wrong pair locks out at attempt 6 (`Retry-After: 900`); 7x the same passport with an incrementing DOB **never** locks out (0/7). An attacker knowing a passport number can enumerate DOBs (~36,500 for an adult) from one IP. Every failure returns a byte-identical HTTP 200, so there is no client-visible signal. **A fix now exists (ADR-009, TASK-012): a complementary per-IP counter (20 failures/hour, 60-minute lockout) alongside the unchanged per-identity counter (5/15), keeping the per-identity bucket specifically so an attacker cannot lock a legitimate applicant out of their own record.** The fix is implemented and **runtime-verified on `visa-tracker-test.localhost` only** — 2026-09-01 live-HTTP proof: the same passport with an incrementing DOB now locks at attempt 21 (`Retry-After: 3597`, was 0/7); the existing per-identity lockout is unchanged (attempt 6, `Retry-After: 900`); response body md5 is identical across all reachable failure modes. **This risk does not close on that evidence alone.** The fix is uncommitted in `the_visaguy` and site `visaguy` still runs the pre-fix code with public tracking enabled, so the enumeration gap is live in reality right now. Close this risk only after TASK-012 is committed and deployed to `visaguy`, per its own "Completion evidence" section. | Security | runtime-verified |
| 19 | Automatic passport verification (ADR-007) makes an OCR result a public authentication credential with no human review. ICAO check digits catch most misreads but not a consistent self-validating substitution, and attest nothing about document authenticity. Recommendation: keep `require_manual_verification` set in any real production environment. | Security | runtime-verified |
| 20 | The tracker's CORS header is now `*`-derived at transport level (ADR-008); origin enforcement lives only in the API request path. Additionally the application depends on site-level `allow_cors` it does not own — removing that key breaks every browser client, invisibly from application code. | Security | runtime-verified |
| 24 | **A genuinely non-JSON request body to the public `verify_identity` endpoint returns a raw traceback page on an unauthenticated endpoint.** Frappe's own `make_form_dict` parses the request body **before** the app's handler runs, and raises there for malformed (non-JSON) input — outside the app's `UnsafeRequestError` path entirely, so the app's own generic-failure/constant-response handling never gets a chance to apply. This is a pre-existing Frappe-core behaviour, not a defect introduced by `verification.py`. By contrast a valid-JSON-but-wrong-shape body (e.g. `[]`) is caught correctly by the app's `UnsafeRequestError` path and returns the byte-identical generic body. Consequence: information disclosure (a stack trace on a public endpoint) and it defeats the constant-response property this feature otherwise maintains, in this one reachable case. Found 2026-09-01 during TASK-012 live-HTTP testing; not caused by that task's changes. See TASK-014. | Security | runtime-verified |

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
| 21 | **`visaguy_crm.data_collecting_form.add_form_data` is a diverged fork of `fileflo.data_collection.add_form_data`.** The live form calls the CRM copy; the fileflo original is bypassed. Both now carry the `field_id` fix independently and will drift again. Any change to one must be evaluated against the other. See ADR-006. | Architecture | runtime-verified |
| 22 | The lookup HMAC key (`visa_tracker_lookup_hmac_key`) is unrecoverable once set: only `lifecycle_service.py:243` writes `verification_lookup_hash`, and only at creation. There is no recompute seam, so rotating the key silently invalidates every existing application's public lookup. | Configuration | runtime-verified |
| 17 | Active payment gateway configuration (TotalPay / MyFatoorah / upstream gateways) not verified. | Integration | configured-unverified |
| 18 | Active WhatsApp / Twilio / Exotel / OTP / FCM provider traffic not verified. | Integration | configured-unverified |
| 19 | Active Meta / Google Conversions API event forwarding not verified. | Integration | configured-unverified |
| 20 | Backup jobs (S3 / Dropbox) and retention not verified. | Operations | configured-unverified |
| 21 | GST / India Compliance active configuration not verified. | Compliance | configured-unverified |
| 22 | Consumer website order → `PF Process File` / payment join is unresolved at the frontend source level. | Workflow | source-wired |
| 23 | `visaguy_website` does not invoke `visaguy_business.create_process_file` in the frontend evidence. | Workflow | source-wired |

## Notes

- Do not mark a `present`, `source-wired`, or `configured-unverified` question as settled without the follow-up evidence required to answer it.
- Dirty-tree diffs were intentionally not inspected; reconciliation is a prerequisite to any upgrade.
