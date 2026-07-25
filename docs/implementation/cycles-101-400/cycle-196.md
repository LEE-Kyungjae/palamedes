# Improvement Cycle 196

## Topic

Enforce the atomic mismatch-to-consequence mission cycle.

## Deficiency

Palamedes had validators for many pieces of purpose formation but could still
invoke them out of order, omit an uncomfortable operation, or break the state
lineage between generation, criticism, selection, and learning.

## Improvement

Added `validate_atomic_mission_cycle` and an experimental schema.

One atomic cycle now contains exactly six linked operations: observe mismatch,
interpret condition, generate missions, attack missions, select an
authority-bounded action, and learn consequence. Every completed operation has
an artifact, evidence, result, and input/output fingerprint; each output becomes
the next input and no step may be skipped.

## Scope boundary

Cycle 196 defines the atomic process. Cycle 197 will distinguish the visible
mission-contract handoff from the persistent model revision that constitutes
the product's intelligence.

## Verification

- focused mission tests: 389 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot claim a complete purpose cycle unless observation, invention,
attack, bounded selection, and consequence learning remain sequentially linked.
