# Improvement Cycle 233

## Topic

Generate missions through lineage transfer and framing opposition.

## Deficiency

Condition-first and capability-first search can remain trapped inside the same
local vocabulary. They may miss mechanisms already discovered elsewhere and
beneficiaries or states made invisible by the dominant framing.

## Improvement

Added `validate_lineage_opposition_mission_generation` and an experimental
schema.

Lineage transfer names a source condition, mechanism, analogous target
condition, material difference, mission hypothesis, and local probe without
using the source outcome as a forecast. Opposition generation names the
dominant assumption, the hidden beneficiary or condition, why the frame hides
it, supporting evidence, and a failure signal. Opposition must reveal a new
possibility rather than merely negate the dominant mission.

## Scope boundary

Cycle 233 adds lineage and opposition generation. Cycle 234 will add temporal
and no-mission counterfactual generation.

## Verification

- focused mission tests: 537 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can leave the dominant local frame by transferring a mechanism from
another lineage and by generating from what the current framing cannot see.
