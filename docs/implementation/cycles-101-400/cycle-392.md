# Improvement Cycle 392

## Topic

Reuse existing infrastructure around semantic cognition.

## Deficiency

Reimplementing revision storage, fingerprints, restore, providers, reference
retrieval, or benchmarks would add incompatible state and failure semantics.
Calling every integration “new intelligence” also hides that Palamedes' actual
new value is semantic state and the order in which cognition changes it.

## Improvement

Added `build_semantic_infrastructure_reuse_manifest`,
`validate_semantic_infrastructure_reuse_manifest`, and an experimental schema.

The manifest verifies actual repository paths and symbols for revision,
fingerprint, restore, provider, reference, and benchmark capabilities. Each is
bound as reused with no replacement. New implementation scope is exactly
`semantic_state` and `cognition_order`; parallel stores or stacks and an
autonomous daemon are forbidden.

## Scope boundary

Cycle 392 fixes the reuse boundary. Cycle 393 will package the first code
artifact as mission schemas and validators rather than an autonomous daemon.

## Verification

- focused mission tests: 1,173 passed
- schema JSON parse: 289 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes adds semantic cognition where it is genuinely new and inherits
existing operational machinery where it is already adequate.
