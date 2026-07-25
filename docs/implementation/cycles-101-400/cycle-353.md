# Improvement Cycle 353

## Topic

Prevent mission compilation from generating tasks.

## Deficiency

Even a semantically faithful planner adapter can cross the purpose/planning
boundary if its first call asks for tasks or lets a planner begin execution.
That collapses strategy review, mission correction, authority issue, and task
decomposition into one irreversible handoff.

## Improvement

Added `validate_strategy_only_first_planner_handoff` and an experimental
schema.

The first handoff has exactly four custody events: Palamedes dispatches the
compiled mission, the planner acknowledges it, the planner proposes a strategy,
and the proposal returns for mission review. Every event is fingerprinted.
The boundary then waits for Palamedes strategy review. No task artifact,
implementation sequence, execution command, execution authority, implementation
start, or planner self-approval is permitted.

## Scope boundary

Cycle 353 fixes the first-handoff stopping point. Cycle 354 will define what the
planner acknowledgment must say about beneficiary, meaning, authority, and
unclear clauses.

## Verification

- focused mission tests: 1017 passed
- schema JSON parse: 250 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The first planner interaction returns understanding and strategy for review; it
does not silently become task generation or execution.
