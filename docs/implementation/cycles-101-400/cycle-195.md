# Improvement Cycle 195

## Topic

Require insight to change the mission landscape.

## Deficiency

An observation could be labeled an insight because it sounded surprising even
when it created, removed, sequenced, or reprioritized no worthwhile purpose.

## Improvement

Added `validate_insight_mission_landscape_change` and an experimental schema.

An insight binds evidence and distinct before-and-after landscape fingerprints
to at least one typed create, remove, sequence, or reprioritize operation. Each
operation names affected missions, states, reason, and evidence. Removed missions
must retain lineage. Interesting commentary without landscape change is
explicitly insufficient.

## Scope boundary

Cycle 195 connects insight to mission choice. Cycle 196 will define the atomic
Palamedes loop from mismatch observation through consequence learning.

## Verification

- focused mission tests: 385 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

An insight is real only when it changes which worthwhile missions are reachable,
removed, ordered, or prioritized.
