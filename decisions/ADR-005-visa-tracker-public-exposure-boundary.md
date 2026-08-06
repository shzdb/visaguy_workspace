# ADR-005: Visa Tracker Status Ownership and Public Exposure Boundary

## Status

Accepted

## Context

FEAT-001 exposes visa application status to the public, authenticated only by passport number and date of birth. Both are weak knowledge factors: passport numbers are semi-guessable within a range and dates of birth are low-entropy. The system must therefore assume the verification pair will eventually be brute-forced or leaked, and limit what a successful lookup can reveal.

Separately, status is written from two directions — operations work in `PF Process File`, while corrections occasionally need to happen on the tracking record itself — which risks recursion and duplicate history entries.

The client-facing status vocabulary is also a business concern that changes without engineering involvement.

## Decision

### Status ownership

- `Visa Tracking Application.current_status` is the single canonical current public state.
- `Visa Tracking Status Log` is the canonical immutable client-visible timeline.
- `Visa Tracking Status` records are **configuration, not code**. Each carries a stable code, order, default message, active flag, final flag, success flag, and `allow_on_process_file` flag. No business logic may branch on a status *label*.
- Before a Process File exists, status is the configured default from `Visa Tracker Settings`. No Lead status field is required.
- After a Process File is linked, `PF Process File.custom_client_status` is the normal operations input.
- Direct changes from `Visa Tracking Application` are exceptional, must synchronise the linked Process File, and must not recurse.
- All status writes route through one service so that exactly one log entry is created per *effective* change. Re-saving the same status creates no log row.

### Public exposure boundary

The public response may contain **only**: masked applicant name, masked passport number, destination and visa type when approved, current public status, configured public message, last-updated timestamp, public status timeline, and a generic support link.

It must **never** contain: date of birth, full passport number, passport files, extracted MRZ, internal document names, Lead/Customer/PF identifiers, internal notes, employee names, authority documents, payment data, or processing errors.

### Access controls

- Lookup is HMAC-based; the passport/DOB pair is never stored or transmitted in a reversible public form.
- A successful verification returns a short-lived **opaque** session token held in Redis. The token encodes nothing.
- Rate limiting and temporary lockout apply to repeated failures.
- Every failure mode — wrong passport, wrong DOB, no such record, locked out — returns one generic response. The API must not let an attacker distinguish them.
- CORS is restricted to the tracker origin.
- Verification attempts are recorded in `Visa Tracker Audit Log`.
- No sensitive value may appear in a URL, query string, log line, browser storage, analytics payload, or error message.
- The MVP permits one active tracking application per verified passport identity. Multiple simultaneous active applications require internal review rather than a public case selector.

## Consequences

### Positive

- A brute-forced lookup yields masked, minimal, non-actionable information.
- Uniform failure responses remove the oracle that would make enumeration cheap.
- Business can change the client-facing status vocabulary without a deployment.
- One write path makes the timeline trustworthy as an audit record.

### Negative

- Masking limits the usefulness of the public view; some clients will still call support.
- Uniform errors make legitimate user mistakes harder to self-diagnose.
- Status-as-records means a misconfigured settings row can stall lifecycle transitions silently.
- Redis becomes a availability dependency of the public tracker.
- One active application per passport identity is a real product limitation for repeat or concurrent applicants.

## Open item

Commit `8254f93` in `the_visaguy` ("feat: auto verify extraction") introduces automatic verification of extractions. FEAT-001 excludes "automatic use of unverified extraction data" and requires that only a verified extraction be linked as the preferred passport. Auto-verification is compatible with that rule **only if** its promotion criteria are strict — a valid TD3 MRZ with all check digits passing, and no duplicate conflict.

**The criteria must be reviewed and recorded here during TASK-010.** Until then this ADR does not sanction auto-verification.

## Alternatives considered

- **Full details behind passport + DOB.** Rejected: the authentication factors are too weak to protect them.
- **Distinct error messages per failure mode.** Rejected: gives an attacker a free enumeration oracle.
- **Status as a hardcoded Select field.** Rejected: makes every business wording change an engineering deployment.
- **A public case selector for multiple active applications.** Rejected for the MVP: it leaks the existence and count of a person's applications to anyone holding the weak factor pair.

## Revisit when

A stronger public authentication factor is introduced (OTP to a verified phone or email), the one-active-application limit blocks real cases, or the auto-verification review in TASK-010 concludes.
