# Improvement Cycle 225

## Topic

Use historical analogy for mechanisms, not forecasts.

## Deficiency

A mechanism that worked historically can become a seductive forecast for a new
setting. Timing, institutions, scale, and beneficiary power can reverse or
erase the old causal relation even when the surface pattern looks similar.

## Improvement

Added `validate_historical_mechanism_analogy` and an experimental schema.

Historical evidence may transfer only a mechanism candidate. The record must
compare historical and current timing, institutional structure, scale, and
beneficiary power and state how each difference affects transfer. Local
evidence, a local probe prediction, and a failure signal are required before
the mechanism gains authority.

## Scope boundary

Cycle 225 governs historical analogy. Cycle 226 will require every live model
to predict observations that would surprise and weaken it.

## Verification

- focused mission tests: 505 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes mines history for mechanisms worth testing while refusing to import
historical outcomes as forecasts for a materially different present.
