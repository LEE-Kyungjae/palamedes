# Improvement Cycle 164

## Topic

Constrain hindsight with pre-selection alternative forecasts.

## Deficiency

Even with pre-structured attribution, Palamedes could explain the observed
result using only the selected mission's story. The outcomes of rejected
missions are unobservable, leaving retrospective reasoning weakly constrained.

## Improvement

Added `validate_preselection_alternative_forecasts` and an experimental schema.

At least three mission candidates now forecast outcomes, causal predictions,
failure signals, and probability ranges under one information manifest and
observation window. The set is frozen before selection, contains exactly one
winner and at least two preserved alternatives, and cannot claim that
counterfactual outcomes were observed.

## Scope boundary

Cycle 164 preserves competing forecasts before selection. Cycle 165 will inspect
the granular movement, invariance, and timing of observed signals.

## Verification

- focused mission tests: 261 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Outcome learning is constrained by predictions made for both selected and
rejected missions before the winner was known.
