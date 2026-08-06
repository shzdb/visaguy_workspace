# Agent Instructions

This repository is a project workspace, not an application-code repository.

## Before working

1. Read `README.md`.
2. Read `.agents/rules/project-rules.md`.
3. Read `decisions/README.md` — the ADR index and decision log — plus relevant documentation in `docs/`.
4. Before changing behaviour in any app, read `docs/architecture/workflows.md` for the end-to-end code flow you are touching.
5. Read the relevant feature document in `features/`.
6. For implementation work, use only a task marked `ready` in `tasks/ready/`.
7. Load the applicable workflow under `.agents/skills/` when present.
8. For questions about libraries, frameworks, API references, or CLI commands, use the available Context7 integration first. If it is unavailable or returns no relevant documentation, state that and fall back to the product's official primary documentation or installed CLI help. Use `.agents/` for this workspace's canonical rules, skills, and templates.

## Core domain rule

**Zone and Company are independent axes.** Zone is the customer-facing market; Company is the employing legal entity. Neither derives from the other, and three of the four names coincide — so keying the wrong one looks correct until a back-office record passes through it.

Customer-facing scoping uses **Zone**. Legal, financial, and HR scoping uses **Company**. Permission scoping may use either, by configuration.

Read `docs/architecture/system-overview.md` § Core domain axes and `decisions/ADR-006` before designing anything that scopes data.

## Authority model

- This workspace is authoritative for intent, decisions, status, risks, and open questions.
- Application repositories are authoritative for implementation, tests, generated schemas, builds, and releases.
- Do not put application code, secrets, production data, or sensitive raw data in this repository.

## Discovery

- Rules: `.agents/rules/project-rules.md`
- Skills: `.agents/skills/`
- Templates: `.agents/templates/`
- Canonical docs: `docs/index.md`
- Code flows: `docs/architecture/workflows.md`
- Features: `features/README.md`
- Tasks: `tasks/README.md`

## Deployment authority

Merging to `develop`/`main` and deploying to staging or live are **manual, project-owner-only** actions. No agent may perform them. Staging and live are separate events. Before marking any feature complete, ask the owner both questions separately — see `.agents/rules/project-rules.md`.

## Verification labels

Use these labels consistently when reporting evidence:

- **present** — capability surface or settings DocType exists in source.
- **source-wired** — hooks, imports, or caller/callee relationships are evidenced in code.
- **configured-unverified** — environment/config values observed only as key names; activation not verified.
- **runtime-verified** — live traffic, provider call, or active configuration confirmed.

This audit runtime-verified SSH access, installed apps, versions, and CLI help; it did not verify provider traffic or production workflows.
