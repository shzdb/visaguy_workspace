# Phase 2 — Triage (orchestrator)

Recon confirmed all 11 spec defects still present at the claimed sites, plus 4 new ones. Zero real test coverage — the four test files are empty Frappe scaffolds.

## Orchestrator spot-checks

| Claim | Verified how | Result |
|---|---|---|
| N1 positional shuffle | Compared `send.py:7` signature against `processor.py:60` call, both read directly during the 2026-08-06 audit | **Confirmed** — position 4 is `header_params`, so `button_url_map` lands in the header, `ref_doctype` becomes `button_url_map`, `ref_name` becomes `ref_doctype`, and `ref_name` is dropped |
| N4 `header_video` | `WF Account Settings` field list read during the audit: `header_image`, `header_attachment`, `header_text` — no `header_video` | **Confirmed** |
| D1 `NameError` | Read `processor.py` def boundaries during the audit: `process_whatsapp_message` spans 41–108, so line 61 is inside it and `doc` is unbound | **Confirmed** |

## Severity ranking

**Customer-visible, ship first:**

- **D1** — new conversations get no `WF Active Chat Flow`; initial step re-sent on every inbound message. A message loop toward the customer.
- **N1** — every flow-driven send has mangled arguments. Buttons broken, message-to-record linkage lost.

**Correctness of the safety mechanism:**

- **D2 / D4 / D5 / N3** — the limiter does not count, cannot count atomically, has two competing window mechanisms, and check/increment disagree on incomplete config. One rewrite fixes all four.

**Robustness, no behaviour change on the happy path:**

- **D8, D9, D10, D11, N2, N4** — error masking, missing guards, log spam, button index collision, null-reference assumption, nonexistent field.

**Blocked on a product decision — NOT assigned to an executor:**

- **D3** outbound rate limiting. Open question 3 is unresolved: may a transactional message (payment success, visa completion) ever be *dropped*? Implementing a naive limiter here could silently swallow payment confirmations.
- **D7** account-level ceiling. Needs Meta tier and quality-rating values (open question 4).
- **D6** `limit_after`. Nobody has established what it was meant to do (open question 1).

Per `.agents/rules/project-rules.md`, unresolved product decisions are not assigned to implementation agents. These three are held back and surfaced to the owner.

## Execution order

Sequenced so later phases build on committed earlier work, and so that phases editing the same file do not collide.

| Phase | Scope | File(s) | Rationale |
|---|---|---|---|
| 3a | D1 + N1 | `processor.py` | Highest severity, customer-visible, both in the same function |
| 3b | D2, D4, D5, N3 | `rate_limiting.py`, `processor.py` | Limiter rewrite; must land before anything consumes it |
| 3d | D8–D11, N2, N4 | `send.py`, `processor.py` | Robustness; last because 3a/3b also touch `processor.py` |
| 4 | Verify | — | Gated on test-site availability |

Phase 3c (D3, D7) is **removed** from this run pending owner decisions.

## Policies for executors

1. `frappe.cache()` is a Redis client — use `.incr()` / `.expire()`. No separate connection, no site prefixing.
2. Fix `processor.py:151` **nowhere** — that `increment_rate_limit(doc.whatsapp_account, ...)` call is correct, `doc` is a parameter of `send_default_message`.
3. Every fixed call site must use **keyword arguments** for `send_whatsapp_template`, so N1 cannot recur.
4. Do not silently broaden a `try` block. The broad `except Exception` in `process_whatsapp_message` is what hid D1 for so long — narrow it where practical and always log the exception with a traceback.
5. Preserve existing public function signatures unless a defect requires the change; other apps import from `waflo.waflo.messaging.send`.
6. Tests: Frappe `FrappeTestCase`. Write them so they exercise logic without requiring live WhatsApp API calls — mock `make_post_request`.

## Verification reality

`waflo` is installed on the `visaguy` site, which is a **development** environment (production is a separate, inaccessible server). The suite was run there after implementation: 15/15 pass. See `04-verify.md` for what the tests do and do not cover.
