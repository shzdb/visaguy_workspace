# ADR-008: Deployment Authority and Completion Gates

## Status

Accepted

## Context

VisaGuy spans 30 bench apps across a shared production site. Merging a feature branch into `develop` or `main` and deploying it affects every tenant of that site at once, and several apps carry class overrides and hooks that interact — three CRM layers, a helpdesk fork, an HRMS wrapper, payment gateway webhooks.

Agents working in this workspace have direct SSH access to the bench and push access to the application repositories. Without an explicit rule, an agent could reasonably conclude that finishing a task includes shipping it.

Separately, "done" has been ambiguous. A feature whose code is merged and running on staging is not the same as one serving customers, and treating those as one event has previously let work be recorded as complete before it was live.

## Decision

**Merging and deploying are manual actions performed by the project owner. No agent may perform them.**

An agent may:

- prepare change lists and merge ordering,
- report current branch, tag, and deployment state,
- push feature branches to their upstreams so work is not lost,
- record confirmed outcomes in this workspace after the owner reports them.

An agent may **not**:

- merge into `develop` or `main`,
- deploy to staging or live,
- tag a release,
- alter branch checkout state on the bench.

**Staging deployment and live deployment are separate events, confirmed separately.**

Before any feature moves to `features/completed/`, the agent must ask the project owner two distinct questions:

1. Has this been **deployed to staging**?
2. Has this been **deployed live**?

Confirmation of staging alone is never sufficient. Neither is a merged pull request.

Each feature records the two gates explicitly. See [TASK-011](../tasks/blocked/visa-tracking/TASK-011-staging-and-live-deployment.md) for the pattern: a task in the deployment repository scope, owned by the project owner, with a fill-in block per gate.

## Consequences

### Positive

- A shared production site cannot be changed by an agent acting on a plausible-looking task.
- The owner retains the judgement call about when a change is safe to ship, which depends on business timing an agent cannot see.
- "Completed" in this workspace means live, so the status is trustworthy without cross-checking.
- Pushing feature branches remains permitted, so the no-deploy rule never becomes a reason to lose work.

### Negative

- Features sit in `ongoing/` longer, and the workspace will usually show work finished but undeployed.
- The owner is a serialisation point for shipping.
- Requires discipline to record gate confirmations promptly, or the workspace drifts behind reality — the exact failure the 2026-08-06 audit found.

## Alternatives considered

- **Allow agents to merge to `develop` but not `main`.** Rejected: `develop` feeds staging, which is a real environment, and the merge itself is where cross-app conflicts surface.
- **Single completion gate at merge.** Rejected: merged is not deployed, and deployed to staging is not live. Collapsing them is what allowed prior status drift.
- **Allow deployment when a task explicitly authorises it.** Rejected for now: a task is written by an agent or from a plan, so this would let the constraint author its own exception.

## Revisit when

A staging environment exists that is fully isolated from production and cheap to rebuild, or automated deployment with reliable rollback makes owner-in-the-loop unnecessary for staging specifically.
