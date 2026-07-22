# 09h — Settings Loader (D1) and Enqueue (D2) Corrective

Site: `visa-tracker-test.localhost`. Worktree: `/home/shahzad/visa-tracker-worktrees/the_visaguy`, branch `feat/visa-tracker`. Starting HEAD `4593a845f336763a4afdce2d155bb96471c6b198` (clean). Commit produced by this phase: **`ccbd63240d952979a62ceb408e987ff9e3c4c0cd`**.

## D1 — Settings loader always returned `None`

**Root cause.** `the_visaguy/visa_tracking/utils/settings.py::_load_settings()` guarded with
`if not frappe.db.table_exists(SETTINGS_DOCNAME): return None`. `Visa Tracker Settings` is a
Single (`issingle: 1`); Singles have no dedicated table (`tabVisa Tracker Settings` never
exists — rows live in `tabSingles`), so the guard was unconditionally true and the loader
unconditionally returned `None` on every real site.

**Fix applied.** Replaced the table-existence check with a DocType-existence check:
`frappe.db.exists("DocType", SETTINGS_DOCNAME)`, keeping the existing
`except frappe.DoesNotExistError: return None` fallback for the case where the DocType exists
but no Single row has been saved yet. This still returns `None` during the pre-install /
pre-migrate window (the legitimate original intent of the guard — `frappe.flags.in_install` is
untouched and still handled by the caller), but now resolves correctly once the DocType is
installed, regardless of it being a Single.

**Rationale for this approach over alternatives:** deleting the guard outright would remove the
install-time safety net explicitly required by the dispatch; checking `tabSingles` row presence
directly was rejected as more fragile (couples the loader to Frappe's Single storage
implementation) when `DoesNotExistError` already covers "DocType exists, no row yet" more
robustly via the standard `frappe.get_doc` path.

**Call sites checked.** `get_visa_tracker_settings()` (only caller of `_load_settings`) —
unchanged, still just consumes the return value. All downstream consumers
(`is_tracking_enabled`, `is_public_tracking_enabled`, `is_passport_extraction_enabled`,
`validate_cors`, `create_tracking_application`, `run_fileflo_inspection`,
`reconcile_missing_extractions`) required no changes — they already correctly handle a
non-`None` settings doc; they had simply never received one.

### V2 — runtime evidence (runtime-verified)

Before/after captured via `bench console` on the live site:

```
BEFORE_GUARD table_exists: False        # frappe.db.table_exists("Visa Tracker Settings")
AFTER_GUARD doctype_exists: Visa Tracker Settings   # frappe.db.exists("DocType", ...)
tabSingles_rows: 33                     # frappe.db.count("Singles", {"doctype": ...})
```

After the fix, with cache cleared:

```
AFTER_FIX settings doctype: Visa Tracker Settings
AFTER_FIX enabled: 1
AFTER_FIX enable_public_tracking: 1
AFTER_FIX enable_passport_extraction: 1
```

Previously-dead path exercised: created a synthetic `FF File Collection` (no rows,
`ff_file_collection.json` has no required fields) and called
`run_fileflo_inspection(coll.name)` directly:

```
V2_INSPECTION_RESULT: {'status': 'ok', 'processed_rows': []}
```

Before the fix this call always short-circuited to `{"status": "disabled", "processed_rows": []}`
(confirmed statically: `_is_inspection_enabled` requires a non-`None` settings object, which
`get_visa_tracker_settings()` could never produce). Synthetic collection deleted after the check.

## D2 — `enqueue_passport_extraction` raised `AttributeError` on every created extraction

**Root cause.** `frappe.enqueue(..., enqueue_after_commit=True)` returns `None` immediately —
confirmed by reading the installed Frappe source
(`/home/shahzad/bench/apps/frappe/frappe/utils/background_jobs.py:168-170`):
`if enqueue_after_commit: frappe.db.after_commit.add(enqueue_call); return`. The orchestrator
then did `job.id`, which raised `AttributeError: 'NoneType' object has no attribute 'id'` on
every "created" extraction (100% of the time this branch executed).

**Fix applied.** Generate the job id ourselves (`uuid.uuid4().hex`) before enqueueing, pass it
via `frappe.enqueue(..., job_id=job_id, enqueue_after_commit=True)`, and record that same
`job_id` via `pex.db_set("last_job_id", job_id)`. The function now returns `job_id` (a string)
instead of a `Job`/`None`.

**Why this is safe / correct semantics:** read `create_job_id()` and `get_job()` in the same
Frappe source file — `frappe.enqueue(job_id=...)` namespaces the caller-supplied id to
`f"{site}::{job_id}"` internally, and lookup helpers (`get_job`, `is_job_enqueued`,
`get_job_status`) re-apply that same namespacing when given the raw id back. So recording the
raw (pre-namespaced) id we generated is exactly what those lookup helpers expect — no
information is lost. `enqueue_after_commit=True` is unchanged, so the race the flag exists to
prevent (a worker picking up a record before its insert transaction commits) is still avoided.

**Call sites checked (grepped for `enqueue_passport_extraction` across the app):**
- `the_visaguy/visa_tracking/services/fileflo_inspection_service.py:91` — was `job = enqueue_passport_extraction(...); ... "last_job_id": job.id`. Updated to `job_id = enqueue_passport_extraction(...); ... "last_job_id": job_id` since the return value's type changed from `Job` to `str`.
- `the_visaguy/visa_tracking/tests/test_fileflo_inspection.py:283` — unit test that mocked `frappe.enqueue` and asserted on `job.id`; this test directly encoded the pre-fix (buggy) contract and was rewritten (see below).
- No other call sites found in the app.

### V3 — runtime evidence (runtime-verified)

