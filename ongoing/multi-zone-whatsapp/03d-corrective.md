# 03d corrective — test mocks + account backfill

## Defect 1 — mocks

Replaced every `types.SimpleNamespace` in `the_visaguy/tests/` with `frappe._dict`, which supports both attribute access and `.get()` like a Frappe Document.

Sites fixed (9):
- `test_whatsapp_handlers.py`: event-template child row, lead doc, applicant-info child, inbound feedback doc (×2 tests), quality-feedback template doc, template parameter row
- `test_whatsapp_default_zone.py`: event-template and feedback-defaults child rows used by `validate()`

`receive_feedback.py` unchanged; still uses `doc.get(`.

## Defect 2 — patch strategy: **rename**

Renamed `backfill_whatsapp_default_zone` → `backfill_whatsapp_default_zone_and_account` (module + `patches.txt` entry); deleted the old module.

Why rename rather than a second patch: the zone-only patch already ran on `visaguy` and is in Patch Log, so it would never re-run. A renamed module is a new patch identity that re-applies the (idempotent) zone backfill and adds the account backfill in one cohesive migration. A second patch would also work, but would leave a permanently incomplete first patch in the tree.

Account backfill: only fills empty `whatsapp_account`; uses `WhatsApp Account` with `is_default_outgoing=1`; logs loudly and leaves unset if none; never overwrites a set value.

## Defect 3 — new test

`TestBackfillWhatsappDefaultAccount.test_backfill_sets_default_outgoing_account_without_overwriting` asserts:
- an enabled-equivalent row with `whatsapp_account=None` gets the default-outgoing account
- a row that already has an account is not passed to `set_value` (untouched)
