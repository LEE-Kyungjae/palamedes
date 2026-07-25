# Improvement Cycle 252

## Topic

Begin the planner contract with situation and meaning.

## Deficiency

A planner that sees an objective or mechanism before the originating condition
and its stakes can optimize a detached target. Even a technically faithful
plan then loses why the mission was selected and cannot recognize when changed
reality has invalidated it.

## Improvement

Added `validate_situation_meaning_first_contract` and an experimental schema.

The contract fixes its first two sections as `situation` and `meaning`.
Situation must identify the current observed condition, scope, evidence, and
observation time without prescribing a solution. Meaning must state why the
condition matters, what stake is at risk, its interpretive evidence, and its
connection to selection; it cannot be reduced to a metric target. Beneficiary,
desired condition, causal thesis, boundaries, and signals follow afterward.

## Scope boundary

Cycle 252 fixes the contract's semantic opening. Cycle 253 will make beneficiary
and desired external condition explicit within that downstream structure.

## Verification

- focused mission tests: 613 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Before a Palamedes planner optimizes anything, it receives the condition that
exists and the consequential meaning that made the mission worth pursuing.
