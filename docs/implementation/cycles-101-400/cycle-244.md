# Improvement Cycle 244

## Topic

Prove mission dominance under shared assumptions.

## Deficiency

Calling one mission dominant can hide a tradeoff or compare incommensurable
estimates. Dominance requires a common assumption set and a strict no-worse
test, not a persuasive overall impression.

## Improvement

Added `validate_shared_assumption_mission_dominance` and an experimental schema.

Exactly two candidates are normalized to one assumption set across
constitutional fit, beneficiary consequence, evidence strength, reversibility,
and resource efficiency. One dominates only when it is no worse on every axis
and strictly better on at least one. Equal or cross-trading candidates remain
non-dominated, and declared winner and loser must match the computation.

## Scope boundary

Cycle 244 defines dominance after normalization. Cycle 245 will handle the
common case where candidates start from different assumptions.

## Verification

- focused mission tests: 581 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes eliminates a mission by dominance only through a reproducible
five-axis comparison under the same assumptions.
