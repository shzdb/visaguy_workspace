# TASK-042 pipeline (sections 1-5) - log

## Summary
`analyse_file(file_path, options)` is the new pure entry point in `services/extraction_service.py`, with `ExtractionOptions` and `LEGACY_OPTIONS` exactly as in the fixed interface. `_run_extraction` now calls it with default options and writes the same fields, statuses, error codes and messages as before. Early exit, the 2400 px cap with full-resolution fallback, in-memory numpy input, and per-settings engine caching are implemented. The benchmark (section 6) is not part of this branch.

Branch `sl/task-042` (base main b8f41d8), pushed to remote `bench`.

## Commits
- 99cfbab perf(TASK-042): add analyse_file with early exit, resolution cap, in-memory input and engine settings
- ef2078a test(TASK-042): fix pipeline test expectations
(head ef2078a; no Co-Authored-By, verified with `git log -1 --format=%B`)

## Files
- passport_extractor/passport_extractor/services/extraction_service.py (options, analyse_file, search helpers, slimmer _run_extraction)
- passport_extractor/passport_extractor/ocr/image_preprocessor.py (lazy `iter_variants`, `cap_image`; `preprocess_image` kept, same output order)
- passport_extractor/passport_extractor/ocr/paddle_ocr_engine.py (engine cache per settings, `run_ocr(image, in_memory, textline_orientation, cpu_threads)`)
- passport_extractor/passport_extractor/tests/test_extraction_pipeline.py (new)

## Design notes
- Verified PaddleOCR 3.7.0 source on the bench (read-only):
  - CPU threads: constructor keyword `cpu_threads` (a common argument handled in `paddleocr/_common_args.py`, default `DEFAULT_CPU_THREADS = 10`). It is passed only when set, so None keeps the PaddleOCR default.
  - Textline orientation: `use_textline_orientation` (unchanged).
  - numpy input: `predict` accepts `np.ndarray` (paddlex `ImageBatchSampler.sample`). `ReadImage(format="BGR")` returns arrays unchanged, and the file path route uses `cv2.imdecode(IMREAD_COLOR)`, which is BGR. So the in-memory path converts PIL RGB to a contiguous HxWx3 uint8 BGR array. The variants are grayscale expanded to RGB, so the values equal what a PNG round trip gives.
- Engine cache: `_engines` dict keyed by `(textline_orientation, cpu_threads)`; thresholds and models unchanged. Each distinct settings tuple holds its own engine in memory (only matters for the benchmark switching settings in one process).
- Options resolution: `None` for textline_orientation / cpu_threads is resolved inside `analyse_file` from `frappe.conf` keys `passport_extractor_textline_orientation` (default True) and `passport_extractor_cpu_threads` (default unset). If no site is active, config reads give None.
- Selection rule is unchanged: first candidate (in variant order, then candidate order) with a valid MRZ and confidence >= 75 wins, else highest confidence overall. Early exit stops at that same candidate, so it picks the same one as the full search for the same OCR output.
- Fallback trigger: the full-resolution search runs when the capped search found no *accepted* candidate (valid MRZ and confidence >= threshold), and only if the page was actually downscaled. The contract says "no valid MRZ"; I used the stricter accepted test so a low-confidence valid read at the capped size is not preferred over a better full-resolution read. Entries from both scales compete in the final highest-confidence fallback.
- The cap uses PIL LANCZOS on the RGB image before preprocessing. Variant `scale` is the cap factor rounded to 4 places (1.0 if not capped or if the fallback won). `page` is 1-based.
- Preprocessing is now a generator, so rotations are only computed when reached. Deviation: if OpenCV fails midway through the rotations (not during setup) there is no PIL fallback for the already yielded variants. Setup failures still fall back as before.
- `analyse_file` extra keys beyond the fixed interface: `raw_ocr_lines`, `mrz_line_1`, `mrz_line_2`, `raw_extraction_result`. `_run_extraction` needs them to keep writing `raw_ocr_text` and `raw_extraction_result`.
- Error behaviour kept: empty file read gives FILE_READ_ERROR; OCR exception gives OCR_ENGINE_ERROR with no raw text written; no candidates gives NO_MRZ_FOUND with raw text written. Exceptions from opening the file or rendering a PDF still propagate (as before), so `run_ocr_pipeline` marks them OCR_ENGINE_ERROR with the generic message. The "Required passport fields are missing." message for NO_MRZ_FOUND under Needs Review is preserved.
- `run_ocr` keeps working with a bare `run_ocr(image)` call (defaults: in-memory, orientation on).
- File extension for PDF detection now comes from `file_path` instead of `file_doc.file_name`.

## Tests
Added `tests/test_extraction_pipeline.py` (33 tests): early exit at first valid variant, no-MRZ runs 8, LEGACY runs all 8, angle order (new and legacy, canvas expansion), cap downsizes, fallback to full resolution once, no fallback when not downscaled, `max_side=None`, options reach the runner, BGR array layout, array vs path in `run_ocr`, engine cache and constructor kwargs, option resolution from config, selection rule (first accepted vs first valid, highest-confidence fallback, check-digit failure), result shape, OCR exception, `_run_extraction` wiring for Extracted / Needs Review / Failed paths. The "benchmark prints no values" test belongs to the benchmark agent.

Baseline on bench worktree (main b8f41d8): `Ran 30 tests ... OK`.
After change (ef2078a): `Ran 63 tests in 1.519s ... OK`.
Ran: py_compile on all touched files OK; pure tests as above via flock on `/home/shahzad/sl-worktrees/task-042-passport_extractor`.

## Not run (need a site / the pilot files)
- Site tests in `doctype/passport_extraction/test_passport_extraction.py` (end-to-end `run_ocr_pipeline` with real PaddleOCR).
- Pilot comparison legacy vs new over the 36 passports (same status and fingerprint), timing, and the textline-orientation-off run.
- Confirming `cpu_threads` takes effect on the 6-CPU bench.

## Open questions
- Should the fallback trigger on "no valid MRZ at all" (the contract wording) instead of "no accepted candidate"? Current choice is the safer one but costs more time on files whose capped read is valid but low-confidence.
- The two commits could be squashed before merge.
