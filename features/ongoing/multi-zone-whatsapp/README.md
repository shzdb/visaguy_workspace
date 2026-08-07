---
id: FEAT-002
title: Multi-zone configurable WhatsApp auto messages and feedback
status: ongoing
priority: high
repositories:
  - the_visaguy
  - waflo
owners: []
depends_on:
  - FEAT-003
  - ADR-006
  - ADR-007
created: 2026-08-06
updated: 2026-08-06
---

# Multi-zone configurable WhatsApp auto messages and feedback

## Current status

**Implemented and verified on the dev site. Not merged, not deployed, and multi-zone behaviour not yet proven with real accounts.**

| Task | State |
|---|---|
| [TASK-018](../../../tasks/ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md) — Qatar WABA, number, templates | **ready — critical path, start now** |
| [TASK-019](../../../tasks/completed/multi-zone-whatsapp/TASK-019-implement-zone-routing.md) — zone routing and config model | completed |
| [TASK-020](../../../tasks/blocked/multi-zone-whatsapp/TASK-020-configure-tvg-qatar.md) — configure Qatar and prove routing | blocked |

Branches: `waflo` `feat/multi-zone-whatsapp` @ `f81fe81`, `the_visaguy` @ `aa3ef89`. Both pushed.

Verified on `visaguy`: `waflo` **28/28**, `the_visaguy` **13/13**, and `bench migrate` confirmed the Company→Zone backfill against real data.

**What is not proven:** with only one `WhatsApp Account` configured, every runtime path still resolves to `Visaguy UAE`. Routing is exercised by mocks. TASK-020 is the first genuine multi-zone test.


> **Terminology.** This feature is scoped by **Zone**, not Company. Per [ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md), Zone is the customer-facing market and Company is the employing legal entity, and the two are independent. A customer must always hear from the WhatsApp number of the zone serving them, whichever office does the work. See [ADR-007](../../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md).

## Summary

Make event-driven WhatsApp auto messages and feedback messages work for more than one company, configurable per company, and extensible to many companies without code changes.

The starting position is better than it looks. `Whatsapp Default` is **already** a per-company DocType (`autoname: field:company`) and the handlers in `the_visaguy` already resolve configuration per record rather than from a constant. The hardcoded `COMPANY = "TVG"` in `the_visaguy/handlers/whatsapp_message.py` is only referenced by a **commented-out** function and is dead.

What actually blocks a second company is narrower and sharper:

1. **Every outgoing message is sent from one global WhatsApp account.** `waflo/waflo/messaging/send.py:29` calls `get_whatsapp_account(account_type="outgoing")`, which resolves the account flagged `is_default_outgoing`. `send_whatsapp_template()` has no account parameter. Company B cannot send from its own number.
2. **Configuration lookup has a field-type mismatch that works only by naming coincidence.** Handlers pass `doc.custom_zone` (a Link to **Zone**) into `frappe.get_doc("Whatsapp Default", {"company": ...})`, where `company` is a Link to **Company**. The callers are right and the field is wrong — the fix is to retype the field to Zone, per ADR-007.
3. **Unconfigured events raise `IndexError`.** Six call sites use `[x for x in whatsapp_default.event_template if x.event_type == "..."][0]`. A company that has not configured every event type crashes the handler.

## Evidence

Verified against the remote bench on 2026-08-06. `the_visaguy` on `main` @ `e690b5b`, `waflo` on `develop` @ `2167958`, `frappe_whatsapp` on `master` @ `27f3438`.

### Template records are per-account, and their names collide

Found 2026-08-06 while scoping the TVG Qatar rollout. **Not previously in this plan.**

`WhatsApp Templates` carries a `whatsapp_account` Link and is autonamed `format:{template_name}-{language_code}`. All seven existing records are bound to `Visaguy UAE`:

`default_reply-en`, `hello_world-en_US`, `lead_form-en`, `payment_success-en`, `process_form-en`, `payment_completion_feedback-en`, `visa_completion_feedback-en` — all `APPROVED`.

Meta approves templates **per WABA**, so each zone needs its own template records. But a second zone cannot create `lead_form-en` — the name is taken.

