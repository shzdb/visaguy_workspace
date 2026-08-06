---
id: TASK-015
feature: FEAT-003
title: Harden the send path and remove dead configuration
status: completed
repository: waflo
owners: []
depends_on:
  - TASK-014
expected_files: []
created: 2026-08-06
updated: 2026-08-06
---

# Harden the send path and remove dead configuration

## Objective

Fix D8, D9, D10, D11, N2, N4, and remove the dead `limit_after` field (D6).

## Owner decision applied

D6 — `WF Settings.limit_after` sat under the Rate Limiting tab and was read by no code. Nobody could establish what it was for, so it is **removed** rather than guessed at.

## Implementation evidence

`tridz-dev/waflo`, branch `feat/waflo-correctness`, commit **`d057f1e`** — *fix(send): harden template send and drop dead limit_after*.

| Defect | Fix |
|---|---|
| D8 | `frappe.flags.integration_request` referenced in the `except` block raised `AttributeError` when a send failed before the HTTP request was issued, masking the original error. Now guarded; the original exception is always logged with a traceback. |
| D9 | An unknown template produced `"name": null` in the payload. Now raises a clear, actionable error instead of sending. |
| D10 | `frappe.log_error("WhatsApp API URL AND INDEX", ...)` fired inside the per-button loop on every send with buttons. Removed. |
| D11 | `use_flow` combined with `button_url_map` — both hard-code button index `0`. **Rejected with a clear error** rather than guessing the Meta template's button order. |
| N2 | The continuing-flow branch dereferenced `active_doc.reference_doctype/name` unguarded while `create_active_flow` permits them to be `None`. Now guarded like the new-flow branch. |
| N4 | `send_default_message` read `wf_account_settings.header_video`, which does not exist on `WF Account Settings`. Corrected. |
| D6 | `limit_after` removed from `wf_settings.json` (both `field_order` and `fields`), with a patch registered to drop it on existing sites. |

Files: `send.py`, `processor.py`, `wf_settings.json`, `patches.txt`, patch module, `tests/test_send_hardening.py`.

## Validation

`test_send_hardening.py` (4 tests). Full suite 20/20 on the `visaguy` dev site.

Gates confirmed by the orchestrator across the whole branch: `grep -rn "limit_after" waflo/` empty, `grep -rn "header_video" waflo/` empty, `grep -rn "WhatsApp API URL AND INDEX" waflo/` empty, all doctype JSON parses, `python3 -m compileall` clean.

## Deviations

E4 offered a choice between rejecting the `use_flow` + `button_url_map` combination or offsetting the flow button index. **Reject** was chosen: offsetting would require guessing the button order in the Meta-side template, which could send a silently wrong payload.

Verified safe for every current caller — `the_visaguy`'s `_send_lead_form_link` and `_send_process_form_link` use `button_url_map` only; both feedback sends use `use_flow` only. **No current caller combines them.**

## Known limitations

The D11 rejection is a real constraint on future template design: a template needing both a dynamic URL button and a FLOW button cannot be sent in one call and will throw. That is deliberate — loud failure over a wrong payload — but it must be known before such a template is designed.

The D6 removal patch has **not been run** against a site with the field populated; `bench migrate` was not executed as part of this task.
