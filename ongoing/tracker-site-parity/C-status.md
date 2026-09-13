# C-status — status tone alignment

## Final cue lists

From `src/lib/statusTone.ts`:

- **critical**: `reject`, `refus`, `declin`, `cancel`, `withdraw`, `fail`, `action`
- **success**: `approv`, `issued`, `grant`, `complet`, `deliver`, `collect`, `ready`
- **brand**: `progress`, `working`, `process`, `review`, `submit`, `lodg`, `receiv`, `pending`, `confirm`, `payment`
- **neutral**: fallback

## Mapping table with observed results

| Input                             | Expected | Observed |
| --------------------------------- | -------- | -------- |
| Draft                             | neutral  | neutral  |
| Payment Confirmed                 | brand    | brand    |
| Application Submitted             | brand    | brand    |
| Application Processing            | brand    | brand    |
| Pending Action                    | critical | critical |
| Application Received              | brand    | brand    |
| Working on Your Application       | brand    | brand    |
| Visa Approved                     | success  | success  |
| Visa Issued                       | success  | success  |
| Visa Rejected                     | critical | critical |
| Rejected - application complete   | critical | critical |
| Some Unknown Backend Status       | neutral  | neutral  |

All C1 pairs correct: **yes**

## Gate results

- `npm run lint`: passed (1 pre-existing warning in `src/context/SessionContext.tsx`, not touched)
- `npx tsc --noEmit`: passed
- `npm run test`: **55 passed / 0 failed** (41 existing + 14 new)
- `npm run build`: passed

## Commit

`fix(ui): align status tone mapping to the real application status vocabulary`
SHA: `6f01fc844e8c53d050fff67dc3b037c1c7b4a018`
