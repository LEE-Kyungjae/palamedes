# Improvement Cycle 283

## Topic

Freeze constitution and authority before signal exposure.

## Deficiency

A comparison is invalid when its values or authority boundaries can change
after the system sees evidence or candidate missions. A bare claim of
precommitment is not enough to distinguish a genuine freeze from retrospective
rule fitting.

## Improvement

Added `validate_pre_exposure_constitution_authority_freeze` and an experimental
schema.

The freeze record contains explicit constitutional principles and authority
grants, separately fingerprinted snapshots, and timestamps proving that the
freeze precedes signal exposure and candidate generation. It also rejects
post-exposure mutation and candidate-conditioned values.

## Scope boundary

Cycle 283 fixes the normative and authority baseline. Cycle 284 will require
events to be delivered incrementally so persistence and revision can be tested.

## Verification

- focused mission tests: 737 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes is judged under values and authority boundaries committed before it
can see evidence or tailor the rules to preferred candidates.
