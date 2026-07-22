# FEAT-001 pending-task handoff

These prompts are self-contained executor contracts for the remaining Visa Tracking work. Run them in dependency order; do not start a dependent prompt until its prerequisite report and commit SHA exist.

| Order | Task | Prompt | Prerequisite |
|---|---|---|---|
| 1 | TASK-004 | `08a2-task-004-resume.txt` | Existing interrupted work must be recovered, not discarded |
| 2 | TASK-006 | `08b-task-006-implementation.txt` | TASK-004 committed in both backend worktrees |
| 3 | TASK-007 | `08c-task-007-implementation.txt` | TASK-006 committed |
| 4 | TASK-009 | `08d-task-009-implementation.txt` | TASK-007 API contract committed; TASK-008 already complete |
| 5 | TASK-002 runtime closure | `09a-task-002-runtime-closure.txt` | Dedicated test site can be created safely; otherwise record blocker |
| 6 | TASK-010 | `10-task-010-final-verification.txt` | TASK-004/006/007/009 complete; performs final cross-repository gate |

Shared rules for every agent:

- Read `README.md`, `.agents/rules/project-rules.md`, the named task document, relevant accepted ADRs, and prior implementation reports before acting.
- The workspace is authoritative for intent/status; application repositories are authoritative for implementation and tests.
- SSH is `ssh -p 2257 shahzad@erpcode.tridz.in`. The remote bench is `/home/shahzad/bench`.
- Existing remote feature worktrees are under `/home/shahzad/visa-tracker-worktrees/` on `feat/visa-tracker`. Original app checkouts and `processflo` are read-only.
- Preserve every pre-existing or interrupted change. Never stash, reset, clean, force-checkout, or overwrite work to obtain a clean tree.
- Never run a migration, test, or write operation on active site `visaguy`. Use only the dedicated test site authorized by TASK-010.
- Use bare `bench` from `/home/shahzad/bench`, always with an explicit `--site` for site operations. Do not probe with `bench --version`, `bench --help`, or `which bench`.
- Do not set Git identity, pass `--author`, or set author/committer environment variables. Use the environment defaults.
- Do not push, deploy, add remotes, expose secrets/PII, or use real passport data.
- Commit only intentional application-repository changes. Do not commit workspace lifecycle documents unless the coordinating workspace agent explicitly owns that step.
- Reports must distinguish `present`, `source-wired`, `configured-unverified`, and `runtime-verified` evidence.

Suggested Kimi invocation from this workspace:

```bash
kimi -p "$(< ongoing/visa-tracking-implementation/prompts/<prompt-file>)" \
  --add-dir /home/shzd/Projects/workspaces/visaguy_workspace
```

Remote work is performed through SSH by the executor. The coordinator must review every diff, test result, report, and commit before releasing the next dependency.