**Resolution, without modifying `frappe_whatsapp`:** `template_name` is the Frappe-side identity and `actual_name` is the name sent to Meta (`send.py` looks up `actual_name` and puts that in the payload). So a zone suffix on `template_name` with an unchanged `actual_name` resolves the collision:

| Zone | `template_name` | `actual_name` (Meta) | `whatsapp_account` |
|---|---|---|---|
| TVG | `lead_form` | `lead_form` | `Visaguy UAE` |
| TVG Qatar | `lead_form_qatar` | `lead_form` | `Visaguy Qatar` |

This must be a documented naming convention, applied consistently. `Whatsapp Default.event_template` links to the record, so each zone's rows point at its own templates and nothing else changes.

Rejected alternative: changing the `WhatsApp Templates` autoname to include the account. That means modifying an app we do not maintain — see [ADR-009](../../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md).

### Current data state

| Entity | Records |
|---|---|
| `WhatsApp Account` | **1** — `Visaguy UAE` (`is_default_outgoing = 1`, `is_default_incoming = 1`) |
| `Whatsapp Default` | **1** — `TVG` (company `TVG`, enabled) |
| `Company` | 4 — `TVG`, `TVG Qatar`, `TVG Saudi`, `TVG  India` |
| `Zone` | 3 — `TVG`, `TVG Qatar`, `TVG Saudi` |

Two things follow directly.

**The Zone/Company coincidence.** Zone names currently happen to match Company names for `TVG`, `TVG Qatar`, and `TVG Saudi`, which is why the mismatched lookup has not yet failed. It is one rename away from breaking.

The four-companies-to-three-zones asymmetry is **not** a data gap. `TVG  India` is a back-office branch whose employees handle UAE and Qatar leads; it has no customers of its own and therefore needs no zone and no WhatsApp configuration (ADR-006). Its double-space name is a data-quality wart worth cleaning, but it is not a blocker for this feature once the lookup keys on Zone.

**`frappe_whatsapp` is not the constraint.** It already ships a `WhatsApp Account` DocType, a `migrate_to_multi_account` patch, and `get_whatsapp_account(phone_id=..., account_type=...)`. Multi-account support exists and is simply unused — one account is configured and everything routes through it.

## User value

- A second company can send its own auto and feedback messages from its own WhatsApp number.
- Adding company three onward is configuration, not a code change or a release.
- Per-company branding: introduction image, helpline number, templates, and feedback header images are already modelled per company; they become genuinely usable.
- A company that has not finished configuring an event degrades gracefully instead of throwing.

## Scope

### Included

1. Explicit WhatsApp account routing through the send path (`waflo`).
2. A per-company account binding on `Whatsapp Default` (`the_visaguy`).
3. Resolution of the Zone vs Company keying mismatch — see ADR-006.
4. Safe lookup for unconfigured event types and missing company configuration.
5. Auto messages: Lead Form, Process Form, Payment Success, Visa Completion.
6. Feedback messages: Payment Feedback, Completion Feedback.
7. Extensible event types so a new event does not require a schema change.
8. Configuration validation surfacing an incomplete company setup before it fails at send time.
9. Removal of dead and hardcoded values.
10. Per-company onboarding runbook and a second-company configuration.

### Excluded from the first release

- Per-company message *content* authoring UI. Templates remain `WhatsApp Templates` records.
- Per-company language selection beyond a single configurable code per account. Full localisation is a follow-up.
- Migrating existing `Whatsapp Default` history or rewriting sent-message logs.
- Inbound routing changes. Multi-account **inbound** already resolves by `phone_id`; only outbound is broken.
- Rate limiting policy per company — depends on FEAT-003 landing first.

## Required modifications

### `waflo` — send path

| # | Change | Location |
|---|---|---|
| M1 | Add an explicit `whatsapp_account` parameter to `send_whatsapp_template()` and `_send_whatsapp_template()`. Fall back to the default outgoing account only when it is not supplied. | `waflo/waflo/messaging/send.py:7,28,29` |
| M2 | Propagate `whatsapp_account` through the `queue=True` enqueue branch, which currently drops any new kwarg silently. | `send.py:10-23` |
| M3 | Make the template language code configurable per account instead of the hardcoded `"en"`. | `send.py:80` |
| M4 | Pass the resolved account through to `log_whatsapp_message` so logs attribute messages to the right number. Already parameterised; just needs the correct value. | `send.py:103` |

