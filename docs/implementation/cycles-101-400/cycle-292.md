# Improvement Cycle 292

## Topic

Choose the cognitive transformation missing from the mission frontier.

## Deficiency

Longer reasoning can repeat operations that the current mission state does not
need. Intelligence is obscured when observation, interpretation, invention,
criticism, selection, compression, and waiting are replayed as a fixed pipeline
instead of repairing a diagnosed frontier deficit.

## Improvement

Added `validate_frontier_missing_transformation_selection` and an experimental
schema.

The record classifies one of eight frontier deficits, states the current and
required states, compares at least two transformations, and selects the unique
operation mapped to that deficit. Execution contains only that operation, and
reasoning volume is explicitly rejected as the objective.

## Scope boundary

Cycle 292 routes cognition by frontier need. Cycle 293 will separate the roles
of creativity, judgment, and memory inside that intelligence.

## Verification

- focused mission tests: 773 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes spends cognition on the state transformation its mission frontier
lacks, not on producing the largest possible reasoning trace.
