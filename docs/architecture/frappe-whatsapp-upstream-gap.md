# frappe_whatsapp — Upstream Gap Analysis

Assessment of 21 upstream commits accumulated since our checkout, and what they mean for the capabilities we rebuilt in `waflo`.

**Our pin:** `master` @ `27f3438`, 2025-12-13. Backup branch `master_backup` created at that commit on 2026-08-06; the bench working tree was clean.
**Upstream:** `master` @ `08bc1f6`, 2026-08-04. Remote `https://github.com/shridarpatil/frappe_whatsapp.git`.
**Gap:** 21 commits, 40 files, +3,324 / −320.

Nothing has been merged. This is analysis only.

## The headline question

[ADR-009](../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md) justifies `waflo` on two capabilities `frappe_whatsapp` lacked. Its "revisit when" condition is exactly this situation. The answer is **split**.

### Dynamic URL buttons — now available upstream, but a different model

Upstream `send_template` now emits `sub_type: "url"` button components with index shifting (`5b874db`):

```python
elif btn.button_type == "Visit Website" and btn.url_type == "Dynamic":
    ref_doc = frappe.get_doc(self.reference_doctype, self.reference_name)
    url = ref_doc.get_formatted(btn.website_url)
```

**This is declarative and document-driven.** The URL suffix is a *field on the reference document*, named on the template's button row.

`waflo` is imperative and caller-driven:

```python
button_url_map={"0": f"/form/{form_id}"}
```

The suffix is an arbitrary value computed at send time. Ours comes from an `FF File Collection` lookup — **not a field on the Lead**. To adopt upstream's model we would need a custom field on `Lead` / `CRM Lead` holding the URL suffix, populated before the message fires.

So the capability exists, but it is not a drop-in replacement.

### FLOW buttons — still absent upstream

`grep FLOW` across upstream's `whatsapp_message.py` returns **nothing**. Upstream supports `content_type == "flow"` for *interactive non-template messages*, which is a different mechanism. Template `sub_type: "FLOW"` — what `waflo`'s `use_flow` emits — has no upstream equivalent.

Both our feedback templates (`payment_completion_feedback`, `visa_completion_feedback`) depend on it.

**Conclusion: ADR-009's rationale narrows but does not collapse.** `waflo` remains necessary for FLOW buttons and for rate limiting, which upstream still has none of.

## Major upstream changes

### 1. Frappe v16 support — additive, not breaking

`854760c` adds v16 support; `pyproject.toml` moves from `frappe = ">=14.0.0"` to `">=14.0.0,<=17.0.0-dev"`. **v15 is still supported.**

The v16-specific code is guarded at runtime:

```python
if hasattr(frappe.db, "after_commit"):   # v16+
    ...
else:                                     # v14/v15
    ...
```

On our v15 bench the old path runs. `b510f63` similarly only commits on v16. **Low risk**, but it is the single largest reason to test rather than assume.

### 2. Template button handling — `5b874db`

Static "Call Phone" and "Visit Website" buttons are no longer emitted as components, because Meta rejects them (`sub_type must be one of {...}`). Only buttons with *runtime* parameters go into the payload. Also adds `quick_reply` payload buttons and index shifting when a catalog (MPM) button occupies index 0.

Directly relevant: this is upstream converging on the area `waflo` covers.

### 3. Multi-account fixes

- `8881ba1` — patch ordering bug: `set_default_in_whatsapp_settings` ran first, called `settings.save()`, wiped legacy rows from `tabSingles`, so `migrate_to_multi_account` then found nothing and silently no-op'd. Sites upgrading from the pre-multi-account schema were left **without a WhatsApp Account**. The fix reorders the patches and hardens the migration.

  **We are not in the broken state** — `Visaguy UAE` exists and all seven templates have `whatsapp_account` set. Both patches are already recorded in our Patch Log so they will not re-run.

- `93443e7` — adds a WhatsApp Account field to `WhatsApp Notification`, extending multi-account to notification templates.

### 4. New features we do not currently need

| Commit | Feature |
|---|---|
| `aa80a37` | Catalog / multi-product message (MPM) support |
| `1b34ac9`, `5aabc27` | **Subscribe App to Webhooks** action on `WhatsApp Account` — potentially useful for onboarding Qatar's number |
| `315efc9` | Custom `event_frequency` on `WhatsApp Notification` |
| `ec3c3d2` | S3 file URL support for media |

### 5. Bulk messaging

`891494d` retry of failed bulk messages, `08bc1f6` honours `scheduled_time`. Adds a **new scheduler event**:

