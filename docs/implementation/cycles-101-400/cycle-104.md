# Improvement Cycle 104

## Topic

Plural values can make missions genuinely incomparable. Palamedes must not hide
that uncertainty by forcing a total ranking.

## Deficiency

Cycle 103 preserves separate beneficiary and harm dimensions, but no comparison
contract prevents a selector from converting conflicting dimensions back into a
winner, score, or rank.

## Improvement

Added an experimental partial-order mission comparison contract.

It:

- forbids `rank`, `score`, and `winner` shortcuts;
- compares missions separately on plural consequence dimensions;
- accepts dominance only when one side is never worse or unknown and is better
  on at least one dimension;
- requires `incomparable` when dimensions conflict or remain unknown;
- permits `equivalent` only when every observed dimension is equal.

## Scope boundary

Cycle 104 preserves incomparability. It does not yet choose what to do when two
missions remain incomparable; that is Cycle 105.

## Files

- `palamedes_mission.py`
- `schemas/experimental/plural-mission-comparison.schema.json`
- `tests/test_palamedes_mission.py`

## Verification

- focused mission tests: 19 passed cumulatively
- experimental plural-comparison schema parse: passed
- Python compilation: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot manufacture a winner when benefit, harm, or another value
dimension conflicts or remains unknown.

## Next

Cycle 105 must choose a reversible, information-producing next action without
pretending the underlying value conflict has been resolved.
