# Improvement Cycle 344

## Topic

Compute dominance only under shared assumptions.

## Deficiency

One candidate can appear superior because it assumes a favorable world while a
rival assumes a harsher one. Treating that difference as value performance
creates false dominance.

## Improvement

Added `validate_shared_assumption_dominance_frontier` and an experimental schema.

Each candidate records assumption IDs, values, fingerprints, and evidence.
Dominance is allowed only when the complete assumption maps match exactly.
When any ID, value, or hash differs, dominance is forbidden and the pair creates
an unresolved decision frontier naming exact differing assumptions, their
decision relevance, needed discriminating evidence, and resolution trigger.
Assumption differences cannot be relabeled as value differences.

## Scope boundary

Cycle 344 protects dominance comparability. Cycle 345 will review the remaining
non-dominated candidates across adversarial axes and sensitivity ranges instead
of aggregate scores.

## Verification

- focused mission tests: 981 passed
- schema JSON parse: 241 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes calls one mission dominant only when both missions are evaluated under
the same assumed world.
