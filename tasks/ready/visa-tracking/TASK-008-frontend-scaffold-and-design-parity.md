---
id: TASK-008
feature: FEAT-001
title: visa_tracker SPA scaffold and design parity with the consumer website
status: ready
repository: visa_tracker
owners: []
depends_on:
  - TASK-007
expected_files: []
created: 2026-07-20
updated: 2026-08-06
---

# visa_tracker SPA scaffold and design parity with the consumer website

## Objective

Create the standalone public `visa_tracker` React SPA and establish visual parity with `visaguy-website-client` before any tracking logic is written.

## Context

This is the first genuinely unstarted task in FEAT-001. All backend work (TASK-001 through TASK-007) is implemented on `feat/visa-tracker` branches. No frontend work exists in any repository or on the remote bench.

## Inputs

- Read-only access to `visaguy-website-client` (`tvgglobal/visaguy-website-client`) as the design reference.
- The approved public information boundary from TASK-007.

## Required behaviour

Initialise a new local repository with the fixed stack: React, Vite, TypeScript, React Router, Tailwind CSS, shadcn/ui, Axios, React Hook Form, and Zod.

Match the VisaGuy consumer visual language: same logo and approved brand assets, header and footer composition, typography scale, colors and CSS variables, button/input/card/alert/loading treatment, spacing, radius, shadow, and responsive behaviour.

## Constraints

- Presentational components may be copied and adapted. Next.js-specific routing, `next/image`, server components, environment access, authentication, and data-fetching code must **not** be copied into the Vite app.
- Never commit tracker changes into `visaguy-website-client`.
- No Git remote is required for this task; local commits are sufficient.

## Blocking prerequisite

`visaguy-website-client` is **not currently cloned on this workstation**. It must be cloned read-only from `tvgglobal/visaguy-website-client` before design parity can be assessed. See `docs/operations/local-development.md`.

## Validation

- `npm run build` (or the chosen package manager equivalent) succeeds.
- A side-by-side comparison of header, footer, typography, and primary button/card/alert against the consumer website shows no visible drift on desktop and mobile.
- The repository contains local commits.

## Definition of done

The SPA builds, renders the shared shell, and is visually indistinguishable from the consumer website chrome. No tracking logic is required yet.
