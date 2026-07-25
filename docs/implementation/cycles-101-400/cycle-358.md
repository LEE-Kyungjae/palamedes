# Improvement Cycle 358

## Topic

Invalidate dependent strategies on mission revision.

## Deficiency

The earlier invalidation contract notifies downstream artifacts, but a planner
strategy can still continue if its exact mission dependency is not fingerprinted
or if a replacement becomes active without explicit acceptance of the revised
mission. That produces silent plan drift under a stale purpose.

## Improvement

Added `validate_strategy_revision_acceptance_invalidation` and an experimental
schema.

Every active strategy version names the predecessor mission fingerprint and
becomes invalidated, notified, and non-executable when that mission is revised.
The planner must explicitly accept the successor ID, version, and fingerprint,
reconfirm its invariants, resolve all unclear clauses, and name every
superseded strategy. Only a replacement strategy bound to that successor and
acceptance record may become active.

## Scope boundary

Cycle 358 closes mission-to-strategy revision continuity. Cycle 359 will return
outcome events against mission signals rather than treating task completion or
planner success as beneficiary consequence.

## Verification

- focused mission tests: 1037 passed
- schema JSON parse: 255 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A mission revision makes stale strategies non-executable, and strategy resumes
only after the planner explicitly accepts the exact revised mission.
