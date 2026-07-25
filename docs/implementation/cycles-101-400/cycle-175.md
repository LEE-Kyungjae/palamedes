# Improvement Cycle 175

## Topic

Preserve beneficiary condition and non-goal invariants during planning.

## Deficiency

A planner could optimize feasibility until the strategy served a different
beneficiary condition or silently discarded a non-goal, producing delivery
success while emptying the mission of its original meaning.

## Improvement

Added `validate_strategy_meaning_invariants` and an experimental schema.

Every strategy review compares the contract's beneficiary condition and
non-goals with the proposal. Feasibility cannot override meaning. Drift cannot
be accepted as strategy adaptation; it must return for an explicit, identified
mission revision with a reason.

## Scope boundary

Cycle 175 protects mission meaning during strategy formation. Cycle 176 will
expand downstream status beyond task delivery to include retired uncertainty
and observed consequence.

## Verification

- focused mission tests: 305 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Execution flexibility ends where beneficiary meaning or a declared non-goal
changes; crossing that line requires an explicit mission revision.
