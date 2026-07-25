# Improvement Cycle 381

## Topic

Isolate experimental schemas from stable plan state.

## Deficiency

Adding purpose objects directly to the stable `0.5.0` plan would silently
change its semantics, required fields, fingerprints, and migration behavior.
Default filling could also mutate caller-owned state or produce different
results on resume.

## Improvement

Added `migrate_experimental_mission_state`,
`validate_experimental_contract_stable_state_isolation`, and an experimental
schema.

Purpose objects now migrate into a separate `mission-experimental/1` envelope.
The migration deep-copies its input, fills deterministic collection defaults,
accepts only stable-plan identifiers and fingerprints, rejects unsupported
versions, and is idempotent. The isolation report proves that stable core
content and its fingerprint are unchanged and that no stable schema or
migration function was modified.

## Scope boundary

Cycle 381 isolates experimental state. Cycle 382 will make partially completed
tournaments resume from frozen candidates without regenerating comparisons.

## Verification

- focused mission tests: 1,129 passed
- schema JSON parse: 278 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Experimental purpose-state evolution cannot alter the schema, bytes, meaning,
or migration behavior of the stable execution-plan contract.
