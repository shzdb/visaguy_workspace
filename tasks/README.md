# Tasks

This directory contains implementation-ready task documents.

## Lifecycle states

- `ready/` — tasks that require no new product or architecture decision and can be picked up by an implementation agent.
- `in-progress/` — tasks currently being worked on.
- `blocked/` — tasks that cannot proceed until an external dependency or decision is resolved.
- `completed/` — tasks with implementation and validation evidence recorded.

## Entry criteria

- A task must reference a feature and have a clear objective, required behaviour, constraints, expected changes, validation steps, and definition of done.
- Only mark a task `ready` when it requires no new product or architecture decision.
- Use `.agents/templates/task.md` to create a new task document.

## Status alignment

The document metadata `status` must match the folder it lives in. When a task moves between states, move the file to the corresponding folder and update its `updated` date.
