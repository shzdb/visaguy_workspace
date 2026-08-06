# ADR-007: WhatsApp Configuration Is Keyed on Zone

## Status

Accepted

## Context

`the_visaguy` resolves per-market WhatsApp configuration like this:

```
whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": doc.custom_zone})
```

There is a field-type mismatch: `CRM Lead.custom_zone` is a Link → `Zone`, while `Whatsapp Default.company` is a Link → `Company`. The lookup resolves today only because three zone names coincide with three company names.

The question is which axis the configuration should actually be keyed on. [ADR-006](ADR-006-zone-and-company-as-distinct-domain-axes.md) establishes that Zone and Company are independent, and that `TVG India` is a back-office branch whose employees handle UAE and Qatar leads.

That makes the answer concrete rather than abstract. A lead created by an Indian employee for a UAE customer carries `custom_zone = TVG` and `custom_company = TVG India`. If WhatsApp configuration were keyed on Company:

> A UAE customer would receive their visa updates from the TVG India back-office WhatsApp number.

That is wrong operationally and wrong for the brand. The customer belongs to the UAE market and must hear from the UAE number, regardless of which office keyed in their details.

A WhatsApp Business Account is nevertheless *owned* by a legal entity — Meta registers it to a company. That ownership is a fact about the account held in Meta's console; it is not modelled in Frappe and is not part of this decision.

## Decision

**`Whatsapp Default` is keyed on Zone.** Rename the `company` field to `zone` and retype it as Link → `Zone`.

**One zone has exactly one WhatsApp account.** Multiple numbers per zone are explicitly out of scope and must not be designed for.

Concretely:

| Zone | Whatsapp Default | WhatsApp Account |
|---|---|---|
| `TVG` | one record | e.g. `Visaguy UAE` |
| `TVG Qatar` | one record | its own |
| `TVG Saudi` | one record | its own |
| — | none needed | `TVG  India` is back office, no customers |

`TVG India` needs no `Whatsapp Default` record. Its employees' messages go out under the zone of the lead they are working on, which is exactly the intended behaviour.

The `is_enabled(company, customer)` helper in `whatsapp_default.py` must have its parameter renamed to `zone`, since every caller already passes a zone.

## Consequences

### Positive

- A customer always hears from the WhatsApp number of the market serving them, independent of which office handles the work.
- The back-office model works transparently — TVG India staff need no WhatsApp configuration at all.
- The field type finally matches what every caller passes; the lookup stops depending on a name coincidence.
- Adding a market means adding a Zone, a `WhatsApp Account`, and a `Whatsapp Default` — no code change.
- Correctly predicts that there are three zones and three WhatsApp configurations, not four.

### Negative

- Requires a migration: rename and retype the field on `Whatsapp Default`, migrate the existing `TVG` record, and update five lookup sites plus `is_enabled`.
- A zone with no `Whatsapp Default` record must fail cleanly and observably rather than silently sending nothing.

## Alternatives considered

- **Key on Company.** Rejected. This was the recommendation in an earlier draft of ADR-006, made before the back-office model was understood. It would route a UAE customer's messages through the TVG India number whenever an Indian employee created the lead.
- **Key on both, resolving Company first then Zone.** Rejected: preserves the ambiguity permanently, and its failure mode is quietly selecting the wrong number.
- **Leave the mismatch and rely on matching names.** Rejected: one zone rename breaks live customer messaging, and `TVG  India` (double space) already shows the naming assumption does not hold.

## Migration outline

1. Add `zone` (Link → Zone) to `Whatsapp Default`; keep `company` temporarily.
2. Backfill `zone` from the existing `company` value — the current single record is `TVG`, which is a valid Zone name.
3. Update the five lookup sites in `handlers/whatsapp_message.py` and `is_enabled` in `whatsapp_default.py`.
4. Verify TVG messages resolve to the same configuration before and after.
5. Drop `company` and change `autoname` to `field:zone`.
6. Add validation rejecting an enabled `Whatsapp Default` whose zone has no bound `WhatsApp Account`.

## Revisit when

A zone needs more than one WhatsApp number — for example one per destination — which would make the key composite. Deliberately not designed for now. Or a back-office branch begins serving customers directly under its own identity.
