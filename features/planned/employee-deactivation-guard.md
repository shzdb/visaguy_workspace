# Employee Deactivation Guard

## Status

planned

## Summary

Prevent HR from deactivating an employee while there are pending (non-terminal) Leave Applications. This avoids the `InactiveEmployeeStatusError` that blocks subsequent leave approval/rejection.

## Motivation

HR occasionally marks employees as Inactive before processing all their pending leave requests. Once inactive, HRMS blocks all workflow actions on those leaves, requiring manual re-activation to unblock.

## Scope

### Phase 1 (this feature)

- Block employee status change to Inactive/Left/Suspended when pending Leave Applications exist.
- Pending = any Leave Application not in Approved, Rejected, or Cancelled state.
- Both `Open` and `Reviewed` workflow states are considered pending.
- Error message lists affected leave applications with clickable links.

### Phase 2 (deferred)

- Extend to Attendance Request, Compensatory Leave Request, Leave Encashment.
- To be implemented when those features are actively used.

## Implementation

- Custom app: `visaguy_hrms`
- File: `custom_scripts/employee_hooks.py`
- Hook type: `doc_events` → Employee → validate
- No changes to the Employee class override.

## Decision reference

[ADR-003](file:///home/fasil/Tridz/visaguy_workspace/decisions/ADR-003-employee-deactivation-guard.md)

## Dependencies

- `visaguy_hrms` app (internally maintained, `tridz-dev/visaguy_hrms`)
- HRMS Leave Application DocType
- Leave Approval workflow (Open → Reviewed → Approved/Rejected)
