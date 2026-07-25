# Improvement Cycle 155

## Topic

Prove upstream cognition beyond supplied-signal planning.

## Deficiency

Cycle 154 compares system complexity, but a full Palamedes workflow could appear
better through polished ceremony while deriving the same mission a simple
planner could infer from supplied signals.

## Improvement

Added `validate_upstream_cognition_evidence` and an experimental schema.

The evaluation fixes supplied signals and records simple-planner and Palamedes
outputs under blind comparison. Palamedes must add autonomously discovered
signals, new hypotheses, and a frame transition; the same mission cannot be
inferable from supplied signals. Ceremony is explicitly not cognition, and a
simplification action is precommitted if the test fails.

## Scope boundary

Cycle 155 isolates upstream cognitive value. Cycle 156 must prevent Palamedes
from optimizing superficial artifacts merely to win benchmark preference.

## Verification

- focused mission tests: 225 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes earns its role only by discovering consequential signals, hypotheses,
or frames that were not already supplied to an ordinary planner.
