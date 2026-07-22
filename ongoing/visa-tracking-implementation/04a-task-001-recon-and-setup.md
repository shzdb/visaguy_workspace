# TASK-001 Reconnaissance and Setup Evidence Log

> Generated: 2026-07-21
> Feature: FEAT-001 — Visa application tracking and passport extraction
> Task: TASK-001 — Preflight and branch setup

## Scope

This log records the verified source/runtime baseline and safe branch/worktree layout produced during TASK-001. It contains no application code, secrets, PII, raw diffs, passport samples, or production records.

---

## 1. Remote bench baseline (T1)

- **Bench root**: `/home/shahzad/bench`
- **Site**: `visaguy`
- **Bench layout confirmed**: `apps/`, `sites/`, `Procfile` present.
- **Installed apps on `visaguy`** (source-wired, `bench --site visaguy list-apps`):
  - `frappe` 15.113.0 on `version-15`
  - `erpnext` 15.106.0 on `version-15`
  - `hrms` 15.45.2 on `version-15`
  - `india_compliance` 15.18.0 on `version-15`
  - `payments` 0.0.1 on `version-15`
  - `helpdesk` 0.10.0 on `modification_develop_branch`
  - `crm` 2.0.0-dev on `tridz-dev`
  - `fileflo` 0.0.1 on `fix/mandatory-file`
  - `processflo` 0.0.1 on `develop`
  - `the_visaguy` 0.0.1 on `main`
  - `visaguy_crm` 0.0.1 on `develop`
  - `visaguy_business` 0.0.1 on `develop`
  - `visaguy_frappe_crm` 0.0.1 on `develop`
  - `visaguy_helpdesk` 0.0.1 on `develop`
  - `visaguy_hrms` 0.0.1 on `main`
  - `visaguy_raven` 0.0.1 on `develop`
  - `visaguy_website` 0.0.1 on `develop`
  - Plus additional installed apps not directly owned by FEAT-001.

---

## 2. Repository metadata (T2)

### 2.1 `the_visaguy`

- **Path**: `/home/shahzad/bench/apps/the_visaguy`
- **HEAD SHA**: `e690b5b1ac897874fb33439fa429e2aee103cc3e`
- **Checked-out branch**: `main`
- **Working tree**: clean (`git status --short` empty)
- **Local branches**: `develop`, `feat/timer`, `main`
- **Remotes** (credentials redacted):
  - `origin` → `github.com:tvgglobal/the_visaguy.git`
  - `upstream` → `tridz:tvgglobal/the_visaguy.git`
- **Default branch inference**: `develop` is an ancestor of `main`; `main` is 5 commits ahead of `develop` and matches `upstream/main` exactly. `main` is therefore the unambiguous production/default base for FEAT-001.

### 2.2 `fileflo`

- **Path**: `/home/shahzad/bench/apps/fileflo`
- **HEAD SHA**: `6683010e89d9209363e6ba3881f4a90a47420bd2`
- **Checked-out branch**: `fix/mandatory-file`
- **Working tree**: clean (`git status --short` empty)
- **Local branches**: `develop`, `feat/fileo-updates`, `fix/mandatory-file`, `main`
- **Remote HEAD**: `upstream/HEAD -> upstream/develop`
- **Remotes** (credentials redacted):
  - `upstream` → `tridz:tridz-dev/FileFlo.git`
- **Branch relationships**:
  - `fix/mandatory-file` is **not** an ancestor of `develop`.
  - `develop` is **not** an ancestor of `fix/mandatory-file`.
  - `fix/mandatory-file` is `9 behind, 19 ahead` of `develop`.
  - `fix/mandatory-file` is `1 ahead, 0 behind` `main`.
- **Default branch inference**: `upstream/HEAD` points to `develop`, but `develop` is 19 commits behind the deployed `fix/mandatory-file` branch and `fix/mandatory-file` is one commit ahead of `main`. The intended base for `feat/visa-tracker` is therefore **ambiguous**.
- **Stop condition applied**: `feat/visa-tracker` worktree **not created** for `fileflo`. A workspace decision is required before branching.

### 2.3 `processflo`

