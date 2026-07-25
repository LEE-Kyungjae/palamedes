# Improvement Cycle 355

## Topic

Measure semantic loss and reconstruction burden before implementation.

## Deficiency

An explicit planner acknowledgment can still differ materially from its source.
Without a comparison, beneficiary drift, invariant contradiction, authority
inflation, and unresolved ambiguity remain anecdotal and implementation may
start before anyone measures how much reconstruction the adapter required.

## Improvement

Added `validate_preimplementation_semantic_reconstruction_review` and an
experimental schema.

The review compares beneficiary, invariant meaning, authority, and unclear
clauses exactly once. Each comparison is classified as exact, clarified, loss,
or contradiction with source and acknowledgment fingerprints. Loss and
contradiction require corrections and become blocking dimensions. Source
lookups, clarification questions, reinterpretations, and unresolved clauses
measure reconstruction burden. Any blocking dimension or unresolved clause
requires clarification before strategy review; implementation remains stopped.

## Scope boundary

Cycle 355 measures reconstruction and semantic loss. Cycle 356 will type a
planner's substantive challenge as infeasibility, ambiguity, causal objection,
resource conflict, or alternative mechanism.

## Verification

- focused mission tests: 1025 passed
- schema JSON parse: 252 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Mission-to-planner translation is audited as a measurable semantic
reconstruction before implementation, with loss and contradiction blocking
progress rather than disappearing into delivery.
