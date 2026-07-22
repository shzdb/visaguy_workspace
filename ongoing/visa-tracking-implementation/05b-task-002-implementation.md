# TASK-002 Implementation Report — Passport Extractor Scaffold and DocType

**Date:** 2026-07-21  
**Feature worktree:** `/home/shahzad/visa-tracker-worktrees/passport_extractor`  
**Branch:** `feat/visa-tracker`  
**Base SHA:** `07b8cab40cd4054b39a78f23a271d7201e71baa0`  
**Implementation commit SHA:** `6746d049db93c86d3cce8f35f763aac6b9366192`  
**Corrective audit commit SHA:** `2f25c0d52d2bb898c217b61f448705e5eda550c7`  
**TASK-002 verdict:** `runtime-blocked`

---

## Summary

Implemented the complete `Passport Extraction` DocType schema, controller, role, generic utilities, and automated tests for the `passport_extractor` app in the dedicated feature worktree. All changes were delivered via the mandatory patch-only method and committed locally. No edits occurred outside the feature worktree, no migration or tests ran on `visaguy`, no asset build ran, and no push was performed.

The dedicated test site `passport-extractor-test.localhost` could not be created because `root_password` is **not configured** in `/home/shahzad/bench/sites/common_site_config.json`. Per the task stop conditions, runtime verification (site creation, migration, and test execution) is therefore blocked. The implementation is statically validated and ready to run as soon as a safe, isolated test site is available.

An orchestrator review of the executor's implementation found and corrected four invariant gaps: request audit fields are now server-owned and immutable, retry counts cannot be changed outside `Failed -> Queued`, duplicate/supersession self-references are rejected, and hashing resolves bytes through the validated Frappe `File.get_full_path()` API. Focused tests were added for these cases. The corrective commit used the remote environment's existing Git identity; no author configuration or override was supplied.

---

## Changed files

| File | Purpose |
|------|---------|
| `passport_extractor/passport_extractor/doctype/passport_extraction/__init__.py` | DocType package marker (empty) |
| `passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.json` | DocType schema with 47 accepted data fields, exact status options, role permissions, and permlevel-1 raw/MRZ/error fields |
| `passport_extractor/passport_extractor/doctype/passport_extraction/passport_extraction.py` | Document controller enforcing transitions, timestamps, retry bounds, verification audit, duplicate/supersession checks, and private-file validation seams |
| `passport_extractor/passport_extractor/doctype/passport_extraction/test_passport_extraction.py` | `unittest.TestCase` unit tests plus `FrappeTestCase` integration tests using only synthetic fixtures |
| `passport_extractor/passport_extractor/role/passport_extractor_user/passport_extractor_user.json` | App-owned internal role `Passport Extractor User` |
| `passport_extractor/passport_extractor/utils.py` | Generic helpers: normalization, transition graph, private-File validation, chunked SHA-256 hashing |

No scaffold files (`pyproject.toml`, `README.md`, `license.txt`, top-level `__init__.py`, or `hooks.py`) were modified.

---

## Static validation gates

All static checks passed before commit.

| Gate | Result | Evidence label |
|------|--------|----------------|
| `git diff --check` | Pass (no whitespace errors) | source-wired |
| JSON parse — `passport_extraction.json` | Pass | present |
| 47 accepted data-field count | Pass (47 fields, excluding 5 section-break layout fields) | present |
| Status options exact | Pass (`Queued`, `Processing`, `Extracted`, `Needs Review`, `Verified`, `Rejected`, `Failed`, `Duplicate`, `Superseded`) | present |
| Permlevel-1 raw/MRZ/error fields | Pass (`raw_ocr_text`, `raw_extraction_result`, `mrz_line_1`, `mrz_line_2`, `error_message`) | present |
| `Passport Extractor User` permissions present, no Guest rule | Pass | present |
| Python compile — all changed `.py` files | Pass (bench Python environment) | source-wired |
| Module resolution with worktree-first `PYTHONPATH` | Pass (`passport_extractor.__file__` resolves inside feature worktree) | source-wired |
| Import checks with worktree-first `PYTHONPATH` | Pass for `utils`, controller, and test module (bench Python environment) | source-wired |
| Forbidden dependency scan | Pass — no references to `the_visaguy`, `fileflo`, `processflo`, `Lead`, `Customer`, `Visa Tracking Application`, `PF Process File`, or `FF File Collection` | source-wired |
| PII/permission/state-transition review | Pass — no PII, no public-file byte access before privacy check, no direct DB writes bypassing validation, no raw SQL | source-wired |
| Request/retry/audit invariant review | Pass — request provenance is server-owned, retry changes are transition-bound, verification provenance is immutable after verification, and duplicate/supersession self-links are rejected | source-wired |
| `ruff` | Not available on the bench; no tools installed | configured-unverified |

