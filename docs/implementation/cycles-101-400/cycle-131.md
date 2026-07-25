# Improvement Cycle 131

## Topic

Generate mission candidates independently before cross-contamination.

## Deficiency

Cycle 130 admits only defensible opportunities, but sequential mission
generation lets the first candidate establish vocabulary, assumptions, and a
solution frame that anchors every later candidate.

## Improvement

Added `validate_independent_mission_generation` and an experimental schema.

A generation batch requires at least three serious alternatives formed without
peer visibility from distinct evidence slices. Each candidate preserves its own
mission thesis, beneficiary change, and mechanism. Sequential
cross-contamination is forbidden during formation.

## Scope boundary

Cycle 131 protects independent formation. Cycle 132 must normalize sealed
candidates against one common constitutional and resource context before
comparison.

## Verification

- focused mission tests: 129 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes compares alternatives that were genuinely originated from different
evidence frames rather than variations anchored by the first idea.