- **Path**: `/home/shahzad/bench/apps/processflo`
- **HEAD SHA**: `2f2b5657d20a778159dce0b2268c2a676ad66627`
- **Checked-out branch**: `develop`
- **Working tree**: dirty — `M processflo/generate_file_collection.py`
- **Local branches**: `develop`
- **Remote HEAD**: `upstream/HEAD -> upstream/develop`
- **Remotes** (credentials redacted):
  - `upstream` → `tridz:tridz-dev/ProcessFlo.git`
- **Action**: inspected only; no branch, edit, stash, commit, reset, or clean performed.
- **Conflict assessment**: the dirty change is in `generate_file_collection.py`, which is unrelated to the planned `custom_visa_tracking_application` / `custom_client_status` custom fields supplied by `the_visaguy`.

---

## 3. Integration evidence (T3)

### 3.1 FileFlo persisted record and field-ID property

- **Parent submission DocType**: `FF File Collection`
  - Controller: `fileflo/fileflo/doctype/ff_file_collection/ff_file_collection.py`
  - Key fields:
    - `reference_type` (Link / DocType)
    - `reference_name` (Dynamic Link against `reference_type`)
    - `file_collection_file` (Table → `FF File Collection File`)
    - `information` (Table → `FF File Collection Data`)
- **File row child table**: `FF File Collection File`
  - Schema: `fileflo/fileflo/doctype/ff_file_collection_file/ff_file_collection_file.json`
  - **Stable field-ID property**: `field_id` (fieldtype `Data`, `read_only`: 1)
- **Information/value child table**: `FF File Collection Data`
  - Schema: `fileflo/fileflo/doctype/ff_file_collection_data/ff_file_collection_data.json`
  - **Stable field-ID property**: `field_id` (fieldtype `Data`, `read_only`: 1)
- **File attachment DocType**: `FF Document`
  - Controller: `fileflo/fileflo/doctype/ff_document/ff_document.py`
  - The actual uploaded file is stored via the `attach` field on `FF Document`.
- **Persistence code path**: `fileflo/fileflo/data_collection.py::add_form_data`
  - Saves submitted information values to `FF File Collection Data` rows.
  - Creates `FF Document` records and links them to `FF File Collection File` rows via the `document` field.

### 3.2 File Collection-to-Lead relationship

- **Relationship fields**: `FF File Collection.reference_type` and `FF File Collection.reference_name`.
- **Lead-side creation path**: `visaguy_crm/visaguy_crm/file_collection_from_lead.py::generate_file_collection_lead(lead_name, doctype="Lead")`
  - Iterates `Lead.custom_applicant_information` rows.
  - For each applicant creates/reuses an `FF File Collection` with:
    - `reference_type = doctype` (e.g., `"Lead"`)
    - `reference_name = lead_name`
    - `applicant_name = applicant_details.name1`
    - `custom_type = applicant_details.type`
  - Stores the collection back on the applicant row via `applicant_details.db_set('file_collection', ...)`.
- **Conclusion**: the File Collection-to-Lead join is through `FF File Collection.reference_type = "Lead"` / `"CRM Lead"` and `reference_name = <lead name>`, with the lead/applicant context held in `visaguy_crm`.

### 3.3 Lead-to-PF Process File creation/link path

- **Entry point**: `visaguy_crm/visaguy_crm/allocated_to_process_file.py::create_process_file(lead_name, doctype="Lead")`
- **Flow**:
  1. Loads `Lead` (or `CRM Lead`) and `Destination`.
  2. For each `custom_applicant_information` row of type `Primary`, calls `create_pf_process_file(...)`.
  3. `create_pf_process_file` creates `PF Process File` with:
     - `custom_reference_type = doctype`
     - `custom_reference_name = lead_name`
     - `applicant_name = applicant_details.name1`
     - `process_` = resolved process template
     - `custom_lead_file_collection` = linked `FF File Collection`
  4. Writes `applicant_details.process_file = pf_process_file.name`.
  5. Sets `lead_data.custom_process_file_created = 1`.
- **PF Process File base schema**: `processflo/processflo/doctype/pf_process_file/pf_process_file.json`
  - Existing link: `file_collection` → `FF File Collection`.
  - Existing custom fields (supplied by other apps): `custom_reference_type`, `custom_reference_name`.
