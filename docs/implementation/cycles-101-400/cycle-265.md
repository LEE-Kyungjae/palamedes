# Improvement Cycle 265

## Topic

Protect mission lineage races with state fingerprints.

## Deficiency

Two purpose wakes can read the same mission lineage, reason independently, and
write incompatible successors. Action idempotency does not prevent the second
thought from overwriting the first and leaving a lineage that never existed as
a coherent state.

## Improvement

Added `validate_mission_lineage_fingerprint_commit` and an experimental schema.

Each wake records the lineage version and fingerprint it read, the current
stored version and fingerprint, and its direct successor proposal. A commit is
allowed only when both base identifiers still match current state and the
proposal changes the fingerprint. Otherwise it is rejected as stale, the
current lineage remains untouched, and retry from current state is required.

## Scope boundary

Cycle 265 protects concurrent mission-state transitions. Cycle 266 will address
duplicate thought by warning on semantic similarity without automatically
suppressing legitimate revisits.

## Verification

- focused mission tests: 665 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

No Palamedes wake can silently overwrite a mission lineage that changed after
the wake began; concurrent cognition commits through an atomic state
transition.
