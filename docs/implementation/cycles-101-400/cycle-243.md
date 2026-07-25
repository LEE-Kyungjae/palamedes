# Improvement Cycle 243

## Topic

Select with boundaries, dominance, and unresolved tradeoffs.

## Deficiency

A single judge or weighted score collapses distinct constitutional, causal, and
beneficiary concerns into one reward. A high score can compensate for a
disqualifying violation, and genuine value tradeoffs disappear into arithmetic.

## Improvement

Added `validate_nonscalar_mission_selection` and an experimental schema.

Selection first applies evidence-backed pass or disqualify boundaries to every
candidate. It then records dominance only under a named shared assumption set.
Remaining non-dominated conflicts preserve the candidates, axes in tension,
tradeoff, and authorized resolver. A single scalar reward is forbidden.

## Scope boundary

Cycle 243 establishes the selection structure. Cycle 244 will define the exact
conditions under which one mission dominates another.

## Verification

- focused mission tests: 577 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot average away a forbidden mission property or disguise an
unresolved value tradeoff as a numerical winner.
