# Improvement Cycle 393

## Topic

Package the mission schema and validator bundle first.

## Deficiency

Starting with an autonomous daemon would conceal undefined semantic contracts
behind runtime behavior. It would also grant scheduling and effect authority
before individual purpose-state transitions can be inspected or tested.

## Improvement

Added `build_mission_schema_validator_bundle`,
`validate_mission_schema_validator_bundle`, and an experimental schema.

The bundle verifies seven existing schema-validator pairs covering signal,
constitution, causal sketches, mission candidates, tournament, selected
mission, and outcome return. Missing files or symbols invalidate the bundle.
Its artifact kind is contracts and validators; it explicitly excludes a
daemon, scheduler, background loop, and external-action authority.

## Scope boundary

Cycle 393 fixes the first artifact. Cycle 394 will add explicit commands for
those semantic objects with freeze and lineage invariants.

## Verification

- focused mission tests: 1,177 passed
- schema JSON parse: 290 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes exposes inspectable semantic contracts before it acquires autonomous
runtime behavior.
