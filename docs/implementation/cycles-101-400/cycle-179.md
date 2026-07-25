# Improvement Cycle 179

## Topic

Version mission revisions and invalidate downstream dependencies.

## Deficiency

A mission revision could overwrite its predecessor or leave strategies and
probes silently operating against obsolete meaning, making the feedback
protocol indistinguishable from untracked plan drift.

## Improvement

Added `validate_mission_revision_invalidation` and an experimental schema.

Every revision names immutable predecessor and distinct successor versions,
evidence, reasons, and changed fields. Each downstream artifact bound to the old
version receives a disposition and delivered notice with a reason. At least one
dependency must be invalidated, while others may require review or be explicitly
confirmed compatible.

## Scope boundary

Cycle 179 makes mission revision and dependency impact explicit. Cycle 180 will
integrate the handoff thesis: Palamedes owns purpose coherence, planners own
strategy, and typed evidence crosses the boundary in both directions.

## Verification

- focused mission tests: 321 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Mission meaning changes only through a new traceable version, and no dependent
downstream artifact continues silently against an obsolete contract.
