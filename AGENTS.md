# Agent Instructions

This repository is a project workspace, not an application-code repository.

## Before working

1. Read `README.md`.
2. Read `.agents/rules/project-rules.md`.
3. Read relevant documentation and accepted ADRs in `docs/` and `decisions/`.
4. Read the relevant feature document in `features/`.
5. For implementation work, use only a task marked `ready` in `tasks/ready/`.
6. Load the applicable workflow under `.agents/skills/` when present.
7. For questions about libraries, frameworks, API references, or CLI commands, use the available Context7 integration first. If it is unavailable or returns no relevant documentation, state that and fall back to the product's official primary documentation or installed CLI help. Use `.agents/` for this workspace's canonical rules, skills, and templates.

## Authority model

- This workspace is authoritative for intent, decisions, status, risks, and open questions.
- Application repositories are authoritative for implementation, tests, generated schemas, builds, and releases.
- Do not put application code, secrets, production data, or sensitive raw data in this repository.

## Discovery

- Rules: `.agents/rules/project-rules.md`
- Skills: `.agents/skills/`
- Templates: `.agents/templates/`
- Canonical docs: `docs/index.md`
- Features: `features/README.md`
- Tasks: `tasks/README.md`

## Verification labels

Use these labels consistently when reporting evidence:

- **present** — capability surface or settings DocType exists in source.
- **source-wired** — hooks, imports, or caller/callee relationships are evidenced in code.
- **configured-unverified** — environment/config values observed only as key names; activation not verified.
- **runtime-verified** — live traffic, provider call, or active configuration confirmed.

This audit runtime-verified SSH access, installed apps, versions, and CLI help; it did not verify provider traffic or production workflows.
