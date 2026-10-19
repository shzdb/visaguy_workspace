# TASK-042 part 6: benchmark command

## Summary
Added `passport_extractor.passport_extractor.benchmark.run(directory, mode="new", limit=None, output=None, textline_orientation=None)`. It imports `ExtractionOptions`, `LEGACY_OPTIONS` and `analyse_file` lazily from `services.extraction_service` (added by the other agent). No DB writes, no frappe import at module level.

## Commits
- 3a7d18f feat(TASK-042): add value-free extraction benchmark command (branch sl/task-042b, pushed to bench; no AI trailer)

## Files changed
- passport_extractor/passport_extractor/benchmark.py (new)
- passport_extractor/passport_extractor/tests/test_benchmark.py (new, 12 tests)

## Design notes and deviations
- Output per file: index, ext, image_size, status, error_code, confidence, mrz_valid, passes, seconds, variant, fingerprint. File names, values, names and dates are never printed or written. A one-time `index->ext` map is printed.
- Fingerprint: first 10 hex of sha256("passport_number_normalized|date_of_birth"), else "-".
- Extension check reproduces only the app's extension rule. Supported: pdf, jpg, jpeg, png. Reconciling "list skipped files" with "HEIC must fail": image types the app rejects (heic, heif, webp, gif, bmp, tif, tiff) become Failed / UNSUPPORTED_FILE_TYPE / passes 0 without calling analyse_file; all other extensions become status "Skipped". Both count in `files`. This split list is my choice; adjust REJECTED_EXTENSIONS if needed.
- `limit` applies to supported+rejected files, not Skipped ones (Skipped are still listed). Skipped rows are excluded from the seconds statistics.
- Exceptions: row status "Error", error_code = exception class name only; message never printed.
- `textline_orientation` accepts 0/1/true/false/bool; it overrides the default `ExtractionOptions()` only in "new" mode (mutates the fresh instance, so the field must be non-frozen; if the other agent makes the dataclass frozen, switch to `dataclasses.replace`).
- `limit` accepts strings (bench execute). Output JSONL is flushed per row, so a long run can be tailed.
- `run` also returns the totals dict (bench execute prints it).

## Tests added (pure, analyse_file mocked via sys.modules)
TestFingerprint: stable_and_hides_values, missing_value_gives_dash. TestParsing: parse_bool. TestRun: legacy_uses_legacy_options, new_uses_defaults_and_textline_override, bad_mode, heic_is_unsupported_without_analysis, other_extensions_are_skipped_and_counted, sorted_and_limit, output_json_lines_and_totals, exception_becomes_error_row_with_class_name_only, no_names_or_values_in_output.

Pure tier on bench worktree task-042b-passport_extractor: baseline (b8f41d8) "Ran 30 tests ... OK"; after: "Ran 42 tests in 0.068s ... OK". py_compile OK.

## On-site checks still to run (orchestrator)
- After merging with the other agent's branch (so `analyse_file`/`LEGACY_OPTIONS` exist), run `bench --site visa-tracker-test.localhost execute passport_extractor.passport_extractor.benchmark.run --kwargs "{'directory': '/home/shahzad/bench/passport', 'mode': 'legacy', 'output': '/tmp/legacy.jsonl'}"`, then `mode: 'new'`, then `mode: 'new', 'textline_orientation': '0'`.
- Compare status and fingerprint per index between legacy and new; report average seconds.
- Confirm the real `analyse_file` result keys (status, error_code, confidence, mrz_valid, fields, passes, seconds, variant, image_size) match the fixed interface; the benchmark reads them with `.get`.

## Needs from another task
- `ExtractionOptions` must allow attribute assignment (not frozen), or tell me to use `dataclasses.replace`.

## Open questions
- Whether the benchmark should live-print `image_size` as [w, h] (printed as given).
