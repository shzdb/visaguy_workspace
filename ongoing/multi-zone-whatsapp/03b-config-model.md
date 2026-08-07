# Phase 3b — WhatsApp config model (Zone rekey)

Branch: `feat/multi-zone-whatsapp` @ `7ffaa26` (was `e690b5b`). Repo: `the_visaguy/` only. `waflo/` untouched.

## New `Whatsapp Default` field list

| fieldname | fieldtype | options / notes |
|-----------|-----------|-----------------|
| settings_tab | Tab Break | |
| **zone** | Link → Zone | **reqd, unique** — configuration key |
| **whatsapp_account** | Link → WhatsApp Account | required by validate when `enabled=1` |
| company | Link → Company | **kept**, `read_only=1`, label `Company (Deprecated / Legacy)` — not reqd/unique anymore |
| enabled | Check | default 0 |
| introduction_tab | Tab Break | |
| introduction_section | Section Break | |
| introduction_image | Attach Image | reqd |
| helpline_number | Data | reqd |
| templates_tab | Tab Break | |
| event_template | Table → WhatsApp Default Templates | |
| feedback_tab | Tab Break | |
| feedback_defaults | Table → Whatsapp Feedback Defaults | |

- `autoname`: `field:zone` (was `field:company`)
- `zone` and `whatsapp_account` appear in **both** `field_order` and `fields`

## Patch: `the_visaguy.patches.backfill_whatsapp_default_zone`

Registered under `[post_model_sync]` in `patches.txt`.

Behaviour:

1. Skip if `zone` column missing.
2. For each `Whatsapp Default` row with `zone` already set → skip (idempotent re-run).
3. Else if `company` matches an existing `Zone` name → `set_value(zone=company, update_modified=False)`.
4. Else if company empty or no matching Zone → `frappe.log_error` loudly; leave `zone` unset (no guessing).

**Why idempotent:** rows with `zone` set are skipped; re-running after a successful backfill performs no writes. Safe if migrate is interrupted and re-run.

### B3 autoname reasoning (verified)

Changing `autoname` from `field:company` to `field:zone` does **not** rename existing documents. The live row stays named `TVG`. Its `company` is `"TVG"` and a Zone named `TVG` exists, so after backfill `zone="TVG"` and the document name remains `TVG`. Name-based and `{"zone": "TVG"}` lookups stay consistent. Child-table `parent` values stay `TVG`.

## Validation rules (M9)

When `enabled = 1`, `validate` rejects the save if any of:

1. No `whatsapp_account` bound.
2. Any of `REQUIRED_EVENT_TYPES` missing from `event_template`:
   - Lead Form, Process Form, Payment Success, Payment Feedback, Completion Feedback
3. Any of `REQUIRED_FEEDBACK_TYPES` missing from `feedback_defaults`:
   - Payment Feedback, Completion Feedback

**`Visa Completion` is not required** (remains a valid Select option; no wired handler).

Constants are module-level: `REQUIRED_EVENT_TYPES`, `REQUIRED_FEEDBACK_TYPES`.

Error message form:

> Cannot enable Whatsapp Default for zone '{zone}': missing \<named gaps\>. Configure each required row explicitly for this zone — configuration is not inherited from another zone.

Title: `Incomplete WhatsApp configuration`. Missing items are named so an operator configuring TVG Qatar sees exactly which rows to add.

## Lookups rekeyed (B4 + B5)

| Site | Change |
|------|--------|
| `is_enabled` signature + `db.exists` | `company` → `zone` |
| 4 `is_enabled(...)` call sites in `handlers/whatsapp_message.py` | `zone=doc/lead.custom_zone` |
| 4 live `frappe.get_doc("Whatsapp Default", …)` | `{"zone": …}` |

Dead commented code left untouched. `receive_feedback.py` not touched (later phase). Index `[0]` sites not touched.

**LOOKUPS_REKEYED = 4** (live `get_doc`); plus `is_enabled` definition and its 4 callers.

## Insights fixture check

Two scripts (`QRY-0931`, `QRY-0933`) join:

```sql
FROM `tabWhatsapp Feedback Defaults` AS fd
INNER JOIN `tabWhatsApp Default Templates` AS dt
    ON dt.parent = fd.parent
```

They key child rows by **parent document name**. Document names do not change (live parent stays `TVG`), so these joins remain valid. No fixture edit required. (`QRY-0935` reads `tabWhatsapp Feedback Defaults` without parent join — also unaffected.)

## Tests added (`the_visaguy/the_visaguy/tests/`)

Package created with `__init__.py`. File: `test_whatsapp_default_zone.py` — **5** test methods:

| Test | Asserts |
|------|---------|
| `test_returns_true_only_for_enabled_matching_zone` | `is_enabled(zone=…)` queries `{"zone", "enabled": 1}` and returns True when exists |
| `test_no_whatsapp_default_returns_false_without_raising` | missing zone → False, no raise |
| `test_enable_with_missing_event_template_is_rejected_and_named` | validate throws; message names `Lead Form` and the zone |
| `test_enable_without_whatsapp_account_is_rejected` | validate throws; message names `whatsapp_account` |
| `test_backfill_sets_zone_from_company_and_is_idempotent` | first run `set_value` zone from company; second run no write |

`FrappeTestCase`. **Not run via bench** — compile-only verification.

## Gates

- `py_compile` on all modified `.py` → pass
- JSON load of `whatsapp_default.json` → yes
- `zone` in `field_order` and `fields` → yes
- `grep` for `"company": doc.custom_zone` / `lead.custom_zone` → none
- `git -C ../waflo status --porcelain` → empty
- No conflict markers

## Uncertain

None material. Company field kept read-only/deprecated with `reqd` removed so new zone rows can be created without a legacy company value; drop in a follow-up release.
