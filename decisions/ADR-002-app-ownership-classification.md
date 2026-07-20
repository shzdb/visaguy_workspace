# ADR-002: App Ownership Classification

## Status

Accepted

## Context

The VisaGuy bench contains 29 app repositories with mixed origins. Some are internally maintained, some are true upstream checkouts, and two are maintained forks of upstream projects. A consistent ownership rule is needed for documentation, security review, and upgrade planning.

## Decision

- Repositories owned by `tridz-dev` or `tvgglobal` are classified as internally maintained.
- `crm` and `helpdesk` are internally maintained forks of Frappe CRM and Frappe Helpdesk, respectively, and are documented as maintained apps.
- All other repository owners are classified as external/upstream.
- This rule is applied uniformly across the repository catalog, risk register, and operational runbooks.

## Consequences

### Positive

- Simple, auditable rule that matches the Git remote evidence.
- Makes upgrade and security review scope explicit.

### Negative

- A future fork of an external app by `tridz-dev` or `tvgglobal` would automatically be classified as internally maintained, even if it has minimal customization.

## Alternatives considered

- Classify by amount of customization. Rejected because customization depth is hard to measure consistently and can change over time.
- Classify by remote name. Rejected because remotes are not uniform across repos.

## Revisit when

A new ownership model is introduced (for example, a dedicated `visaguy` organization) or when a maintained fork is archived or returned to upstream.
