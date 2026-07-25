# Improvement Cycle 109

## Topic

Assemble plural principles, preferences, prohibitions, uncertainty, and
precedents.

## Deficiency

Cycles 101–108 constrain individual value claims, but Palamedes had no single
inspectable state showing which value-bearing inputs coexist at a decision
point. An implementation could omit an awkward category or hide the plurality
behind a scalar objective.

## Improvement

Added `validate_plural_value_state` and an experimental JSON Schema.

The state requires five non-empty, provenance-bearing components: principles,
preference claims, prohibitions, uncertainties, and precedents. Component IDs
are globally unique. Scalarizing fields such as score, utility, reward,
objective, and weights are rejected.

## Scope boundary

Cycle 109 assembles a value state. Cycle 110 must bind that state to a
revisable, provenance-bearing constitution and define how the two relate.

## Verification

- focused mission tests: 41 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can inspect the full plural value context without pretending it is
one number or silently dropping an inconvenient category.
