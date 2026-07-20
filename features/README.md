# Features

This directory contains feature documents. A feature is a user-facing capability or significant architectural change.

## Lifecycle states

- `planned/` — accepted for the backlog but not yet started.
- `ongoing/` — actively being worked on.
- `completed/` — implementation and validation evidence recorded.
- `parked/` — intentionally deferred; must include a reason and revisit condition.

## Entry criteria

- A feature must have a clear scope, user value, acceptance criteria, and dependencies.
- Do not invent features not supported by accepted evidence.
- Use `.agents/templates/feature.md` to create a new feature document.

## Status alignment

The document metadata `status` must match the folder it lives in. When a feature moves between states, move the file to the corresponding folder and update its `updated` date.