D8–D11 in [FEAT-003](../../ongoing/waflo-correctness/README.md) touch the same file. Sequence the two features to avoid conflicting edits — FEAT-003 first.

### `the_visaguy` — configuration model

| # | Change | Location |
|---|---|---|
| M5 | Add a `whatsapp_account` Link field (→ `WhatsApp Account`) to `Whatsapp Default`, so each zone binds to its sending number. | `communications/doctype/whatsapp_default/whatsapp_default.json` |
| M6 | Rekey `Whatsapp Default` from `company` (Link → Company) to `zone` (Link → Zone) per ADR-007, including `autoname`, the migration, and the five lookup sites. | `whatsapp_default.json`, `handlers/whatsapp_message.py`, `whatsapp_default.py` |
| M6b | Rename the `is_enabled(company, customer)` parameter to `zone`. Every caller already passes a zone; only the name is wrong. | `whatsapp_default.py:13-21` |
| M7 | Replace the hardcoded `event_type` Select with a `Whatsapp Event Type` DocType so new events are configuration. Migrate the six existing values. | `whatsapp_default_templates.json` |
| M8 | Align `Whatsapp Feedback Defaults.feedback_type` with the same extensible list. | `whatsapp_feedback_defaults.json` |
| M9 | Add a `validate` on `Whatsapp Default` that flags missing required event templates, and a missing bound `WhatsApp Account`, when `enabled = 1` — so misconfiguration surfaces at save time rather than at send time. | `whatsapp_default.py` |

### `the_visaguy` — handler robustness

| # | Change | Location |
|---|---|---|
| M10 | Replace all six `[x for x in ... if x.event_type == "..."][0]` with a safe helper returning `None`, then skip and log. | `handlers/whatsapp_message.py` — `_send_lead_form_link`, `_send_process_form_link`, `_send_payment_received` (×2), `_send_process_file_documents_delivered` (×2) |
| M11 | Guard `frappe.get_doc("Whatsapp Default", {"company": ...})`, which raises `DoesNotExistError` for an unconfigured company. 4 sites. | `handlers/whatsapp_message.py` |
| M12 | Replace `frappe.get_doc("Sales Invoice", {...})` with an existence check. `get_doc` raises rather than returning `None`, so the following `if not sales_invoice` guard is unreachable dead code. | `_send_payment_received` |
| M13 | Remove the dead `COMPANY = "TVG"` constant and the commented-out `send_default_message` block. | `handlers/whatsapp_message.py:16,22-46` |
| M14 | Replace the hardcoded `TEMP_HOST_NAME = "https://visaguy.erpcode.tridz.in"` with configuration. | `handlers/whatsapp_message.py:14` |
| M15 | Remove `frappe.log_error("Sales invoice for sending in whatsapp message", sales_invoice)` and the `file_url` log — these fire on every payment and pass a whole Document as the log body. | `_send_payment_received` |
| M16 | Strengthen `clean_mobile_no`, which currently only strips `+`. Multi-country operation needs real normalisation and validation. | `whatsapp_default.py:9` |

### Configuration and data

| # | Change |
|---|---|
| M17 | Create one `WhatsApp Account` record per zone and bind it in `Whatsapp Default`. |
| M18 | Create `Whatsapp Default` rows for each additional zone with templates and feedback images. `TVG India` needs none. |
| M19 | Clean up the `TVG  India` double-space company name as data hygiene. No longer blocking once the lookup keys on Zone. |

## Proposed task order

| # | Task | Repository | Depends on |
|---|---|---|---|
| 0 | [TASK-018](../../../tasks/ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md) — TVG Qatar WABA, number, template approval | external (Meta) | none — **ready now, critical path** |
| 1 | Preflight: branch setup, confirm line references | both | FEAT-003 deployed |
| 2 | Account routing through the send path — M1–M4 | `waflo` | 1 |
| 3 | Rekey `Whatsapp Default` to Zone, with migration — M6, M6b | `the_visaguy` | 1 |
| 4 | Config model: account binding, event types, validation — M5, M7, M8, M9 | `the_visaguy` | 3 |
| 5 | Handler robustness and cleanup — M10–M16 | `the_visaguy` | 4 |
| 6 | Second-zone configuration and onboarding runbook — M17–M19 | config | 2, 4, 5 |
| 7 | Verification: two zones, all six events, back-office isolation test | both | 6 |

