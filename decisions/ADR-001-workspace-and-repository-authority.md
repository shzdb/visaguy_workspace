# ADR-001: Workspace and Repository Authority

## Status

Accepted

## Context

VisaGuy spans multiple application repositories (Frappe bench apps and three frontend repositories) plus a project workspace. Implementation details, tests, and builds live in application repositories, while product intent, architecture decisions, procedures, and status need a durable home that survives chat history and is discoverable by both humans and agents.

## Decision

- The workspace repository (`visaguy_workspace`) is authoritative for intent, architecture understanding, decisions, procedures, risks, open questions, feature/task scope, and project status.
- Application repositories are authoritative for implementation, tests, generated schemas, build configuration, release versions, and deployment artifacts.
- Implementation work must be driven by workspace tasks and must respect the boundaries above.

## Consequences

### Positive

- Clear separation between "what we decided" and "how it was built".
- Agents can discover canonical rules and status without re-reading application code.
- Product and architecture decisions are durable and version-controlled.

### Negative

- Requires discipline to keep workspace documents aligned with application changes.
- Risk of drift if completion reports are not recorded.

## Alternatives considered

- Treat one application repository as the single source of truth. Rejected because the system is multi-repo and no single repo represents product intent.
- Maintain documentation only in chat history. Rejected because it is not discoverable or version-controlled.

## Revisit when

A single application repository becomes the clear monorepo for both product and implementation, or when the workspace stops being actively maintained.
