# Implement Employee Deactivation Guard

## Status

ready

## Feature

[employee-deactivation-guard](file:///home/fasil/Tridz/visaguy_workspace/features/planned/employee-deactivation-guard.md)

## Decision

[ADR-003](file:///home/fasil/Tridz/visaguy_workspace/decisions/ADR-003-employee-deactivation-guard.md)

## Objective

Add a `doc_events` validate hook on Employee in `visaguy_hrms` that prevents status changes to non-active states when pending Leave Applications exist.

## Files to create/modify

### Create: `visaguy_hrms/custom_scripts/employee_hooks.py`

Single function `check_pending_leave_applications(doc, method)`:
- Return early if `doc.status == "Active"`.
- Return early if `not doc.has_value_changed("status")`.
- Query `Leave Application` where employee = doc.name, docstatus != 2, status not in (Approved, Rejected).
- If results found, `frappe.throw()` with a list of pending leaves (max 10 shown, with links).

### Modify: `visaguy_hrms/hooks.py`

Add to `doc_events`:
```python
"Employee": {
    "validate": "visaguy_hrms.custom_scripts.employee_hooks.check_pending_leave_applications",
}
```

## Verification

1. Test employee with pending leave → status change blocked with descriptive error.
2. Test employee with no pending leave → status change succeeds.
3. Test employee with only approved/rejected leaves → status change succeeds.
4. Test save without status change → no interference.
5. Test status change from Inactive → Active → no interference.

## Acceptance criteria

- [ ] Guard function deployed to `visaguy_hrms`
- [ ] Hook registered in `hooks.py`
- [ ] Manual verification steps 1–5 pass
- [ ] No regression in existing Employee class override behaviour
