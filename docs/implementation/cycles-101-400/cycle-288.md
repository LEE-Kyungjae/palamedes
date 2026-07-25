# Improvement Cycle 288

## Topic

Track human upstream labor required for a viable mission.

## Deficiency

An apparently autonomous result can conceal human framing, clarification,
approval, correction, or rescue. Reporting only model compute or final quality
therefore overstates autonomy and makes conditions economically incomparable.

## Improvement

Added `validate_human_upstream_labor_ledger` and an experimental schema.

Each comparison condition records all five categories through the moment a
viable mission is established. Counts, human seconds, and unique evidence IDs
are reconciled against reported totals. Zero labor must be recorded explicitly,
and later implementation labor is excluded from the upstream measure.

## Scope boundary

Cycle 288 measures the human contribution to mission formation. Cycle 289 will
define explicit experiment failure modes, including hidden human goal injection
and planner reconstruction.

## Verification

- focused mission tests: 757 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Claims that Palamedes replaces upstream human thought must include the complete
measured human labor needed to obtain its viable mission.
