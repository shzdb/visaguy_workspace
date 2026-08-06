---
id: FEAT-002
title: Multi-company configurable WhatsApp auto messages and feedback
status: planned
priority: high
repositories:
  - the_visaguy
  - waflo
owners: []
depends_on:
  - FEAT-003
  - ADR-006
created: 2026-08-06
updated: 2026-08-06
---

# Multi-company configurable WhatsApp auto messages and feedback

## Summary

Make event-driven WhatsApp auto messages and feedback messages work for more than one company, configurable per company, and extensible to many companies without code changes.

The starting position is better than it looks. `Whatsapp Default` is **already** a per-company DocType (`autoname: field:company`) and the handlers in `the_visaguy` already resolve configuration per record rather than from a constant. The hardcoded `COMPANY = "TVG"` in `the_visaguy/handlers/whatsapp_message.py` is only referenced by a **commented-out** function and is dead.

What actually blocks a second company is narrower and sharper:

1. **Every outgoing message is sent from one global WhatsApp account.** `waflo/waflo/messaging/send.py:29` calls `get_whatsapp_account(account_type="outgoing")`, which resolves the account flagged `is_default_outgoing`. `send_whatsapp_template()` has no account parameter. Company B cannot send from its own number.
2. **Configuration lookup is keyed on a field-type mismatch that works only by naming coincidence.** Handlers pass `doc.custom_zone` (a Link to **Zone**) into `frappe.get_doc("Whatsapp Default", {"company": ...})`, where `company` is a Link to **Company**.
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

**The Zone/Company coincidence.** Zone names currently happen to match Company names for `TVG`, `TVG Qatar`, and `TVG Saudi`, which is why the mismatched lookup has not yet failed. It is one rename away from breaking. Note also that the company `TVG  India` contains a **double space** and has no matching Zone — any name-based matching involving it will fail.

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

D8–D11 in [FEAT-003](../waflo-correctness/README.md) touch the same file. Sequence the two features to avoid conflicting edits — FEAT-003 first.

### `the_visaguy` — configuration model

| # | Change | Location |
|---|---|---|
| M5 | Add a `whatsapp_account` Link field (→ `WhatsApp Account`) to `Whatsapp Default`, so each company binds to its sending number. | `communications/doctype/whatsapp_default/whatsapp_default.json` |
| M6 | Resolve the Zone/Company keying mismatch per ADR-006. | `handlers/whatsapp_message.py` (5 lookup sites), `whatsapp_default.py:is_enabled` |
| M7 | Replace the hardcoded `event_type` Select with a `Whatsapp Event Type` DocType so new events are configuration. Migrate the six existing values. | `whatsapp_default_templates.json` |
| M8 | Align `Whatsapp Feedback Defaults.feedback_type` with the same extensible list. | `whatsapp_feedback_defaults.json` |
| M9 | Add a `validate` on `Whatsapp Default` that flags missing required event templates when `enabled = 1`, so misconfiguration surfaces at save time rather than at send time. | `whatsapp_default.py` |

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
| M17 | Create a `WhatsApp Account` record per company and bind it in `Whatsapp Default`. |
| M18 | Create `Whatsapp Default` rows for each additional company with templates and feedback images. |
| M19 | Decide the disposition of the `TVG  India` double-space company name — rename or map explicitly. It will break any name-based matching. |

## Proposed task order

| # | Task | Repository | Depends on |
|---|---|---|---|
| 1 | Preflight: branch setup, confirm line references, decide ADR-006 | both | FEAT-003 task 1 |
| 2 | Account routing through the send path — M1–M4 | `waflo` | 1 |
| 3 | Config model: account binding, event types, validation — M5, M7, M8, M9 | `the_visaguy` | 1 |
| 4 | Zone/Company resolution — M6 | `the_visaguy` | ADR-006 |
| 5 | Handler robustness and cleanup — M10–M16 | `the_visaguy` | 3 |
| 6 | Second-company configuration and onboarding runbook — M17–M19 | config | 2, 3, 4, 5 |
| 7 | Verification: both companies, all six events, isolation tests | both | 6 |

## Acceptance criteria

- A message triggered for company A is sent from company A's WhatsApp account; the same event for company B is sent from B's. Verified in `WhatsApp Message` records, not just in code.
- Adding a third company requires no code change and no deployment.
- A company with an unconfigured event type logs and skips; it does not raise, and it does not affect other companies' messages.
- A company with no `Whatsapp Default` record at all is skipped cleanly.
- Enabling a company with incomplete configuration is rejected at save time with a message naming the missing events.
- All four auto message types and both feedback types work for at least two companies.
- Configuration lookup no longer depends on a Zone name coinciding with a Company name.
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

1. **Zone vs Company as the configuration key** — resolved by ADR-006, which must be accepted before task 4.
2. Should a company inherit defaults from a parent configuration, or must every company configure every event explicitly? Recommendation: explicit, with the M9 validation making gaps obvious. Inheritance across companies with different legal entities and numbers invites accidental cross-company sends.
3. Is one WhatsApp account per company correct, or does a company need several — for example one per zone or per destination? The current model assumes one.
4. What is the intended behaviour when a lead's zone maps to a company that has WhatsApp disabled? Silent skip is the current behaviour and is probably right, but it should be deliberate.

## Dependencies

- [FEAT-003](../waflo-correctness/README.md) — the rate limiter must actually count before traffic is fanned out to more numbers.
- [ADR-006](../../../decisions/ADR-006-whatsapp-company-configuration-key.md) — configuration key decision.
- `frappe_whatsapp` multi-account support — already present, unused.
- Meta Business Account and approved templates for each additional company.

## Completion notes

Not implemented. Planning only.
