# Improvement Cycle 105

## Topic

When plural-value missions remain incomparable, Palamedes should choose a
reversible information-producing action instead of manufacturing a winner.

## Deficiency

Cycle 104 can preserve `incomparable`, but it did not constrain the next action.
A selector could still immediately commit to one mission and thereby convert an
unresolved value conflict into hidden preference.

## Improvement

Added the `incomparable-next-action` contract. It permits only:

- a reversible or partially reversible probe with a named uncertainty,
  rollback, and at least two distinguishing observations; or
- defer with an explicit wake trigger.

The record must state that the value conflict remains unresolved. Irreversible
commitment is rejected.

## Scope boundary

Cycle 105 chooses an information-producing action. Cycle 106 must ensure that
information gain never outranks harm and consent constraints.

## Verification

- focused mission tests: 24 passed cumulatively
- experimental action schema parse: passed
- `git diff --check`: passed

## Resulting invariant

Incomparability can lead to learning or waiting, not an unacknowledged winner.
