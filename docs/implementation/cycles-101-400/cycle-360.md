# Improvement Cycle 360

## Topic

Integrate the bidirectional mission-planner handoff.

## Deficiency

Compilation, acknowledgment, reconstruction review, challenge routing, version
invalidation, and outcome return can each work while their links still break.
A strategy may lose its exact mission dependency or a delivery report may fail
to return against the mission version and signals that authorized it.

## Improvement

Added `validate_bidirectional_mission_planner_handoff_implementation` and an
experimental schema.

The integration requires verified evidence for all nine handoff controls. The
forward dependency binds a mission fingerprint through thin compilation,
semantic mapping, acknowledgment, reconstruction review, and explicit strategy
acceptance. The reverse dependency binds that exact strategy back to the same
mission fingerprint through registered signals and an outcome return to
Palamedes. Early task generation, stale execution, purpose rewriting,
Palamedes implementation control, and delivery-based mission closure are
forbidden.

## Scope boundary

Cycle 360 closes the planner handoff block. Cycle 361 begins external proof
design by rejecting synthetic startup-idea scoring as a test of signal
interpretation or changing purpose.

## Verification

- focused mission tests: 1045 passed
- schema JSON parse: 257 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Mission meaning travels forward into an explicitly accepted strategy, and
beneficiary evidence travels backward from that exact strategy into the same
mission version.