### Field-count detail

The DocType contains exactly 47 accepted data fields:

- Source and provenance: `passport_file`, `file_hash`, `source_doctype`, `source_document`, `source_field_id`, `source_row`, `triggered_by`, `requested_by`, `requested_on` (9)
- Processing: `status`, `processing_started_on`, `processing_completed_on`, `extraction_engine`, `engine_version`, `confidence`, `requires_review`, `retry_count`, `last_job_id`, `error_code`, `error_message` (11)
- Passport values: `passport_number`, `passport_number_normalized`, `date_of_birth`, `expiry_date`, `surname`, `given_names`, `nationality`, `issuing_country`, `sex`, `document_type`, `personal_number` (11)
- MRZ evidence: `mrz_line_1`, `mrz_line_2`, `passport_number_check_valid`, `date_of_birth_check_valid`, `expiry_date_check_valid`, `personal_number_check_valid`, `composite_check_valid`, `mrz_valid` (8)
- Raw/audit: `raw_ocr_text`, `raw_extraction_result`, `verified_by`, `verified_on`, `verification_notes`, `duplicate_of`, `supersedes`, `superseded_by` (8)

Total: **47**.

---

## Runtime validation gates

| Gate | Result | Evidence label |
|------|--------|----------------|
| Dedicated test site exists | `passport-extractor-test.localhost` does **not** exist | runtime-verified |
| `root_password` configured in `common_site_config.json` | **No** — the key is absent | configured-unverified |
| Test-site creation | Blocked by missing `root_password` | — |
| `bench --site passport-extractor-test.localhost migrate` | Not run (site cannot be created) | — |
| `bench --site passport-extractor-test.localhost run-tests --app passport_extractor` | Not run (site cannot be created) | — |
| `visaguy` still lists `passport_extractor` | Pass (scaffold version 0.0.1 shown in `list-apps`) | runtime-verified |
| Migration/tests on `visaguy` | Not performed (explicitly excluded) | — |

### Exact blocker

Dedicated-site runtime verification is blocked because the bench's `common_site_config.json` does **not** contain a `root_password` key. Without it, `bench new-site passport-extractor-test.localhost` cannot create the isolated test database, and therefore migration and the full app test suite cannot be executed. No password value was requested, printed, copied, or exposed.

---

## Implementation notes

- **Naming:** `autoname` is set to `PEX-.YYYY.-.#####` with `naming_rule: Expression`, avoiding an extra `naming_series` data field.
- **Transitions:** Enforced in `validate()` using `self.get_doc_before_save()`; invalid transitions raise `frappe.ValidationError`. Terminal OCR states (`Extracted`, `Needs Review`, `Failed`) set `processing_completed_on`; `Processing` sets `processing_started_on`.
- **Request audit:** `requested_by`, `requested_on`, and the initial retry count are overwritten by the server on insert; request provenance is immutable afterward.
- **Retries:** `retry_count` cannot be negative or changed outside `Failed -> Queued`; that transition deterministically increments it and rejects values above `MAX_RETRY_COUNT` (3).
- **Verification audit:** `verified_by` and `verified_on` are auto-populated on entry to `Verified` and cannot be altered once the record is Verified or Superseded.
- **Supersession:** `superseded_by` is required, cannot reference the same record, and its target must be `Verified` or `Superseded`.
- **Duplicates:** `duplicate_of` is required, must exist, and cannot reference the same record.
- **File seams:** `validate_passport_file()` confirms the File exists and `is_private == 1` before any byte access. `compute_file_hash()` resolves the validated File through `get_full_path()` and hashes in 8 KB chunks.
- **Permissions:** `Passport Extractor User` has level-0 create/read/write/delete plus level-1 read/write. `System Manager` retains full access. `Guest` has no rule.
- **Tests:** Synthetic values only; no real passport data or committed samples. `UnitTestCase` tests exercise helpers without a site; `FrappeTestCase` integration tests exercise DocType behavior on the dedicated test site once available.

---

## Verdict

**TASK-002 is `runtime-blocked`**, not complete. Static implementation, corrective review, and validation are finished and committed locally. Runtime verification (dedicated test-site migration and tests) is blocked solely by the missing `root_password` configuration, which prevents safe test-site creation. No credentials were requested or exposed. The worktree is clean on `feat/visa-tracker` at commit `2f25c0d52d2bb898c217b61f448705e5eda550c7`.
