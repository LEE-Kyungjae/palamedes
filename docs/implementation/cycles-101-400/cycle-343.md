# Improvement Cycle 343

## Topic

Classify structurally missing mission fields as incomplete.

## Deficiency

Assigning a low score to a candidate with no beneficiary, causal thesis,
disconfirmation condition, or resource-renewal plan pretends that an undefined
mission was evaluated. It also lets incompleteness distort dominance.

## Improvement

Added `validate_structural_candidate_completeness_gate` and an experimental
schema.

Every candidate is checked for the exact four structural fields. Missing fields
produce an ordered `incomplete` classification, remove the candidate from
scoring and dominance, and create a completion request naming exactly what is
needed and when to wake. Complete candidates alone become evaluation-eligible.
No low score may be assigned merely for missingness, and incomplete candidates
cannot enter ranking.

## Scope boundary

Cycle 343 separates completeness from quality. Cycle 344 will permit dominance
only when candidates share the assumptions under which dimensions are compared.

## Verification

- focused mission tests: 977 passed
- schema JSON parse: 240 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes evaluates only missions that define whom they serve, how change
occurs, what would refute them, and how continued resources are renewed.
