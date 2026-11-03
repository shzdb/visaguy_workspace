---
id: TASK-051
feature: FEAT-005
title: Branded PDF download of the check result
status: completed
repository: visa_refusal_checker
owners: []
depends_on:
  - TASK-029
expected_files:
  - src/components/refusal-checker/report-pdf.ts
  - src/components/refusal-checker/result-screen.tsx
  - package.json
created: 2026-11-03
updated: 2026-11-03
---

# TASK-051: Branded PDF download of the check result

Tasklane: TASK-2026-01847.

## Objective

Applicants can keep and share their refusal risk report as a Visaguy-branded
PDF.

## Required behaviour

- A Download PDF button saves `visaguy-refusal-risk-report.pdf`.
- The PDF has the logo, applicant name, date, score and band, serious-issue
  flags, per-ground scores, what to fix, the timeline note, and the
  not-immigration-advice disclaimer on every page.
- Text is selectable. The button sits under the report title on phones and in
  the sidebar from `lg`.

## Constraints

- Built in the browser; nothing is sent anywhere. The library loads on click.
- Output stays qualitative: a risk score, never a probability.

## Decisions

- Library: jsPDF 4.2.1, standard Helvetica. It loads as a separate chunk
  (132 kB gzip) and the main bundle grows by about 1 kB. `@react-pdf/renderer`
  was not adopted because of its size.
- The SVG logo is drawn to a canvas and embedded as a JPEG on white, which
  keeps the file near 31 kB (a transparent PNG added over 600 kB).

## Validation

- A high-risk (2 pages) and a low-risk (1 page) report were rendered and
  inspected page by page; wrapping, page breaks, the em dash and the footer
  were fixed from those renders.
- The browser built the file with the right name and logo, and jsPDF's
  optional HTML and SVG helpers were not loaded.
- `tsc -b`, `vite build` and `eslint` pass.

## Definition of done

- Fix in the application repository, deployed, and the download checked on
  iOS Safari, desktop Safari and Chrome.

## Completion evidence

`visa_refusal_checker`, local commit on `main`, 2026-11-03: `3edbd51`. Not
pushed or deployed.

## Deviations and limitations

- Marked completed at the owner's request on 2026-11-03, before push, deploy and the device checks below.

- The download itself was not tried on iOS Safari or desktop Safari, and the
  logo was checked as an image, not inside a rendered page.
- The PDF carries the applicant's name but not the mobile number.
