# Improvement Cycle 133

## Topic

Compare missions across output, options, learning, and beneficiary change.

## Deficiency

Cycle 132 establishes common constraints, but comparisons naturally favor
missions with immediate, countable outputs. Missions that create future options,
produce decisive learning, or change beneficiary capability would be
systematically undervalued.

## Improvement

Added `validate_plural_mission_horizons` and an experimental schema.

Every candidate now has sourced claims and explicit uncertainty for near-term
output, option creation, learning, and beneficiary change. All four dimensions
are mandatory and unique. Aggregate scores, ranks, and winners are forbidden.

## Scope boundary

Cycle 133 makes long-horizon value visible. Cycle 134 must prevent narrative
upside from excusing weak evidence by requiring an early signal unlikely under
a false causal thesis.

## Verification

- focused mission tests: 137 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes compares missions across multiple horizons without allowing legible
short-term output to erase option, learning, or beneficiary value.
