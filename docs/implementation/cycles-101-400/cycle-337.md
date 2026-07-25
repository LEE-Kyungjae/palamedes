# Improvement Cycle 337

## Topic

Bind generated artifacts to identifier-and-hash context manifests.

## Deficiency

An output can change because its evidence changed, its model changed, or both.
Without exact input and runtime manifests, later reproduction cannot identify
which source of change produced the divergence.

## Improvement

Added `validate_generated_artifact_context_manifest` and an experimental schema.

Every generated artifact is bound to an ordered context manifest containing
artifact identifiers, types, content and representation fingerprints, and
provenance IDs without raw content. A separate runtime manifest records
provider, model, version, configuration, prompt template, and role assignment.
Baseline/current context and model hashes deterministically classify reproduction
as evidence change, model change, both, or neither.

## Scope boundary

Cycle 337 establishes reproducible input identity. Cycle 338 will allocate
context tokens toward primary observation, constitutional conflict, and rival
mechanisms before narrative background.

## Verification

- focused mission tests: 953 passed
- schema JSON parse: 234 schemas parsed
- `git diff --check`: passed

## Resulting invariant

No generated artifact exists without enough hashed input and runtime identity to
separate evidence drift from model drift.
