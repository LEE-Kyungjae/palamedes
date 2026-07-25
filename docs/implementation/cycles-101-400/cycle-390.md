# Improvement Cycle 390

## Topic

Integrate fail-closed commitment and open observation.

## Deficiency

A generic fail-closed rule can stop the observations needed to diagnose
failure, while a fail-open rule can commit missions or external effects on
corrupted evidence. Systems can also regain apparent consistency by deleting
the evidence that contradicts their preferred state.

## Improvement

Added `apply_failure_thesis`, `validate_failure_thesis_integration`, and an
experimental schema.

Any unresolved failure closes mission commitment and external-effect gates.
Observation remains open only when it is read-only, bounded, within a
registered operation budget, and covered by observation authority. Every
contradictory evidence record preserves its identity, fingerprint, source, and
challenged claim; evidence deletion cannot repair consistency.

## Scope boundary

Cycle 390 integrates failure behavior. Cycle 391 will implement the vertical
slice inside Palamedes while ending its authority at mission contract and
outcome intake rather than execution.

## Verification

- focused mission tests: 1,165 passed
- schema JSON parse: 287 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Failure closes commitment and effects, not bounded learning or inconvenient
facts.
