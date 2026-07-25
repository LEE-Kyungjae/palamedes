# Improvement Cycle 296

## Topic

Stabilize purpose and implementation ownership across the planner boundary.

## Deficiency

Purpose drifts when planners quietly rewrite why or what outcome, while planning
is strangled when Palamedes prescribes implementation form. A rigid boundary is
also unsafe if new evidence cannot reopen the side competent to respond.

## Improvement

Added `validate_stable_purpose_planner_boundary` and an experimental schema.

Palamedes exclusively owns situation meaning, beneficiary, desired external
condition, and non-goals. Planners own implementation form, task decomposition,
tool selection, and execution sequence. Value or beneficiary evidence reopens
Palamedes, implementation constraints reopen the planner, and causal or
capability evidence reopens both. Evidence triggers review but never directly
rewrites an owned artifact.

## Scope boundary

Cycle 296 fixes responsibility and reopening routes. Cycle 297 will materialize
the minimal purpose runtime as six distinct linked state types.

## Verification

- focused mission tests: 789 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Why and what remain stable under Palamedes, how remains free under planners, and
new evidence reaches the correct owner without bypassing either decision
process.
