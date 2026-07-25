# Improvement Cycle 103

## Topic

One measurable outcome reward cannot define whether a mission is worthwhile.

## Deficiency

Cycle 101 requires independent value sources and Cycle 102 permits sourced
constitution evolution, but a mission could still collapse all consequences
into one reward or aggregate score. That would let measurable activity displace
unmeasured beneficiary conditions and harms.

## Improvement

Added an experimental plural-value consequence contract.

It:

- forbids `reward`, `utility`, and `aggregate_score`;
- requires at least two distinct consequence dimensions;
- requires `beneficiary_change`;
- requires `harm` or `sustainability`;
- preserves benefit, cost, and uncertainty directions independently;
- keeps evidence lineage per consequence rather than per total score.

## Scope boundary

Cycle 103 prevents scalar collapse. It does not yet solve Cycle 104's problem of
representing missions that remain genuinely incomparable under plural values.

## Files

- `palamedes_mission.py`
- `schemas/experimental/plural-value-consequences.schema.json`
- `tests/test_palamedes_mission.py`

## Verification

- focused mission tests: 14 passed cumulatively
- experimental plural-value schema parse: passed
- Python compilation: passed
- `git diff --check`: passed

## Resulting invariant

No single reward, utility, or aggregate score can stand in for mission worth.
Beneficiary change and possible harm remain separately inspectable.

## Next

Cycle 104 must preserve incomparability instead of forcing every mission pair
into a total ranking.
