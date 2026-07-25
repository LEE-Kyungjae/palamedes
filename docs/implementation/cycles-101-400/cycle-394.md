# Improvement Cycle 394

## Topic

Define semantic commands with freeze and lineage invariants.

## Deficiency

Schemas alone do not prevent callers from creating objects out of order,
rewriting a prior artifact, or attaching a contract to an unrelated candidate
set. Generic CRUD also erases the difference between semantic transitions and
execution commands.

## Improvement

Added `apply_semantic_command`, `run_semantic_command_sequence`,
`validate_semantic_command_freeze_lineage`, and an experimental schema.

Signal and constitution commands create independent frozen bases. Sketches
must reference both in order; candidates reference sketches, tournament
references candidates, contract references tournament, and outcome references
contract. IDs are immutable and unique, existing stages cannot be rewritten,
and every parent must already exist and be frozen. The surface emits no
execution command.

## Scope boundary

Cycle 394 defines explicit commands. Cycle 395 will wrap them in a
provider-neutral `MissionCycle` orchestrator exercised first with static
fixtures.

## Verification

- focused mission tests: 1,181 passed
- schema JSON parse: 291 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Every semantic command creates one frozen artifact whose authority and meaning
are reconstructable from an explicit prior lineage.
