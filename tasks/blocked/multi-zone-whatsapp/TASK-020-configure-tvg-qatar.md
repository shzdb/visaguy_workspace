---
id: TASK-020
feature: FEAT-002
title: Configure TVG Qatar and prove multi-zone routing
status: blocked
repository: none (configuration)
owners:
  - project-owner
depends_on:
  - TASK-018
  - TASK-019
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Configure TVG Qatar and prove multi-zone routing

## Objective

Configure TVG Qatar as the second zone and confirm, with real evidence, that its messages leave from its own WhatsApp number.

This is the task that actually proves FEAT-002. Everything before it is internally consistent code and a verified migration; none of it demonstrates that a second zone works, because until now only one `WhatsApp Account` has existed.

## Blocked by

1. **[TASK-018](../../ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md)** — Qatar WABA, verified number, and six approved templates. External lead time; start first.
2. **[TASK-019](../../completed/multi-zone-whatsapp/TASK-019-implement-zone-routing.md)** deployed. Not merely written — until it is deployed, `waflo` ignores per-zone configuration entirely.
3. **[TASK-017](../../blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md)**, because FEAT-002 is branched on top of FEAT-003 and they deploy together.

## Procedure

Follow [`docs/operations/zone-whatsapp-onboarding.md`](../../../docs/operations/zone-whatsapp-onboarding.md). Summary:

1. `WhatsApp Account` for Qatar — **do not set `is_default_outgoing` or `is_default_incoming`**. Those flags are global; setting them would redirect every zone's traffic to Qatar.
2. Six `WhatsApp Templates` records with zone-suffixed `template_name` and unchanged `actual_name`, each bound to the Qatar account.
3. `Whatsapp Default` for zone `TVG Qatar` — bind the account, add all five event templates and both feedback defaults, then enable. Saving with anything missing is rejected and the error names the gap.

## Validation — this is the point of the task

- A message triggered for a **TVG Qatar** lead produces a `WhatsApp Message` whose `whatsapp_account` is **Qatar's**, not `Visaguy UAE`. Check the record, not the code.
- The same event for a **TVG** lead still shows `Visaguy UAE`. No regression.
- **Back-office isolation:** a lead with `custom_zone = TVG` and `custom_company = TVG India` — created by an Indian employee for a UAE customer — sends from the **UAE** number. This is the case that would have silently broken had configuration been keyed on Company ([ADR-006](../../../decisions/ADR-006-zone-and-company-as-distinct-domain-axes.md)).
- An inbound message to Qatar's number receives its default reply **from Qatar's number**.
- A feedback reply on Qatar's number is matched against **Qatar's** feedback configuration, not TVG's.
- A deferred (rate-limited) Qatar message is retried from **Qatar's** number.
- A zone with an intentionally missing event template logs a warning naming the zone, and does not raise or affect other zones.

## Definition of done

Two zones send from two numbers, verified in `WhatsApp Message` records, with the back-office case and the feedback round trip both confirmed.

Only then may FEAT-002 move to `features/completed/`, and only after TASK-017's staging and live gates are both recorded ([ADR-008](../../../decisions/ADR-008-deployment-authority-and-completion-gates.md)).
