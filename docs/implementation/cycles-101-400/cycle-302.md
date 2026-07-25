# Improvement Cycle 302

## Topic

Reuse kernel lifecycle semantics without duplicating purpose objects.

## Deficiency

Semantic separation could create a second persistence universe with subtly
different revision, fingerprint, restore, conflict, and provenance behavior.
That duplication would weaken recovery and make cross-domain lineage unreliable.

## Improvement

Added `validate_shared_kernel_lifecycle_adapter` and an experimental schema.

Observation, interpretation, mission, and execution-plan domains bind to one
adapter exposing the kernel's atomic write, fingerprint, optimistic conflict,
revision append, revision restore, and provenance metadata services. Each
domain supplies only a distinct semantic validator. Private lifecycle stores,
an independent purpose database, and untyped plan fields are prohibited.

## Scope boundary

Cycle 302 shares lifecycle mechanics while preserving Cycle 301's semantic
separation. Cycle 303 will place new typed epistemic objects inside this common
revision envelope.

## Verification

- focused mission tests: 813 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Purpose states differ in meaning and validation, not in the mechanics that make
their revisions atomic, conflict-aware, recoverable, and attributable.
