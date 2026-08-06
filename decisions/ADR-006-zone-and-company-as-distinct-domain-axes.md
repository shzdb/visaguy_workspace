# ADR-006: Zone and Company Are Distinct Domain Axes

## Status

Accepted

This ADR records architecture that already exists in VisaGuy and has been in production use. It is written down because it is foundational, non-obvious, and easy to get wrong — an earlier draft of this ADR got it wrong and recommended the opposite.

## Context

VisaGuy operates four companies and three zones:

| Company (legal entity) | Zone (market) |
|---|---|
| `TVG` (UAE) | `TVG` |
| `TVG Qatar` | `TVG Qatar` |
| `TVG Saudi` | `TVG Saudi` |
| `TVG  India` | — none |

The names overlap for three of the four, which invites the assumption that Zone is a synonym or a derivative of Company. **It is not.** They are independent axes, and a record carries both.

- **Zone** is the operational and market context an employee works in. It drives lead management, operations, and permission scoping, and carries market attributes — the `Zone` DocType has a `currency` field.
- **Company** is the legal entity that employs the person. It drives financial, statutory, and HR concerns.

The decisive case is **`TVG India`, which is a back-office branch**. Its employees sit in India but handle leads and operations belonging to the UAE or Qatar operation. Therefore:

> A Lead can legitimately have `custom_zone = TVG` (the UAE market it belongs to) and `custom_company = TVG India` (the entity employing whoever created it). Staff assigned to the `TVG` zone in their Employee record can access that lead.

This also explains the count asymmetry: there are four companies but three zones. **`TVG India` having no zone is correct by design, not a data gap** — a back office serves other zones and has no customers of its own.

## Evidence

| Claim | Evidence |
|---|---|
| Both axes are set independently at creation | `visaguy_frappe_crm/functions/add_zone.py:14-15` assigns `doc.custom_zone` and `doc.custom_company` from separate keys on the session user's Employee record |
| `Employee` carries both | `custom_zone` (Link → Zone) and `company` on the Employee custom fields |
| Permission scoping can use either axis | `visaguy_frappe_crm/functions/lead_restrictions.py:16-23` branches on `TVG User Restriction.lead_manager_company_restriction` vs `.lead_manager_zone_restriction`, emitting either a `custom_company` or a `custom_zone` filter |
| Zone carries market attributes | `add_zone.py:17` reads `currency` from the `Zone` record onto the lead |
| `CRM Lead` carries both | `custom_zone` (Link → Zone) and `custom_company` custom fields |

## Decision

Zone and Company are permanently distinct. Neither may be derived from the other, and code must not treat matching names as evidence that they are equivalent.

**Routing rule:**

- Anything **customer-facing** keys on **Zone** — WhatsApp numbers and messaging configuration, currency, market defaults, customer communication branding.
- Anything **legal, financial, or HR** keys on **Company** — invoices, payroll, statutory and GST compliance, employment records.
- **Permission scoping may use either**, and the choice is configuration, not a hardcoded assumption. See `TVG User Restriction`.

When a design question presents itself as "which company does this belong to", first check whether the real question is "which market is this customer in". If it is customer-visible, the answer is Zone.

## Consequences

### Positive

- The back-office model works: Indian staff can serve UAE and Qatar customers without those customers seeing anything Indian.
- Market attributes such as currency live with the market, and a zone can be added or retargeted without touching the legal entity structure.
- Permission scoping stays configurable rather than baked in.

### Negative

- Every new feature touching either axis must make a conscious choice, and the wrong choice can be invisible in a single-market setup.
- The name overlap between three zones and three companies actively hides mistakes during development. Code that keys the wrong axis will appear to work.
- Data quality matters: `TVG  India` contains a double space, so any name-based matching across the two axes is fragile as well as wrong.

## Alternatives considered

- **Derive Zone from Company.** Rejected: impossible for `TVG India`, which serves multiple zones and has none of its own.
- **Derive Company from Zone.** Rejected: loses the employing entity, which is required for payroll, invoicing, and compliance.
- **Collapse the two into one field.** Rejected: it would make the back-office operating model unrepresentable, which is a core part of how the business runs.

## Revisit when

A back-office branch acquires its own customer-facing market, a zone spans multiple currencies, or a company needs several zones with genuinely separate customer-facing identities within one market.
