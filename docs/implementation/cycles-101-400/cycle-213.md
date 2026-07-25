# Improvement Cycle 213

## Topic

Resolve prohibition conflicts through an explicit precedence graph.

## Deficiency

Hard prohibitions can conflict. If Palamedes silently uses declaration order,
array position, or implementation accident to choose a winner, an apparent
constitutional decision has no accountable authority.

## Improvement

Added `validate_prohibition_precedence_graph` and an experimental schema.

The contract registers hard prohibitions and directed, reasoned precedence
edges. The graph must be acyclic. A concrete conflict can select a prohibition
only when the corresponding directed edge exists; otherwise it remains
explicitly unresolved with no selected winner and invokes a declared suspension
or escalation action. Declaration order can never break ties.

## Scope boundary

Cycle 213 governs conflict among hard prohibitions. Cycle 214 will govern
overrides of defeasible principles with reasons and predicted consequences.

## Verification

- focused mission tests: 457 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes resolves conflicting prohibitions only through explicit
constitutional precedence and preserves unresolved conflict when no such
authority exists.
