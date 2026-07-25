# Improvement Cycle 261

## Topic

Maintain a frontier of unresolved value-relevant uncertainties and active
mission assumptions.

## Deficiency

Rerunning every purpose generator on every event wastes cognition and repeatedly
reopens settled questions. Ignoring events entirely is also unsafe because the
few uncertainties and assumptions that still determine mission validity can
change.

## Improvement

Added `validate_purpose_uncertainty_frontier` and an experimental schema.

The frontier must contain both unresolved value uncertainty and an active
assumption belonging to the current mission. Every entry links a claim,
relevance, evidence, last test, next discriminating observation, wake
condition, and bounded priority. Resolved or inactive entries move to a
disjoint archive. A full generator rerun on every event is explicitly
forbidden.

## Scope boundary

Cycle 261 defines what runtime purpose cognition watches. Cycle 262 will define
the six event classes that can wake it.

## Verification

- focused mission tests: 649 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes remains attentive to the unresolved beliefs that matter without
reconstructing its entire purpose process for every incoming event.
