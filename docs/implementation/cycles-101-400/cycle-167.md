# Improvement Cycle 167

## Topic

Retire goals whose underlying condition has disappeared.

## Deficiency

A mission could continue after succeeding or after an environmental change
removed the beneficiary condition that originally justified it. Past success
then became an argument for institutional self-preservation.

## Improvement

Added `validate_underlying_condition_review` and an experimental schema.

The review compares the original beneficiary condition with a sourced current
observation. Goals are not preserved by default. A resolved or disappeared
condition forces retirement, revocation of delegation, resource shutdown,
downstream notification, and lineage preservation—even when the mission was
successful. A sourced recurrence trigger permits later reconsideration.

## Scope boundary

Cycle 167 retires completed or obsolete purposes. Cycle 168 will preserve
uncertainty about whether value, mechanism, timing, or luck caused an outcome.

## Verification

- focused mission tests: 273 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Past success cannot preserve a mission after the external condition that gave
the mission meaning has been resolved or disappeared.