## Acceptance criteria

- A message triggered for zone A is sent from zone A's WhatsApp account; the same event for zone B is sent from B's. Verified in `WhatsApp Message` records, not just in code.
- **Back-office isolation test:** a lead with `custom_zone = TVG` and `custom_company = TVG India` — created by an Indian employee for a UAE customer — sends from the **TVG UAE** number, not an India number. This is the single most important assertion in this feature.
- Adding a third zone requires no code change and no deployment.
- A zone with an unconfigured event type logs and skips; it does not raise, and it does not affect other zones' messages.
- A zone with no `Whatsapp Default` record at all is skipped cleanly and observably.
- Enabling a zone with incomplete configuration is rejected at save time with a message naming what is missing.
- All four auto message types and both feedback types work for at least two zones.
- `Whatsapp Default` is keyed on Zone; no lookup depends on a Zone name coinciding with a Company name.
- No hardcoded company, hostname, or account remains in `the_visaguy/handlers/whatsapp_message.py`.
- Existing TVG behaviour is unchanged — verified by comparing sent messages before and after.

## Risks

- **Silent regression for TVG.** Every change here sits on the live messaging path for the existing company. The safest sequencing is: make routing explicit but default to current behaviour, verify no change for TVG, only then introduce company B.
- **The Zone/Company coincidence is load-bearing.** Any fix must migrate existing data, not just change the lookup, or TVG's configuration stops resolving.
- **`frappe.get_cached_doc` on settings** means configuration changes may not take effect until the cache clears. Worth confirming during verification.
- Template approval by Meta is per WhatsApp Business Account. A second company's templates need separate approval, which has lead time outside the team's control.
- Company B's number will have its own quality rating and tier limits — interacts directly with FEAT-003 D7.
- `the_visaguy` is currently on `main` with unrelated work in progress; this feature needs its own branch off a known point.

## Open questions

1. ~~Zone vs Company as the configuration key.~~ **Resolved** by [ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) and [ADR-007](../../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md): keyed on Zone.
2. Should a zone inherit defaults from a parent configuration, or must every zone configure every event explicitly? Recommendation: explicit, with the M9 validation making gaps obvious. Inheritance across markets with different numbers invites accidental cross-market sends.
3. What should happen when a lead's zone has WhatsApp disabled or no configuration? Silent skip is the current behaviour and is probably right, but it should be deliberate and logged.

**Settled, not open:** one WhatsApp account per zone. Multiple numbers per zone are out of scope and are not to be designed for — the revisit condition is recorded in ADR-007.

## Findings from implementation recon (2026-08-06)

Reconnaissance against the code corrected two counts and found four issues this plan had missed. Three of them break Qatar.

### Corrected counts

| This plan said | Code says |
|---|---|
| 5 `Whatsapp Default` lookup sites (M6) | **4** live `get_doc` — a 5th is inside dead commented code |
| 6 `[...][0]` index sites (M10) | **7** — 5 over `event_template`, 2 over `feedback_defaults` |
| `send.py` line references in M1–M4 | Pre-FEAT-003; that file has since been restructured |

### F1 — `receive_feedback.py` hardcodes `COMPANY = "TVG"` (in scope)

It resolves `Whatsapp Feedback Defaults` with `parent = COMPANY`. A Qatar customer replying to a feedback message would be matched against **TVG's** feedback configuration.

This plan covered only the outbound half of feedback. F1 is the inbound half, and without it Qatar feedback collection silently uses the wrong zone's config.

### F2 — `retry_message` drops `whatsapp_account` (in scope)

The `WhatsApp Message` record stores `whatsapp_account`, but `retry_message` never reads it, so the send re-resolves the default outgoing account.

Once a second account exists, a Qatar message deferred by FEAT-003's rate limiter is **retried from the UAE number** — where Qatar's template does not exist, so Meta rejects it. A direct interaction between FEAT-003's deferral and multi-account.

