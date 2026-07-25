# Improvement Cycle 317

## Topic

Select commitment, exploration, probe, or defer from frozen evidence.

## Deficiency

Forcing every tournament to produce one winner hides genuine uncertainty. It
can turn weak evidence into premature commitment or discard safe opportunities
to learn which candidate is better.

## Improvement

Added `validate_four_mode_mission_selection` and an experimental schema.

Selection consumes at least three frozen candidates, forecasts, and critique
records. It may commit one candidate with a bounded scope, explore a strict
subset with budget and expiry, retain competing candidates in a discriminating
probe with harm controls, or defer with a missing condition and wake trigger.
Candidates remain immutable and critiques remain evidence rather than
authority.

## Scope boundary

Cycle 317 creates a governed selection record. Cycle 318 will require
`issue_mission_contract` to consume that record and its constitutional trace,
with no free-form shortcut.

## Verification

- focused mission tests: 873 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can act, learn, test, or wait according to the strength and shape of
frozen evidence instead of manufacturing certainty for every decision.
