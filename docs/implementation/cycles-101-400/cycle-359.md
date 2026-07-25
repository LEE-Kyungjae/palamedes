# Improvement Cycle 359

## Topic

Return outcomes against mission signals rather than task completion.

## Deficiency

A planner can complete every task and report delivery success while the
beneficiary condition remains unchanged or harm appears. If delivery status
substitutes for mission evidence, Palamedes learns from internal activity rather
than external consequence.

## Improvement

Added `validate_mission_signal_outcome_return` and an experimental schema.

The return binds the exact mission and strategy versions, registers both
success and harm signals, and observes each signal exactly once with direct
evidence and beneficiary scope. Mission status is supported only when all
success signals are met and all harm signals are clear. Any missed success or
triggered harm produces an adverse-or-unsupported result; unresolved evidence
remains inconclusive. Task completion is reported separately and cannot close
the mission, whose outcome returns to Palamedes.

## Scope boundary

Cycle 359 completes the bidirectional outcome path. Cycle 360 will integrate
the thin traceable compilation, reconstruction measurement, version
dependencies, challenge jurisdiction, and mission-signal return.

## Verification

- focused mission tests: 1041 passed
- schema JSON parse: 256 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Planner delivery and beneficiary consequence are separate records, and only
registered mission signals determine the returned mission outcome.
