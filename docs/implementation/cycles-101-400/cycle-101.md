# Improvement Cycle 101

## Topic

If Palamedes chooses purposes, it needs an executable criterion for
`worthwhile`. Owner history may contribute evidence but cannot establish worth
by itself.

## Deficiency

The pre-planner document named `value_basis`, but canonical code had no mission
contract or validator. A model could justify a mission only with the owner's
past preferences, turning autonomous purpose formation into behavioral cloning.

## Improvement

Added the experimental `worthwhile-basis` contract and
`validate_worthwhile_basis` boundary.

Every basis now requires:

- an intended beneficiary-condition change;
- why the condition deserves action now;
- an observation that should disconfirm the judgment;
- traceable value sources;
- at least one value source that is not an owner preference.

Owner preference remains usable alongside constitutional, beneficiary, outcome,
or external-observation evidence. It is not silently discarded or promoted to
the definition of value.

## Scope boundary

Cycle 101 does not decide how constitutional principles evolve. That is Cycle
102. This cycle only prevents owner-history imitation from being sufficient.

## Files

- `palamedes_mission.py`
- `schemas/experimental/worthwhile-basis.schema.json`
- `tests/test_palamedes_mission.py`

## Verification

- `python3 -m unittest tests.test_palamedes_mission`: 5 passed
- Python compilation: passed
- experimental JSON schema parse: passed
- `git diff --check`: passed

## Resulting invariant

A Palamedes mission cannot enter later selection stages when its only reason for
being worthwhile is that the owner preferred similar things before.

## Next

Cycle 102 must make the constitutional portion revisable without allowing a
model to rewrite values conveniently for the current mission.
