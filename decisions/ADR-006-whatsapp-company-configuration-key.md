# ADR-006: WhatsApp Configuration Key — Zone or Company

## Status

**Proposed** — must be accepted before FEAT-002 task 4 can begin.

## Context

`the_visaguy` resolves per-company WhatsApp configuration like this:

```
whatsapp_default = frappe.get_doc("Whatsapp Default", {"company": doc.custom_zone})
```

There is a type mismatch here:

- `CRM Lead.custom_zone` is a **Link → Zone** (label "Zone"), set by `visaguy_frappe_crm`'s `add_zone` hook.
- `Whatsapp Default.company` is a **Link → Company**.

The lookup passes a Zone name into a field constrained to Company. It resolves today only because the names coincide:

| Zone | Company | Match |
|---|---|---|
| `TVG` | `TVG` | yes |
| `TVG Qatar` | `TVG Qatar` | yes |
| `TVG Saudi` | `TVG Saudi` | yes |
| — | `TVG  India` (double space) | **no matching Zone** |

The same ambiguity runs through `is_enabled(company, customer)` in `whatsapp_default.py`, whose parameter is named `company` but receives a Zone from every caller.

This works by coincidence and fails on any of: renaming a Zone, adding a Zone whose name differs from its Company, or adding a Company with no Zone. `TVG  India` already demonstrates the third case. The double space also makes it fragile to any trimmed or normalised comparison.

The decision matters now because FEAT-002 adds a second sending company, and the wrong key would route a customer's messages from the wrong company's WhatsApp number — a visible, brand-damaging failure rather than a silent one.

## Options

### Option A — Key on Company, map Zone → Company explicitly

Add a `company` Link on `Zone`, and resolve `zone.company` before looking up `Whatsapp Default`.

- Configuration stays aligned with the legal and financial entity, which is what a WhatsApp Business Account is registered to.
- Consistent with `Whatsapp Default.company` as it already exists — no schema change to that DocType.
- Several zones can share one company, which matches reality: a company may operate multiple zones with one WhatsApp number.
- Requires backfilling `Zone.company` for existing zones and deciding what `TVG  India` maps to.

### Option B — Key on Zone

Change `Whatsapp Default.company` to a Link → Zone and rename it.

- Matches what the code actually passes today; the smallest code change.
- Zone is an operational/territorial concept, not a legal entity. Binding a WhatsApp Business Account — which is registered to a company and carries that company's quality rating and template approvals — to a territory is a category error.
- Forces one configuration per zone even when several zones share a number, duplicating configuration and inviting drift.
- A company with no zone cannot be configured at all.

### Option C — Support both, resolve at runtime

Accept either and try Company first, then Zone.

- No migration needed.
- Preserves the current ambiguity permanently and doubles the number of states to reason about. The failure mode — quietly selecting the wrong configuration — is exactly what this ADR exists to eliminate.

## Decision

**Recommended: Option A.**

A WhatsApp Business Account belongs to a legal entity. Template approvals, quality ratings, tier limits, and billing all attach to the company, not to a territory. Keying configuration on Company puts the configuration where the constraint actually lives, and lets several zones share one number without duplicated configuration.

Option B is tempting because it is the smaller diff, but it encodes the current accident as the design and will need reversing the first time a company operates two zones on one number.

Option C should be rejected outright: it keeps a silent mis-resolution possible, and the cost of that failure is messages going out from the wrong company.

*Pending owner acceptance.*

## Consequences if Option A is accepted

### Positive

- Configuration is keyed to the entity that actually owns the WhatsApp account.
- Many-zones-to-one-company works without duplicate configuration.
- The `is_enabled(company=...)` signature becomes honest about what it receives.
- Adding a company with no zones is possible.

### Negative

- Requires a migration: add `Zone.company`, backfill three existing zones, and update five lookup sites in `whatsapp_message.py`.
- A zone with no company mapped will resolve to nothing; needs an explicit validation and a clear failure.
- `TVG  India` needs a disposition decision — rename to remove the double space, or map explicitly and leave the name alone.
- Existing `Whatsapp Default` data for `TVG` must be verified to still resolve after the change.

## Migration outline

1. Add `Zone.company` (Link → Company, required).
2. Backfill by exact name match where it succeeds; resolve the rest by hand. Three zones today.
3. Change the five lookup sites to resolve `Zone → company` first.
4. Rename the `is_enabled` parameter and update its callers.
5. Add validation rejecting a Zone with no company.
6. Verify TVG messages still resolve to the same configuration before and after.

## Revisit when

A company legitimately needs more than one WhatsApp account (for example one per zone or per destination), which would make the key a composite rather than a single field. FEAT-002 open question 3 tracks this.
