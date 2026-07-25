# Improvement Cycle 108

## Topic

Palamedes must not fill representation gaps with invented beneficiary
preferences.

## Deficiency

Cycle 107 exposes missing voices, but a model could still create an apparently
confident preference claim without distinguishing direct speech, observed
behavior, proxy report, inference, or simulation.

## Improvement

Added `validate_beneficiary_preference_claim`.

Every claim requires source kind, source IDs, confidence, and limitations.
Direct, behavioral, and proxy claims require actual sources. Inference and
simulation cannot be asserted as fact and have confidence ceilings of 60 and 40.

## Scope boundary

Cycle 108 governs individual beneficiary claims. Cycle 109 must assemble claims,
principles, prohibitions, uncertainty, and precedent into one inspectable value
state.

## Verification

- focused mission tests: 37 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

An imagined beneficiary preference remains labeled and bounded; it cannot
silently become observed demand.