- **Conclusion**: the Lead-to-PF Process File path is owned by `visaguy_crm`, not `processflo`, and is discoverable through `PF Process File.custom_reference_type`, `custom_reference_name`, and the applicant row `process_file` field.

### 3.4 ERPNext Lead vs CRM Lead

- **Source evidence**:
  - `the_visaguy/the_visaguy/hooks.py` registers `on_update` handlers for **both** `Lead` and `CRM Lead`:
    - `"Lead": { "on_update": "the_visaguy.handlers.whatsapp_message.send_lead_updates" }`
    - `"CRM Lead": { "on_update": [...send_lead_updates, conversion_event], "after_insert": [conversion_event] }`
  - `visaguy_crm/visaguy_crm/allocated_to_process_file.py::create_process_file(lead_name, doctype="Lead")` explicitly accepts `doctype="Lead"` or `doctype="CRM Lead"`.
  - `visaguy_crm/visaguy_crm/file_collection_from_lead.py::generate_file_collection_lead(lead_name, doctype="Lead")` also accepts both.
  - Both DocTypes carry `custom_applicant_information`, `custom_file_request_link_sent`, and `custom_process_file_created` (fixture evidence in `visaguy_crm` and `visaguy_frappe_crm`).
- **Conclusion**: both ERPNext `Lead` and Frappe CRM `CRM Lead` are **source-wired** in the deployed flow. `the_visaguy` must therefore supply tracking Links on both DocTypes unless a future workspace decision narrows the scope.

---

## 4. PaddleOCR / runtime package availability (T6)

Import checks were executed in the bench Python environment without opening passport files, downloading models, or running OCR.

| Package | Import result | Notes |
|---|---|---|
| `paddle` | OK | version `3.2.0` |
| `paddleocr` | OK | no `__version__` attribute present |
| `cv2` | OK | OpenCV available |
| `numpy` | OK | available |
| `pymupdf` | **FAIL** | `ModuleNotFoundError` |
| `fitz` | **FAIL** | `ModuleNotFoundError` |

- **Evidence label**: `configured-unverified` / import-only. PaddlePaddle 3.2.0 and PaddleOCR import successfully, but OCR runtime, model files, and MRZ pipeline were not exercised. PyMuPDF/fitz are not currently installed and will need to be added for PDF rendering in TASK-003 if the project does not already use an alternative PDF library.

---

## 5. Local frontend scaffold (T7)

- **Node.js version**: `v24.14.0` (satisfies Vite 8 requirement of Node.js 20.19+ or 22.12+).
- **Target directory**: `/home/shzd/Projects/tridz/visa_tracker` — was absent at start; scaffold created.
- **Scaffold command**: `npm create vite@latest visa_tracker -- --template react-ts`
- **Additional dependencies installed**:
  - `tailwindcss`, `@tailwindcss/vite`
  - `react-router-dom`
  - `axios`
  - `react-hook-form`
  - `@hookform/resolvers`
  - `zod`
- **Configuration**:
  - `vite.config.ts`: `@vitejs/plugin-react`, `@tailwindcss/vite`, `@/` alias → `./src`.
  - `tsconfig.app.json`: `baseUrl` + `paths: { "@/*": ["./src/*"] }`.
  - `src/index.css`: Tailwind CSS v4 import and shadcn/ui theme variables.
- **shadcn/ui**: initialized non-interactively with `npx shadcn@latest init -t vite -b base -p nova --yes`.
  - Initial component added: `src/components/ui/button.tsx`.
  - Utility added: `src/lib/utils.ts`.
- **Validation**:
  - `npm run lint` → passes (one `only-export-components` warning in generated `button.tsx`).
  - `npm run build` → passes.
- **Git**: initialized, no remote added, one scaffold commit:
  - Commit: `20b8c45`
  - Message: `scaffold: Vite 8 + React 19 + TypeScript + Tailwind CSS v4 + shadcn/ui base-nova`
  - `git status --short` is clean after the commit.

---

## 6. Remote worktrees (T4 / T5)

### 6.1 `the_visaguy`

- **Action**: created local-only branch `feat/visa-tracker` from `main` and added worktree.
- **Commands**:
  - `git branch feat/visa-tracker main`
  - `git worktree add /home/shahzad/visa-tracker-worktrees/the_visaguy feat/visa-tracker`