### F3 — inbound replies leave from the wrong account (in scope)

`processor.py` reads `doc.whatsapp_account` for rate-limit accounting and `WF Account Settings`, but its sends do not pass it.

**This path is live.** With the flow engine off, `send_default_message` handles inbound messages — so a Qatar customer messaging the Qatar number would receive their default reply **from the UAE number**. Unlike the dormant flow-engine defects, this breaks the moment a second account exists.

### F4 — `Visa Completion` — **resolved, not a gap**

Recon found that `Visa Completion` is an `event_type` option with no handler, and flagged it as a possible gap in the acceptance criteria.

**Owner confirmed it is not required.** The visa completion message goes out **together with the completion feedback message**, so there is no separate send to implement. The Select option stays; nothing demands it.

This settles what "fully configured" means for a zone.

### Required configuration per zone

Derived from the wired handlers and confirmed by the owner. M9 validation enforces exactly this when a zone is enabled — no more, no less.

| `event_template.event_type` | Required |
|---|---|
| Lead Form | yes |
| Process Form | yes |
| Payment Success | yes |
| Payment Feedback | yes |
| Completion Feedback | yes |
| Visa Completion | **no** — covered by Completion Feedback |

| `feedback_defaults.feedback_type` | Required |
|---|---|
| Payment Feedback | yes |
| Completion Feedback | yes |

Plus a bound `whatsapp_account`. A zone cannot be enabled with any of these missing, and the validation error names what is absent.

### Test reality

`the_visaguy` has six test files, **all empty `FrappeTestCase` stubs**. Nothing exercises the WhatsApp handlers or the send path. Coverage for the config model and the Company→Zone migration is being written from zero, with no pre-existing regression net. `waflo` does have real tests (20 passing from FEAT-003).

## Deployment coupling with FEAT-003

Implementation started 2026-08-06. The `waflo` work is branched off **`feat/waflo-correctness`**, not off `develop`, because M1–M4 restructure the same `send_whatsapp_template` that FEAT-003 rewrote. Branching off `develop` would guarantee conflicts in `send.py`.

### The coupling is one-way

`feat/multi-zone-whatsapp` contains **all six FEAT-003 commits**, so:

- Merging `feat/multi-zone-whatsapp` into `develop` ships **both features**. FEAT-003 does **not** need a separate merge.
- FEAT-002 **cannot** ship without FEAT-003.
- But `feat/waflo-correctness` @ `56899f2` remains on the remote as a clean fast-forward from `develop` with no FEAT-002 code, so **FEAT-003 can still ship alone** if you want to stage the risk.

One merge is simpler; two merges isolate which feature caused a regression. Either way, [TASK-017](../../../tasks/blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md)'s three prerequisites gate this feature, because its changes ship regardless:

1. No end-to-end retry test has run.
2. `bench migrate` has not exercised the `limit_after` removal patch.
3. `max_replies_per_window` needs a deliberate value.

`the_visaguy` is branched off `main` and stays independent — its unmerged `feat/visa-tracker` adds a separate `visa_tracking/` module and does not touch `handlers/whatsapp_message.py`.

## Scope decisions for the first implementation run

| Decision | Choice |
|---|---|
| M7/M8 — extensible `Whatsapp Event Type` DocType | **Deferred.** Qatar uses the same six event types; only the templates differ per zone. Dropping it removes a schema migration from this run. |
| Missing or disabled zone configuration | **Skip, but log a warning.** Not silent — a misconfigured zone must not look identical to a working one. Never fall back to the default account: a Qatar customer must never receive a UAE-numbered message. |
| Template inheritance between zones | **None.** Every zone configures all six explicitly; M9 validation rejects enabling a zone with gaps. |

## Dependencies

- [FEAT-003](../../ongoing/waflo-correctness/README.md) — the rate limiter must actually count before traffic is fanned out to more numbers.
- [ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) — Zone and Company are independent axes.
- [ADR-007](../../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md) — WhatsApp configuration is keyed on Zone.
- `frappe_whatsapp` multi-account support — already present, unused.
- Meta Business Account and approved templates for each additional company.

## Completion notes

Not implemented. Planning only.
