---
id: FEAT-002
title: Multi-zone configurable WhatsApp auto messages and feedback
status: planned
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
| 1 | Preflight: branch setup, confirm line references | both | FEAT-003 task 1 |
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

## Dependencies

- [FEAT-003](../../ongoing/waflo-correctness/README.md) — the rate limiter must actually count before traffic is fanned out to more numbers.
- [ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md) — Zone and Company are independent axes.
- [ADR-007](../../../decisions/ADR-007-whatsapp-configuration-keyed-on-zone.md) — WhatsApp configuration is keyed on Zone.
- `frappe_whatsapp` multi-account support — already present, unused.
- Meta Business Account and approved templates for each additional company.

## Completion notes

Not implemented. Planning only.
