# Improvement Cycle 341

## Topic

Replace pairwise ranking with disqualification and dominance first.

## Deficiency

Ranking every pair scales quadratically and can imply transitive preference
across values that are not commensurable. A candidate invalid under a hard
criterion also should not remain in a rhetorical tournament.

## Improvement

Added `validate_disqualification_dominance_decision_structure` and an
experimental schema.

Every candidate first receives evidence-backed disqualification checks. Only
eligible candidates enter dominance analysis. Dominance is valid only when one
candidate is no worse on every registered value dimension and better on at
least one, with evidence per dimension. Disqualified and dominated candidates
are removed; only the ordered non-dominated frontier reaches comparison.
Global pairwise ranking and cross-value transitive inference are forbidden.

## Scope boundary

Cycle 341 defines the stage structure. Cycle 342 will constrain hard
constitutional disqualification and authorized exceptions.

## Verification

- focused mission tests: 969 passed
- schema JSON parse: 238 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes compares only candidates that remain constitutionally eligible and
non-dominated under the full plural-value record.
