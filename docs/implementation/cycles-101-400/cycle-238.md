# Improvement Cycle 238

## Topic

Make missions falsifiable without fixing implementation.

## Deficiency

A vague mission cannot fail, but a mission that names its implementation too
early turns planners into executors of a preselected mechanism. Outcome
specificity and implementation commitment must remain separate.

## Improvement

Added `validate_falsifiable_implementation_open_mission` and an experimental
schema.

The contract specifies external beneficiary, current and target conditions,
outcome measure, success threshold, evaluation window, and failure condition.
It forbids a selected implementation before planning and requires at least two
reachable mechanism classes. Cross-mechanism invariants and prohibited
consequences constrain planning without dictating the solution.

## Scope boundary

Cycle 238 balances falsifiability and planner freedom. Cycle 239 will test
whether a skeptical planner can translate an original mission into a plain
beneficiary change without relying on creative metaphor.

## Verification

- focused mission tests: 557 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes states exactly what external change would count as success or failure
while leaving planners free to compare multiple implementation paths.
