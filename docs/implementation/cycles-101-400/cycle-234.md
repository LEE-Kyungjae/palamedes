# Improvement Cycle 234

## Topic

Generate missions through timing and no-mission counterfactuals.

## Deficiency

Mission generation can treat immediate action as the only meaningful response
and assume a proposed mission is necessary. It then misses the value of
waiting, sequencing dependencies, expiring windows, and existing recovery.

## Improvement

Added `validate_temporal_counterfactual_mission_generation` and an experimental
schema.

Temporal generation must represent wait, sequence, and act-before-expiry
options with timing conditions, predicted consequences, and evidence. The
no-mission counterfactual states what worsens, for whom, over what horizon, and
tests the claim after accounting for an alternative recovery path rather than
assuming mission necessity.

## Scope boundary

Cycle 234 adds temporal and counterfactual generation. Cycle 235 will isolate
generator contexts and reference slices to prevent shared hidden taste.

## Verification

- focused mission tests: 541 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes generates missions from timing structure and demonstrated
counterfactual worsening instead of assuming immediate action and necessity.
