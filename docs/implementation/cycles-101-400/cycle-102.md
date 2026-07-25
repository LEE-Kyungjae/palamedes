# Improvement Cycle 102

## Topic

A fixed constitution prevents owner imitation but freezes values before
unforeseen contexts appear.

## Deficiency

Cycle 101 can cite a constitutional clause, but no executable rule defines how
that constitution changes. Treating it as immutable blocks learning; allowing
in-place edits lets a model rewrite values conveniently for the current mission.

## Improvement

Added a successor-only constitution revision contract.

A valid revision must:

- increment exactly one version;
- point to the current version as its parent;
- name the trigger sources that exposed insufficiency;
- express clause changes as explicit `add`, `modify`, or `retire` amendments;
- give every amendment a rationale and evidence lineage;
- preserve retirement as retirement rather than hiding replacement text.

## Scope boundary

Cycle 102 permits traceable value evolution. It does not yet solve Cycle 103's
problem of reducing plural worth to a single outcome reward.

## Files

- `palamedes_mission.py`
- `schemas/experimental/constitution-revision.schema.json`
- `tests/test_palamedes_mission.py`

## Verification

- focused mission tests: 10 passed cumulatively
- experimental constitution-revision schema parse: passed
- Python compilation: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot mutate the active constitution in place or skip directly to a
convenient version. Value change must appear as a sourced successor revision.

## Next

Cycle 103 must prevent measurable outcome rewards from replacing plural,
unmeasured beneficiary values.
