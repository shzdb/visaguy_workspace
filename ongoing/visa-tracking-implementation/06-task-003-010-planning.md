# TASK-003 through TASK-010 planning

## Dependency order

| Track | Order | Repository |
|---|---|---|
| Passport extraction | TASK-002 static implementation -> TASK-003 | `passport_extractor` |
| Tracking model and integration | TASK-005 -> TASK-004 -> TASK-006 -> TASK-007 | `the_visaguy`, with the minimal generic TASK-004 event in `fileflo` |
| Public frontend | TASK-008 -> TASK-009 | local `visa_tracker`; `visaguy-website-client` remains read-only |
| Final gate | TASK-010 after TASK-002 through TASK-009 | all implementation repositories plus workspace evidence |

TASK-003, TASK-005, and TASK-008 are independent first-wave tasks. TASK-009 may use mocks while TASK-007 is being implemented, but it cannot complete contract verification before TASK-007. TASK-010 is the only final integration/runtime/rollout-evidence gate.

## Ground assumptions and boundaries

- Remote feature worktrees are `/home/shahzad/visa-tracker-worktrees/passport_extractor`, `/home/shahzad/visa-tracker-worktrees/the_visaguy`, and `/home/shahzad/visa-tracker-worktrees/fileflo`.
- Frontend implementation is local at `/home/shzd/Projects/tridz/visa_tracker`; `/home/shzd/Projects/tridz/visaguy-website-client` is read-only.
- TASK-001 source evidence is authoritative for FileFlo `field_id`, `FF Document`, Lead/CRM Lead, and PF Process File joins.
- `processflo` remains read-only. Any custom fields on PF Process File are owned and shipped by `the_visaguy` fixtures.
- TASK-002 is statically implemented. Its migration and integration tests remain deferred until `passport-extractor-test.localhost` can be safely created.
- No task may migrate or run tests on active site `visaguy`, expose credentials or PII, push, deploy, or override Git author identity.
- Tailwind CSS v4 uses CSS-first `@theme` design tokens; TASK-008 does not add a legacy Tailwind configuration file.
- TASK-010 produces verification and rollout evidence only; it does not authorize deployment.