Created a real private `File` (synthetic `.txt` content, `is_private=1`) and a real
`Passport Extraction` referencing it (status `Queued`, synthetic `source_row`), then called
`enqueue_passport_extraction(pex, settings)` directly on the live site:

```
V3_FILE_URL: /private/files/synthetic-passport-P0000000.txt
V3_PEX_CREATED: PEX-2026-00003
V3_ENQUEUE_OK job_id: 336b7a56e9ed4a9cbd3c2603e3752549
V3_PERSISTED_LAST_JOB_ID: 336b7a56e9ed4a9cbd3c2603e3752549
V3_JOB_ID_MATCHES: True
```

No `AttributeError`. `pex.reload()` after `frappe.db.commit()` confirms `last_job_id` was
actually persisted to the database (not just held in memory) and matches the id returned by the
function. Synthetic `Passport Extraction`, `FF File Collection`, and `File` records were deleted
after the check (`frappe.delete_doc(..., force=True)` + commit).

## Test-code adjustments (only what the fixes directly invalidated)

1. `test_fileflo_inspection.py::test_enqueues_long_worker_and_records_job_id` — previously
   mocked `frappe.enqueue` to return a `MagicMock` with `.id`, asserted the function's return
   value equaled that mock, and asserted `pex.db_set` was called with the mock's `.id`. Rewritten
   to mock `frappe.enqueue` returning `None` (matching real `enqueue_after_commit=True`
   behavior), and assert the `job_id` keyword argument passed into `frappe.enqueue` is truthy,
   equals the function's return value, and equals what `pex.db_set("last_job_id", ...)` was
   called with.
2. `test_settings.py::TestSettings.test_predicates_default_to_false_when_missing` — previously
   passed only because the loader was permanently broken (always `None`, so all predicates were
   trivially `False` regardless of site state). With D1 fixed, the dedicated test site's enabled
   baseline Single (`enabled=1`, public tracking on) makes the predicates genuinely `True`,
   contradicting the old assertions. Per the dispatch's required policy, this was fixed by
   **establishing a disabled Single inside the test itself** (save `enabled=0`,
   `enable_public_tracking=0`, `enable_passport_extraction=0`, verified all three predicates are
   `False`, then restore the original baseline values via `addCleanup`) — not by weakening the
   assertions. A fallback branch guards the case where the DocType does not exist at all (keeps
   the original None-loader assertion for that scenario, e.g. a future pre-install context).

No other test files were touched.

## New genuine defects surfaced

**None.** One pre-existing gap was investigated and ruled out as in-scope noise, not a new
defect:

`TestSettings` (`test_settings.py`) and `TestLookupService` (`test_lookup_service.py`) are
`FrappeTestCase` subclasses that lack the `if getattr(frappe.local, "db", None) is None: raise
unittest.SkipTest(...)` guard that a prior corrective phase (09e) added to nine sibling
integration classes for exactly this reason. Running the pure/standalone tier
(`python -m unittest discover` against `visa_tracking/tests`, no site bound) hits Frappe's own
`FrappeTestCase.setUpClass` trying to resolve a nonexistent `test_site` config
(`frappe.exceptions.IncorrectSitePath: test_site does not exist`) before reaching either class's
own test bodies, producing 2 errors. **Confirmed statically-verified as pre-existing and
unrelated to D1/D2**: reproduced identically (`errors=2, skipped=10`, same two class names) by
`git stash`-ing this phase's changes and re-running the standalone discovery against the
unmodified baseline commit `4593a845f336763a4afdce2d155bb96471c6b198`, then restoring
(`git stash pop`). Neither D1 nor D2 touches these two classes' setup, and the dispatch scopes
new-defect handling to defects surfaced *by* the D1/D2 fixes — this one predates them and is
out of scope to fix here. Reported for visibility, not fixed, not papered over.

## Verification summary

| Check | Result | Evidence label |
|---|---|---|
| V1 `bench --site visa-tracker-test.localhost migrate` | rc=0 | runtime-verified |
| V2 D1 fixed at runtime (settings + `run_fileflo_inspection`) | confirmed, see above | runtime-verified |
| V3 D2 fixed at runtime (`enqueue_passport_extraction`) | confirmed, see above | runtime-verified |
| V4 run 1 `run-tests --app the_visaguy --skip-test-records` | 248 ran / 221 pass / 27 skipped / 0 errors | runtime-verified |
| V4 run 2 (same command, back-to-back) | 248 ran / 221 pass / 27 skipped / 0 errors — identical | runtime-verified |
| V5 `run-tests --app fileflo` | 6/6 | runtime-verified |
| V6 pure standalone tier (`visa_tracking/tests`, no site, bench venv python) | 199 ran / errors=2 (pre-existing, see above) / skipped=10 / 187 pass — identical to baseline | runtime-verified |
| V7 two-run pollution check | run1 == run2 exactly | runtime-verified |
| No conflict markers in diff | confirmed via grep | runtime-verified |
| No secrets/PII in diff | confirmed (synthetic data only, reviewed full diff) | runtime-verified |

All hard gates satisfied. Working tree clean after commit; no push; no remotes touched;
`fileflo`/`passport_extractor` source, site `visaguy`, and `processflo` untouched.

## Files changed

- `the_visaguy/visa_tracking/utils/settings.py` (D1)
- `the_visaguy/visa_tracking/services/extraction_orchestrator.py` (D2)
- `the_visaguy/visa_tracking/services/fileflo_inspection_service.py` (D2 call site)
- `the_visaguy/visa_tracking/tests/test_fileflo_inspection.py` (test invalidated by D2)
- `the_visaguy/visa_tracking/tests/test_settings.py` (test invalidated by D1)

(All paths under `/home/shahzad/visa-tracker-worktrees/the_visaguy/`, remote host, over SSH —
not present in this local workspace checkout.)
