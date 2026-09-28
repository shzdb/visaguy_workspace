# Soft-launch implementation — final report (2026-09-28)

## Result

TASK-031 to TASK-036 are built, reviewed, merged into `feat/visa-tracker` on the
bench (installed checkouts) and verified on `visa-tracker-test.localhost`.
Nothing is pushed or deployed, and nothing was run on `visaguy`.

| Repo | HEAD | On-site suite |
|---|---|---|
| the_visaguy | `3872390` | 638 run, OK (`--skip-test-records`) |
| passport_extractor | `84da2fe` | 98 run, OK (`--skip-test-records`) |

## How it was built

- Wave 1: five Cursor executors in parallel on separate branches with a
  shared-file ownership table and two cross-task contracts. Two correctives
  (TASK-034 Settings System Manager row; TASK-032 field_order guard).
- Integration by the orchestrator (owner choice after the permission check
  refused an unsupervised merge agent): merges, test-site migrate, suites,
  one test fix (`84da2fe`).
- TASK-035 by a sixth executor after TASK-031 fixed the outcome codes.

## Verification level

- runtime-verified (test site): migrate and patch; both suites; field order,
  permissions, layout, workspace, report; smoke test S1–S13 of the real chain
  with captured jobs and simulated OCR; report reasons equal ensure outcomes.
- not verified: real OCR on real passports, browser UI, real worker runs,
  `visaguy` data (owner).

## Owner next steps

1. On `visaguy`: set `Visa Tracker Settings.passport_field_ids` to include
   `passport`, `require_manual_verification` off; install
   `passport_extractor`; migrate (runs the TASK-036 patch and prints counts).
   Until then keep `Visa Tracker Settings.enabled` off there, because the
   merged save hook is live after the next worker reload.
2. Copy the pilot passport files and run the 25 scenarios
   (`07-soft-launch-plan.md`, Phase 3).
3. Browser checks as an Operations Associate: Process File section and
   buttons, Passport Extraction Verify dialog and file preview, coverage report.
4. Push and deploy, together with the undeployed SPA work (TASK-017, 025, 026).

Open gaps: `05-runtime-verification-and-gaps.md` (G2 passport_field_ids, G4
HEIC, G5 = risk 49, closed by the owner as not applicable, G7 preview access).
