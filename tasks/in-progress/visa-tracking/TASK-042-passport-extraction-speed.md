---
id: TASK-042
feature: FEAT-001
title: Make passport extraction faster without changing its results
status: in-progress
repository: passport_extractor
app_path: /home/shahzad/bench/apps/passport_extractor
owners: []
depends_on:
  - TASK-003
created: 2026-10-06
updated: 2026-10-19
---

# TASK-042: Make passport extraction faster without changing its results

## Objective

Owner (2026-10-06, pilot on the live site): average extraction time is about
8 minutes. Cut it sharply **without changing any extraction result** on the
pilot files. A separate worker queue is out of scope (owner).

## Evidence (test bench, 6 CPUs, `main` `b8f41d8`)

| File | Size | Per OCR pass | Passes | First pass with a valid MRZ |
|---|---|---|---|---|
| WhatsApp JPEG | 1064×1280 | 16–23 s | 8 (≈157 s) | 1st (0°, enhanced) |
| PDF scan | 4856×3534 (200 DPI) | 45–58 s | 8 (≈405 s) | 2nd (0°, raw) |

Engine load ≈ 10 s once per worker process (singleton; fine).

Causes:
1. `_process_image` runs PaddleOCR on all 8 variants (4 rotations × enhanced/raw)
   of every image; the early stop exists only between PDF pages.
2. Large inputs (PDF pages at 200 DPI ≈ 17 MP; large phone photos).
3. Each pass saves the variant to a temporary PNG and PaddleOCR reads it back.
4. `use_textline_orientation=True` runs a per-line orientation model although
   the pipeline already tries all rotations.

## Required behaviour

### 1. One pure entry point

Factor the pipeline into `analyse_file(file_path, options=None) -> dict`
(no Frappe document access). It returns: `status` (Extracted / Needs Review /
Failed), `error_code`, `confidence`, the parsed fields, `mrz_valid`,
`passes` (OCR passes run), `seconds`, and the chosen variant (page, angle,
enhanced/raw, scale). `_run_extraction` uses it and keeps writing the same
document fields and statuses as today.

`options` (a small dataclass) switches each optimisation, so the benchmark
can reproduce the old behaviour exactly:

- `early_exit` (default True)
- `angle_order` (default `(0, 180, 90, 270)`; legacy `(0, 90, 180, 270)`)
- `max_side` (default 2400; `None` = no cap) with full-resolution fallback
- `in_memory` (default True: pass a numpy array, no temp file)
- `textline_orientation` (default from site config
  `passport_extractor_textline_orientation`, else True — the owner decides
  after the benchmark)
- `cpu_threads` (default from site config `passport_extractor_cpu_threads`,
  else PaddleOCR's default)

`LEGACY_OPTIONS` must reproduce today's algorithm: all 8 variants, legacy
angle order, no cap, temp-file input, textline orientation on, same
selection rule (first candidate with a valid MRZ and confidence ≥ the
threshold, else the highest-confidence candidate).

### 2. Early exit

Inside an image, stop at the first variant whose MRZ is valid with confidence
≥ `CONFIDENCE_OK_THRESHOLD`. Variant order per angle stays enhanced, then raw.

### 3. Resolution cap with fallback

Downscale the image so its longest side ≤ `max_side` before preprocessing.
If no variant at the capped size gives a valid MRZ, run the same search once
at full resolution before giving up. Record which scale won.

### 4. In-memory input

Pass a numpy array to `engine.predict` (PaddleOCR 3.x accepts it). Check the
array layout PaddleOCR expects (BGR vs RGB) in its source on the bench and
match what reading the PNG produced, so results do not change.

### 5. Engine settings

The singleton engine is built from the options in effect for the process
(textline orientation, cpu_threads). Do not change detection thresholds or
models.

### 6. Benchmark command

`passport_extractor.passport_extractor.benchmark.run(directory, mode="new"|"legacy", limit=None)`,
callable with `bench --site <site> execute`. For each supported file in the
directory (sorted by name) print one line: index, extension, image size,
status, error_code, confidence, mrz_valid, passes, seconds, chosen variant,
and a **fingerprint**: the first 10 hex chars of SHA-256 over
`passport_number_normalized|date_of_birth` (never the values). Write the same
rows as JSON lines to a path given by the caller. No database writes.

## Constraints

- No change to statuses, error codes, field mapping, check-digit rules or
  the review/verify flow.
- No passport values in logs, output or tests (synthetic values only).
- Keep the extractor independent of `the_visaguy` (ADR-003).

## Validation

- Pure tests: early exit stops at the first valid variant; legacy options run
  all 8; the cap downsizes and falls back to full resolution; angle order;
  in-memory path; `LEGACY_OPTIONS` matches the old selection rule; benchmark
  prints no values.
- On the bench (orchestrator), over the 36 pilot passports: run `legacy`
  and `new`. Pass condition: every file whose legacy status is Extracted or
  Verified-eligible has the **same status and the same fingerprint** in
  `new`; no file gets worse; report the time per file and the average.
  Then a second `new` run with textline orientation off, reported separately
  for the owner's decision.

## Results (2026-10-19)

Benchmark on `visa-tracker-test.localhost`, 36 pilot passports plus one
`.txt` (skipped). Status, error code and number/birth-date fingerprint are
identical to `legacy` for all 37 files in both new modes.

| Mode | Average | Median | Max | OCR passes |
|---|---|---|---|---|
| legacy | 126.7 s | 104.7 s | 363.9 s | 288 |
| new | 77.6 s | 38.7 s | 557.4 s | 135 |
| new, textline orientation off | 46.1 s | 25.4 s | 314.2 s | 138 |

Files with no MRZ take longer in `new` (the full-resolution fallback adds
passes). Textline orientation off is an owner decision (site config
`passport_extractor_textline_orientation: 0`); it did not change any result.

Shipped in tridz-dev/passport_extractor#5 together with TASK-043 and
TASK-044 (https://github.com/tridz-dev/passport_extractor/pull/5).

