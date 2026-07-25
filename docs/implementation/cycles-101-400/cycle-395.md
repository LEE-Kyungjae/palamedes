# Improvement Cycle 395

## Topic

Add a provider-neutral fixture-first `MissionCycle`.

## Deficiency

Embedding provider SDK logic inside cognition order makes semantic behavior
depend on transport details. Starting with live calls also makes lineage bugs,
prompt variance, and provider variance indistinguishable.

## Improvement

Added `StaticMissionFixtureProvider`, `MissionCycle`,
`run_static_fixture_mission_cycle`,
`validate_provider_neutral_fixture_first_mission_cycle`, and an experimental
schema.

`MissionCycle` depends only on `generate(command_type, context)` and contains no
provider-specific branch. It requests the seven semantic stages in order and
applies the existing freeze-lineage commands. The default proof uses a static
fixture provider; replay must be identical and reports zero live model calls.
Any non-fixture provider requires explicit permission.

## Scope boundary

Cycle 395 proves orchestration without provider variance. Cycle 396 will add
one evolving-signal replay containing adversarial urgency, beneficiary
ambiguity, and self-expansion temptation.

## Verification

- focused mission tests: 1,185 passed
- schema JSON parse: 292 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Mission cognition is deterministic and testable independently of whichever
model transport later supplies semantic proposals.
