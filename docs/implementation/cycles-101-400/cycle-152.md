# Improvement Cycle 152

## Topic

Bound self-improvement by an external mission.

## Deficiency

Cycle 151 treats self-benefit as conflict, but banning every internal
improvement would prevent capability maintenance and make long-running missions
fragile.

## Improvement

Added `validate_externally_bounded_self_improvement` and an experimental schema.

Self-improvement is permitted only as a dependency of a named external mission
with beneficiary evidence, a counterfactual without the improvement, and a
bound owned independently of Palamedes. Scope, resource limit, expiration,
rollback, success signal, and stop condition are explicit. It cannot become its
own mission or expand authority.

## Scope boundary

Cycle 152 permits bounded maintenance. Cycle 153 must inspect temporal lineage
to detect when self-expansion appeared before beneficiary evidence and was
later rationalized.

## Verification

- focused mission tests: 213 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes may improve itself only to satisfy an externally evidenced mission
dependency under independently controlled bounds.
