# Improvement Cycle 209

## Topic

Wake only when cognition could change a mission.

## Deficiency

An unusual or intellectually interesting event can consume attention without
changing a beneficiary, desired outcome, mechanism, constraint, or stop
condition. Waking on interestingness would turn Palamedes into a novelty feed
rather than an upstream decision agent.

## Improvement

Added `validate_mission_cognition_wake` and an experimental schema.

The wake decision names candidate changes to specific mission dimensions and
records the signal-to-revision link. It scores each candidate from mission
change probability, consequence magnitude, and cognition leverage. The wake or
wait result must follow the highest mission-change score and an explicit
threshold; interestingness is never sufficient.

## Scope boundary

Cycle 209 governs whether cognition is worth starting. Cycle 210 will integrate
the complete signal thesis across value-relevant deviations, consequential
anomalies, model failures, and observation blind spots.

## Verification

- focused mission tests: 441 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes spends cognition on signals capable of changing a mission, not on
events that are merely surprising or interesting.
