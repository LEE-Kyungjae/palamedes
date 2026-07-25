# Improvement Cycle 291

## Topic

Define the preplanning unit as a versioned selected mission.

## Deficiency

An “idea” does not say which conditions produced it, which values constrained
it, who authorized it, what alternatives lost, or whether planning began before
selection. It cannot support accountable revision or causal comparison.

## Improvement

Added `validate_versioned_selected_mission_unit` and an experimental schema.

The preplanning artifact is now a fingerprinted mission version linked to its
previous version, compact mission contract, observed conditions, explicit
values, authority grants, candidate set, and selection record. Version one has
no predecessor; later versions must have one. The selected mission must be an
actual member of a plural candidate set.

## Scope boundary

Cycle 291 changes the unit passed into planning. Cycle 292 will focus
Palamedes's intelligence on selecting the cognitive transformation missing from
the current mission frontier.

## Verification

- focused mission tests: 769 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Planning begins from a governed, reproducible mission decision—not an
unversioned idea with implicit values and unknown authority.
