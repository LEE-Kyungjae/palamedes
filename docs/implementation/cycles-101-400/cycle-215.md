# Improvement Cycle 215

## Topic

Decay learned preference weight without deleting lineage.

## Deficiency

A preference learned under one environment or owner identity can become stale.
Keeping its full operational weight fossilizes old context, while deleting it
hides why earlier decisions were made and prevents later correction.

## Improvement

Added `validate_learned_preference_decay` and an experimental schema.

Decay requires evidence that the environment or owner identity changed. The
new operational weight must equal the original weight multiplied by a
strictly reducing decay factor. The preference statement, original context,
change evidence, rationale, review trigger, and historical lineage remain
present; lineage deletion is forbidden.

## Scope boundary

Cycle 215 governs learned-preference decay. Cycle 216 will keep precedent from
fossilizing bias through scope, analogy, dissent, and invalidation conditions.

## Verification

- focused mission tests: 465 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes reduces the operational force of context-stale preferences without
rewriting or erasing the history from which they arose.
