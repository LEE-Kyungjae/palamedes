# Improvement Cycle 239

## Topic

Translate original missions into skeptical beneficiary-change language.

## Deficiency

Creative metaphor can make a mission feel original while obscuring a vague,
ordinary, or internally focused objective. Reviewers may reward the expression
instead of verifying the beneficiary change beneath it.

## Improvement

Added `validate_skeptical_mission_translation` and an experimental schema.

An independent skeptical translator who cannot see the generation context
removes named creative terms and writes a plain mission. Structured beneficiary,
current condition, target condition, outcome measure, and evaluation horizon
must match the original semantics exactly. Any semantic drift fails the
translation even if the plain statement sounds reasonable.

## Scope boundary

Cycle 239 tests mission intelligibility beneath novelty. Cycle 240 will
integrate independent condition, capability, lineage, opposition, temporal, and
counterfactual generation into the invention thesis.

## Verification

- focused mission tests: 561 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes retains an original mission only when its concrete beneficiary change
survives removal of the creative language that introduced it.