- **Worktree path**: `/home/shahzad/visa-tracker-worktrees/the_visaguy`
- **State**: clean, on `feat/visa-tracker`, HEAD at `e690b5b`.
- **Original checkout**: `/home/shahzad/bench/apps/the_visaguy` remains on `main`, unchanged.

### 6.2 `fileflo`

- **Action**: **skipped**.
- **Reason**: the intended base branch is ambiguous.
  - `upstream/HEAD` declares `develop` as default.
  - The deployed bench branch is `fix/mandatory-file`, which is 19 commits ahead of `develop` and 1 commit ahead of `main`.
  - Creating `feat/visa-tracker` from `develop` would miss deployed code; creating it from `fix/mandatory-file` would branch off a non-default feature branch.
- **Required next step**: workspace decision on whether the FEAT-001 base for `fileflo` is `develop`, `main`, or `fix/mandatory-file`.

### 6.3 `processflo`

- **Action**: inspected only; no branch, edit, stash, commit, reset, or clean.
- **Reason**: ADR-003 designates `processflo` as an integration target with no planned source changes. Its working tree is dirty with unrelated changes.

---

## 7. Passport extractor metadata (T8)

`passport_extractor` was **not scaffolded** because the Frappe `bench new-app` metadata has not been provided.

The following fields are required by the Frappe new-app workflow:

| Field | Status | Proposed value (derived from existing maintained-app metadata in `the_visaguy`) |
|---|---|---|
| `app_name` | missing | `passport_extractor` |
| `app_title` | missing | `Passport Extractor` |
| `app_publisher` | missing | `Shahzad Bin Shahjahan` |
| `app_email` | missing | `shahzad@tridz.com` |
| `app_license` | missing | `mit` |
| `app_description` | missing | `Reusable passport extraction and MRZ validation for Frappe` |

These proposals are derived directly from `the_visaguy/the_visaguy/hooks.py` metadata, which is an internally maintained app in this workspace. They are not final; the project owner must confirm or override them before `bench new-app` is executed in TASK-002.

---

## 8. Validation summary

### 8.1 Completed

- [x] Bench layout and installed apps recorded.
- [x] `the_visaguy`, `fileflo`, and `processflo` repository paths, HEAD SHAs, branches, remotes, and dirty states recorded.
- [x] Exact FileFlo persisted record (`FF File Collection`) and stable field-ID property (`field_id`) documented with source paths.
- [x] Exact File Collection-to-Lead relationship path documented (`reference_type`/`reference_name`, created via `visaguy_crm.file_collection_from_lead`).
- [x] Exact Lead-to-PF Process File creation/link path documented (`visaguy_crm.allocated_to_process_file.create_process_file`).
- [x] Both ERPNext `Lead` and `CRM Lead` confirmed source-wired in deployed flow.
- [x] `the_visaguy` `feat/visa-tracker` branch and dedicated worktree created safely; original checkout untouched.
- [x] `processflo` inspected only; no mutation.
- [x] PaddlePaddle/PaddleOCR import availability recorded (import-only, no OCR runtime).
- [x] Local `visa_tracker` scaffold created, lint/build pass, one Git commit, clean status, no remote.
- [x] Missing `passport_extractor` new-app metadata identified and proposed values recorded.

### 8.2 Skipped / Blocked

- [ ] `fileflo` `feat/visa-tracker` worktree — **blocked** due to ambiguous intended base branch (`develop` vs `main` vs deployed `fix/mandatory-file`). Requires workspace decision before proceeding.
- [ ] `passport_extractor` scaffold — **blocked** pending confirmed new-app metadata (publisher, email, license, title, description).

### 8.3 Overall verdict

- **Integration evidence verdict**: sufficient — exact FileFlo, Lead, and PF Process File joins are source-evidenced.
- **Remote worktree count**: 1 (`the_visaguy` only).
- **Frontend scaffold verdict**: pass — lint and build succeed, Git status clean, no remote.
- **Passport scaffold blocker**: missing Frappe new-app metadata; values proposed but not confirmed.
- **Overall verdict**: TASK-001 is **partially complete**. The workspace must resolve the `fileflo` base-branch ambiguity and confirm `passport_extractor` metadata before TASK-002 begins.
