---
id: TASK-019
feature: FEAT-002
title: Implement per-zone WhatsApp routing and configuration
status: completed
repository: waflo, the_visaguy
owners: []
depends_on: []
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Implement per-zone WhatsApp routing and configuration

## Objective

Make WhatsApp auto messages and feedback messages work per Zone, so a second zone sends from its own number.

## Implementation evidence

| Repo | Branch | Head | Commits |
|---|---|---|---|
| `waflo` | `feat/multi-zone-whatsapp` | `f81fe81` | `f81fe81` |
| `the_visaguy` | `feat/multi-zone-whatsapp` | `aa3ef89` | `7ffaa26`, `280ec5e`, `aa3ef89` |

Both pushed. `waflo` is branched off `feat/waflo-correctness`, not `develop` — see the coupling note below.

### `waflo` — `f81fe81`

M1–M4 plus two recon findings. `send_whatsapp_template` gains a `whatsapp_account` parameter at the end of the signature with a `None` default; when supplied it sends from that account, and when the named account does not exist it **throws rather than falling back**. Threaded through the `queue=True` enqueue branch — a dropped kwarg there would have broken only queued sends. Template language now read from the `WhatsApp Templates` record instead of a hardcoded `"en"`. Loggers receive the account actually used.

F2: `retry_message` now reads `whatsapp_account` off the stored `WhatsApp Message`, so a deferred Qatar message is retried from Qatar's number rather than the default.

F3: `processor.py` threads the inbound account through every send, including `send_default_message`. That path is live with the flow engine off, so without this a Qatar customer messaging Qatar's number would have received a reply from the UAE number.

### `the_visaguy` — `7ffaa26`, `280ec5e`, `aa3ef89`

M5, M6, M6b, M9: `Whatsapp Default` rekeyed to Zone (`autoname: field:zone`, `zone` required and unique), `whatsapp_account` binding added, `is_enabled(zone, customer)` renamed and rekeyed with all four call sites updated, and validation that names exactly what is missing when a zone is enabled. Legacy `company` retained read-only rather than dropped.

M10–M16 plus F1: all seven `[...][0]` index sites replaced with safe lookups that skip and log a warning naming the zone; four `get_doc` lookups guarded; dead `COMPANY = "TVG"` and the commented `send_default_message` removed; hardcoded hostname moved to configuration; log spam removed; `clean_mobile_no` strengthened. `receive_feedback.py` resolves zone from the inbound account, falling back to the referenced lead, and skips with a warning rather than defaulting to TVG.

The critical wiring: all five `send_whatsapp_template` calls now pass `whatsapp_account=whatsapp_default.whatsapp_account`. Without this the field would exist and nothing would read it.

## Validation

Runtime-verified on the `visaguy` dev site.

- `bench --site visaguy run-tests --app waflo` → **28/28 pass**
- `bench --site visaguy run-tests --app the_visaguy --skip-test-records` → **13/13 pass**
- `bench --site visaguy migrate` → backfill verified against real data; live record saves cleanly

`--skip-test-records` is required on this bench because a pre-existing customization makes `custom_display_name` mandatory on Company, breaking Frappe's stock test-record bootstrap. Not caused by this work.

## Deviations and corrections

### The migration left live configuration unsaveable

The first backfill patch set `zone` correctly but left `whatsapp_account` NULL on the `enabled = 1` row — which the new M9 validation requires. Sending still worked (the handler passes `None` and `waflo` falls back), but the record could no longer be saved, so any operator edit would have been rejected.

Fixed by extending the patch to backfill `whatsapp_account` from the account flagged `is_default_outgoing` — the account those rows already send from, preserving behaviour exactly — and renaming the patch so it re-executes where the original was already recorded in Patch Log.

**No unit test would have caught this.** It required running `bench migrate` against real data.

### Test mocks were wrong, not the implementation

The first suite run failed with `AttributeError: 'types.SimpleNamespace' object has no attribute 'get'`. Real Frappe Documents support `.get()`; the mocks did not. The corrective explicitly forbade "fixing" this by weakening `receive_feedback.py` to `getattr(...)`, which would have made the test pass while degrading production code. Nine mocks corrected across the file, not just the two that failed.

### Spec counts were stale

Recon corrected the plan: **4** live lookup sites, not 5 (the 5th is in dead commented code); **7** index sites, not 6 (the payment path alone has three).

### Scope

M7/M8 (extensible `Whatsapp Event Type` DocType) deferred per owner decision — Qatar uses the same six event types, only the templates differ. `Visa Completion` deliberately not implemented; the owner confirmed it ships with the completion feedback message, and the live TVG record independently corroborates this by having exactly five event templates and no Visa Completion row.

## Known limitations

- **Multi-zone behaviour is proven only by unit tests.** With one `WhatsApp Account` configured, every runtime path still resolves to `Visaguy UAE`. Routing is exercised by mocks, not by two real accounts.
- **No live WhatsApp message has been sent from a second account**, because none exists yet — that is [TASK-018](../../ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md).
- No end-to-end feedback round trip on a second number.
- `the_visaguy` had zero real tests before this work, so all 13 are new with no regression baseline.

## Deployment coupling

`waflo`'s branch sits on top of `feat/waflo-correctness`. **Deploying FEAT-002 deploys FEAT-003 with it**, so [TASK-017](../../blocked/waflo-correctness/TASK-017-staging-and-live-deployment.md)'s prerequisites gate this feature too.