```python
"all": [..., "frappe_whatsapp.utils.bulk_messaging.process_scheduled_bulk_messages"]
```

This would begin running on every scheduler tick after a pull. We do not use bulk messaging, so it should be inert — but it is new recurring work appearing without us asking for it.

### 6. Webhook fixes

`8441c38` stops dropping `message_template_status_update` events; `87f48aa` allows framework-managed columns in `data_fields`.

### 7. Test suite

Roughly 2,000 of the 3,324 added lines are tests — `test_webhook.py` (+482), `test_whatsapp_message.py` (+409), `test_whatsapp_templates.py` (+297), `test_bulk_messaging.py` (+275), and more. Upstream went from effectively untested to substantially covered. This materially raises confidence in the other 19 commits.

### 8. Packaging

`setup.py` and `requirements.txt` deleted in favour of flit. Note `requirements.txt` declared `python-magic`; confirm nothing still imports it before pulling.

## Bugs upstream still has that we already fixed in `waflo`

Worth knowing before anyone proposes deleting `waflo`'s send layer:

- `notify()`'s `except` block calls `frappe.flags.integration_request.json()` unguarded — the same defect as FEAT-003 **D8**. When a send fails before the request is issued, this raises `AttributeError` and masks the original error.
- **No rate limiting of any kind.** Anything calling `frappe_whatsapp` directly bypasses our limiter entirely, which is the known cost recorded in ADR-009.

## Proposed plan

Sequenced so nothing collides with work already in flight. **`waflo` and `the_visaguy` currently have unmerged branches touching this exact area** (FEAT-002, FEAT-003), so timing matters more than usual.

### Phase 0 — do not pull yet

FEAT-002 and FEAT-003 are implemented, verified, and **unmerged**. Pulling 21 upstream commits underneath them would mix two large changes and make any regression ambiguous.

**Land FEAT-003 (and optionally FEAT-002) first, let it settle, then take upstream.**

### Phase 1 — dry-run the pull in isolation

On a scratch clone or a non-`visaguy` site, not on the shared bench:

1. Merge `upstream/master` into a throwaway branch off `27f3438`.
2. `bench migrate` and confirm the two already-recorded patches do not re-run.
3. Confirm `whatsapp_message.json`'s ~30 new lines migrate cleanly.
4. Run upstream's new test suite — it is now substantial enough to be a real signal.
5. Verify our seven templates still send: `lead_form` and `process_form` use dynamic URL buttons, and the two feedback templates use FLOW buttons that upstream does not know about.

The critical regression risk is **`5b874db`**. Upstream now filters which buttons become components. `waflo` builds its own payload and does not use upstream's `send_template`, so it should be unaffected — but that must be proven, not assumed.

### Phase 2 — decide on the URL-button model

A genuine architecture decision, not a cleanup:

| Option | Cost | Benefit |
|---|---|---|
| Keep `waflo`'s `button_url_map` | Continue maintaining it | Caller-computed URLs; no schema change; works today |
| Adopt upstream's declarative model | Custom field on `Lead`/`CRM Lead` for the URL suffix, populated before send; rework two handlers | One less thing we maintain; converges with upstream |

**Recommendation: keep `waflo`'s model for now.** FLOW buttons keep `waflo` in the send path regardless, so moving *half* the button handling upstream would split one concern across two apps — strictly worse than either extreme. Revisit if upstream adds template FLOW support.

### Phase 3 — adopt selectively

Worth taking regardless of Phase 2:

- **`1b34ac9` Subscribe App to Webhooks** — plausibly reduces manual steps when onboarding Qatar's number. Evaluate against [`zone-whatsapp-onboarding.md`](../operations/zone-whatsapp-onboarding.md) step 1.
- **`8441c38` webhook status updates** — we consume template status; dropping those events is a real gap.
- **The test suite** — free confidence on an app we depend on and do not maintain.

### Phase 4 — record the outcome

Amend [ADR-009](../../decisions/ADR-009-waflo-as-maintained-whatsapp-extension-layer.md) with the narrowed rationale: dynamic URL buttons are now available upstream in a different form; FLOW buttons and rate limiting are not. That keeps the "revisit when" condition honest for the next person.

## Rollback

`master_backup` @ `27f3438` on the bench. To restore:

```bash
cd ~/bench/apps/frappe_whatsapp && git checkout master_backup
```

Note this restores **code only**. Any schema change applied by `bench migrate` — new `whatsapp_message.json` fields, new patches in Patch Log — is not undone by a checkout. Take a database backup before Phase 1 on any site whose data matters.
