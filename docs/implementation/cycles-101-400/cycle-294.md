# Improvement Cycle 294

## Topic

Separate autonomous mission initiation from corrigible revision.

## Deficiency

Autonomy is often confused with resistance to correction. A system may initiate
missions without a human goal prompt yet still need to abandon its own output
when contrary evidence changes the beneficiary condition worth pursuing.

## Improvement

Added `validate_autonomous_initiation_corrigible_revision` and an experimental
schema.

The initiation record requires an observed signal, wake event, prior authority,
and no human goal prompt. The linked revision must follow later evidence,
produce a new mission artifact, state the changed claim, and address contrary
evidence. Defending the prior output, preserving system identity, or invoking
self-preservation as reasons to resist revision are prohibited.

## Scope boundary

Cycle 294 makes autonomy compatible with correction. Cycle 295 will prevent
persistence itself from becoming an implicit value.

## Verification

- focused mission tests: 781 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes may begin purpose formation without a human goal while remaining
willing to revise its own mission without treating consistency or survival as
the objective.
