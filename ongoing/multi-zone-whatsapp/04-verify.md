# Phase 4 — Verification

Run on the `visaguy` **development** site, `erpcode.tridz.in`. Production is a separate, inaccessible server.

## Branches verified

| Repo | Branch | Head |
|---|---|---|
| `waflo` | `feat/multi-zone-whatsapp` | `f81fe81` |
| `the_visaguy` | `feat/multi-zone-whatsapp` | `aa3ef89` |

Both pushed to their upstreams.

## Test results — runtime-verified

```
bench --site visaguy run-tests --app waflo
Ran 28 tests in 0.107s
OK
```

```
bench --site visaguy run-tests --app the_visaguy --skip-test-records
Ran 13 tests in 0.051s
OK
```

`waflo` 28 = 20 from FEAT-003 + 8 new. `the_visaguy` 13 = all new; the app previously had six test files, all empty stubs.

**`--skip-test-records` is required on this bench.** A pre-existing site customization (`visaguy_crm` / `visaguy_hrms` custom fields on Company) makes `custom_display_name` mandatory, so Frappe's stock test-record bootstrap fails with `MandatoryError: [Company, _Test Company]`. Not caused by this work; it blocks stock test records for every app here.

## Migration — runtime-verified against real data

`bench migrate` was run on `visaguy`. This is the part unit tests could not prove.

| Stage | `zone` | `company` | `whatsapp_account` |
|---|---|---|---|
| Before | — | `TVG` | — |
| After first migrate | `TVG` | `TVG` | **NULL** |
| After corrected patch | `TVG` | `TVG` | `Visaguy UAE` |

Document name stayed `TVG` throughout, confirming the reasoning that changing `autoname` does not rename existing documents.

### The defect the migration exposed

The first patch backfilled `zone` correctly but left `whatsapp_account` NULL on an `enabled = 1` row — which the new M9 validation requires. Sending still worked, because the handler passes `None` and `waflo` falls back to the default account. But **the record could no longer be saved**, so any operator edit would have been rejected.

A migration must not leave live configuration unsaveable. Fixed by extending the patch to backfill `whatsapp_account` from the account flagged `is_default_outgoing` — the account those rows already send from, so behaviour is preserved exactly. The patch was renamed so it would re-execute on a site where the original had already been recorded in Patch Log.

**No unit test would have caught this.** It required running the migration against real data.

### Save cycle confirmed

`frappe.client.set_value` on the live `TVG` record completed successfully, proving the full `validate` cycle now passes. The returned document also confirms the required-configuration list derived for M9 matches live data exactly:

- `event_template`: Lead Form, Process Form, Payment Success, Payment Feedback, Completion Feedback — **exactly the five required, and no `Visa Completion` row**
- `feedback_defaults`: Payment Feedback, Completion Feedback — both present with header images
- `whatsapp_account`: `Visaguy UAE`

This independently corroborates the owner's F4 answer: `Visa Completion` is not a separate send.

## Second defect found by running, not reading

The first `the_visaguy` suite run gave `Ran 12 tests, FAILED (errors=2)`:

```
AttributeError: 'types.SimpleNamespace' object has no attribute 'get'
  at receive_feedback.py:16 -> if doc.get("whatsapp_account"):
```

The **implementation was correct** — real Frappe Documents support `.get()`. The **test mocks were wrong**. The corrective explicitly forbade "fixing" this by weakening `receive_feedback.py` to `getattr(...)`, which would have made the test pass while making production code worse. Nine mocks were corrected across the file, not just the two that happened to fail.

## What was implemented

| Area | Items |
|---|---|
| `waflo` send path | M1–M4 — account parameter, threaded through the `queue=True` branch, template language read from the record, loggers receive the account actually used |
| `waflo` corrections | F2 retry re-sends from the stored account; F3 inbound replies leave from the inbound account |
| `the_visaguy` config | M5 account binding; M6/M6b rekey to Zone with `autoname: field:zone`; M9 validation naming exactly what is missing |
| `the_visaguy` handlers | M10 (7 index sites), M11 (4 lookups), M12–M16 cleanup, plus F1 zone-aware feedback |
| Deferred | M7/M8 extensible event types |

**Never falls back.** An unknown account name throws rather than silently using the default — the guarantee that a Qatar customer cannot receive a UAE-numbered message because of a configuration typo.

## Bench state changed

- `waflo` and `the_visaguy` are on `feat/multi-zone-whatsapp` (owner instructed).
- This bench's own redis instances were started (ports 13008 / 12008 / 11008). `bench migrate` refuses to run without them. This is a **shared multi-tenant server** — other developers' benches run on other ports and were not touched.
- `visaguy` now has the `zone` column, the backfilled row, and both patches in Patch Log. Not reversible by checking out a different branch.
- `allow_tests` remains enabled from earlier work.

## Not verified

- **No live WhatsApp send.** No message has actually been delivered from a second account, because no second `WhatsApp Account` exists yet — that is [TASK-018](../../tasks/ready/multi-zone-whatsapp/TASK-018-tvg-qatar-meta-prerequisites.md).
- **Multi-zone behaviour is proven only by unit tests.** With one account configured, every runtime path still resolves to `Visaguy UAE`. The routing logic is exercised by mocks, not by two real accounts.
- **No end-to-end feedback round trip** — an inbound flow reply on a second number has never been matched to its zone in reality.
- The pre-existing `MandatoryError` on Company test records is worked around, not fixed.
- An unrelated pre-existing warning appears during migrate: `Skipping fixture syncing from custom_field.json. Reason: No module named 'helpdesk.helpdesk.doctype.hd_settings.helpers'` — a `helpdesk` fork issue, not caused by this work, but worth someone's attention.

## The real gate

Everything above proves the code is internally consistent and the migration is safe. It does **not** prove Qatar works, and cannot until a second WhatsApp Account exists. The first genuine multi-zone test is step 5 of [`zone-whatsapp-onboarding.md`](../../docs/operations/zone-whatsapp-onboarding.md): trigger a message for a Qatar lead and confirm the resulting `WhatsApp Message` shows Qatar's account, not `Visaguy UAE`.
