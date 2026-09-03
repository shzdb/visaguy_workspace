# Session 2026-09-03 — verification failure: lookup hash and origin gate

Follow-on from `01-implementation.md`. Triggered by a reported failure of
`POST /api/method/the_visaguy.visa_tracking.api.verification.verify_identity`
with `{"passport_number": "G2746747", "date_of_birth": "1994-10-11"}`,
returning the generic failure despite a Verified extraction and an open
application existing.

## Two independent causes

**The call carried no `Origin` header.** `verify_identity` called
`security.validate_cors` first, and `get_request_origin()` returns `""` when
the header is absent, so the request was rejected before any lookup ran.
Every failure returns the same constant body by design, so this was
indistinguishable from wrong credentials. Removed under ADR-013/TASK-021.

**The stored hash was built from a different string than any client can
type.** Even with the origin gate gone, verification would still have failed.
Measured on the dev site:

```
'G2746747'   -> 57c365e2f614f9...   matched no application
'G2746747<'  -> 5f8fe6c3be70fe...   matched VTA-2026-00739, VTA-2026-00756
```

Fixed under TASK-020.

## Method note: the false alarm I checked

Six of eight applications shared hash `7ca0e8e9…`, which looked like a
collision or a null-input bug. It is neither: the same test passport
`M00381296` was uploaded nine times. Worth recording because the shape of
that finding — many rows, one hash — reads as a serious defect until the
underlying data is checked.

## Method note: two of my own tests contradicted each other

While writing the TASK-019 tests, `test_optional_data_failure_does_not_invalidate_mrz`
failed. The cause was the test, not the code: the composite check digit
covers positions 22–43, so corrupting the optional-data check digit breaks
the composite too. Only the `<`/`0` substitution isolates an optional-only
failure, both carrying numeric value 0. That is now the fixture, and the
finding strengthened the TASK-003 amendment's argument.

## Pre-existing failures, verified as such

Full `visa_tracking` discovery reports 268 tests with 2 errors, both in
`TestProcessFileHandler`, failing in `_maybe_enqueue_client_status_recompute`
→ `is_job_enqueued` for want of `frappe.local.site`. Confirmed unrelated by
restoring the pristine `lifecycle_service.py`, re-running the module, getting
the identical two errors, and restoring the patched version.

## Commits

| Repo | Commit | Change |
|---|---|---|
| `passport_extractor` | `5f2403e` | TASK-019 filler check digit + TASK-020 padding strip |
| `the_visaguy` | `53ed207` | TASK-020 hash the normalized number |
| `the_visaguy` | `1a7af2e` | TASK-021 remove the origin gate |

All on `feat/visa-tracker`, committed locally, not pushed and not deployed.
`the_visaguy` also carried three files modified by a concurrent session
(`hooks.py`, `fileflo_collection_handlers.py`, `test_fileflo_inspection.py`);
those were left unstaged and untouched.

## Outstanding

**The recompute patch has not been run.** Host permission policy refused

```
bench --site visaguy execute the_visaguy.patches.recompute_lookup_hash_unkeyed.execute
```

twice. Until it runs the corrected code does not help the affected rows:
`VTA-2026-00756` keeps its stale hash and that passport still fails
verification. The patch is idempotent and derives from
`passport_number_normalized`.

**Deployment.** Risks 30 and 31 stay open until there is deployment evidence.

**`PEX-2026-00012` still stores `passport_number` as `G2746747<`.** Harmless
now that hashing uses the normalized field, but wrong in the desk UI.
