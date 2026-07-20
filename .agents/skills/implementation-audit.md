# Implementation Audit Skill

## Purpose

Audit implementation evidence in application repositories against claims in this workspace. This skill is read-only: it does not modify code or configuration.

## When to use

- Verifying that a completed task matches its acceptance criteria.
- Checking whether an architecture claim still holds after upstream changes.
- Investigating a bug or regression before creating a fix task.
- Validating that a customization layer has not been broken by an upgrade.

## Procedure

1. Read the workspace claim
   - Locate the relevant feature, task, ADR, or architecture document.
   - Identify the specific claim, interface, or behavior to audit.

2. Map the claim to application evidence
   - Find the owning application repository.
   - Look at the current branch/HEAD, hooks, overrides, fixtures, and tests.
   - Prefer source symbols and stable file paths over transient runtime state.

3. Apply verification labels
   - **present** — the capability surface exists.
   - **source-wired** — hooks/imports/caller-callee relationships are evidenced.
   - **configured-unverified** — config key names exist but activation is not verified.
   - **runtime-verified** — live traffic or active configuration confirmed.

4. Record findings
   - Update the relevant workspace document or task with audit evidence.
   - If the claim no longer holds, move the task/feature to `blocked` or `parked` and explain.

## Constraints

- Do not run commands that mutate application repositories or the remote bench.
- Do not read secrets, production data, or raw logs.
- Do not copy dirty diffs or generated artifacts into the workspace.
- Keep findings concise and cite specific files/symbols where possible.

## Output

- A short audit note added to the task/feature document, or
- A completion report using `.agents/templates/completion-report.md`.
