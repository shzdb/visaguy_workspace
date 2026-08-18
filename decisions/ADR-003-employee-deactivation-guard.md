# ADR-003: Employee Deactivation Guard

## Status

Accepted

## Context

HR occasionally marks employees as Inactive while there are pending Leave Applications against those employees. Once an employee is Inactive, HRMS's `validate_active_employee()` check (called during Leave Application `validate()`) blocks any subsequent workflow actions — including approve and reject. This leaves orphaned pending leaves that cannot be processed without manually re-activating the employee.

The error is `InactiveEmployeeStatusError: Transactions cannot be created for an Inactive Employee`.

## Decision

- Add a validation guard on the Employee DocType that prevents status changes to non-active states (Inactive, Left, Suspended) when there are pending Leave Applications.
- Implement this as a `doc_events` → `validate` hook in `visaguy_hrms`, not as a modification to the existing Employee class override, to keep upgrade compatibility clean.
- Scope initially to Leave Application only. Other HR doctypes (Attendance Request, Compensatory Leave Request, Leave Encashment) will be added when those features are actively used.
- A Leave Application is considered "pending" if it is not in a terminal state (Approved, Rejected, or Cancelled). Both Open and Reviewed workflow states are pending.
- The guard function lives in `visaguy_hrms/custom_scripts/employee_hooks.py`.

## Consequences

### Positive

- Prevents the root cause: HR cannot create the invalid state in the first place.
- Implemented as a hook rather than a class override change, reducing merge risk during HRMS upgrades.
- Clear error message with links to the specific pending leave applications.

### Negative

- HR must approve/reject/cancel all pending leaves before deactivating an employee, which adds a step to the offboarding workflow.
- Only covers Leave Application initially; other document types are deferred.

## Alternatives considered

- **Allow processing**: Override `validate_active_employee` to skip the check during approve/reject workflow actions. Rejected because it would require patching HRMS upstream code or adding fragile monkey-patches.
- **Auto-cancel**: Automatically cancel all pending leaves when an employee is deactivated. Rejected because it silently discards potentially valid leave requests without HR review.
- **Class override modification**: Add the guard inside the existing Employee class override. Rejected at user's request to keep the class override minimal and avoid complications during future HRMS upgrades.

## Revisit when

- Other HR document types need the same protection.
- HRMS upstream adds its own deactivation guard (check release notes on upgrade).
