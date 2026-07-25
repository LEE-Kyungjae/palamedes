# Improvement Cycle 249

## Topic

Record the complete mission tournament selection.

## Deficiency

A selected winner is not an auditable decision when its alternatives,
assumptions, constitutional handling, resource consequences, and reversal
conditions live in separate records or disappear after selection.

## Improvement

Added `validate_mission_tournament_selection_record` and an experimental
schema.

One record now names the winner and outcome type, preserves at least one
distinct alternative, identifies every decisive assumption, records the
constitutional review and any authorized conflict disposition, accounts for
winner, preservation, and probe allocations inside a finite budget, and
precommits a reversal trigger that targets a preserved alternative.

## Scope boundary

Cycle 249 makes a completed selection inspectable and reversible. It does not
recompute the tournament. Cycle 250 will integrate commitment, bounded
exploration, and discriminating-probe outcomes without reducing plural values
to one score.

## Verification

- focused mission tests: 601 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

No Palamedes tournament result is just a winner label: the reason, surviving
options, decisive assumptions, constitutional disposition, finite cost, and
conditions for reversal travel together.
