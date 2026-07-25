# Improvement Cycle 351

## Topic

Adapt goal-and-success-metric planner interfaces.

## Deficiency

Existing planners often accept only a goal and success metric. Passing a mission
contract directly is incompatible, but flattening it into those two strings
silently discards causal, harm, non-goal, authority, and lineage state and can
make the lossy adapter output appear authoritative.

## Improvement

Added `validate_linked_planner_interface_compilation` and an experimental
schema.

The adapter emits the required `goal` and `success_metric` while retaining an
immutable, hash-addressed source mission contract. Both compiled fields carry
reconstructable field lineage. A loss manifest names omitted source fields and
keeps them retrievable. Compilation cannot mutate or replace the source, claim
to be lossless, or promote the planner input above the mission contract.

## Scope boundary

Cycle 351 establishes source retention and compilation lineage. Cycle 352 will
specify the semantic mapping from mission outcome, signals, causal thesis, and
non-goals into planner fields.

## Verification

- focused mission tests: 1009 passed
- schema JSON parse: 248 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A narrow planner can receive its familiar goal and metric fields without
turning a lossy projection into the authoritative mission or severing access to
the richer source.
