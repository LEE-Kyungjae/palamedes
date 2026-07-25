# Improvement Cycle 332

## Topic

Assemble context from bounded decision anchors.

## Deficiency

A context budget limits volume but does not determine relevance. Starting from
global similarity can still retrieve vocabulary-rich material unrelated to the
live purpose decision.

## Improvement

Added `validate_decision_anchored_context_assembly` and an experimental schema.

Assembly must begin from exactly five anchors: the wake reason, relevant
constitution scope, affected beneficiary, active mission frontier, and bounded
lineage neighborhood. Each anchor records its source, fingerprint, selection
question, scope, and selected artifacts. Lineage traversal is capped at three
hops. The final manifest must equal the exact union selected by all anchors and
prove coverage of each one after the leakage guard passes.

## Scope boundary

Cycle 332 defines the starting coordinates for context. Cycle 333 will pressure
retrieval similarity's tendency to favor existing vocabulary.

## Verification

- focused mission tests: 933 passed
- schema JSON parse: 229 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Context is assembled outward from the live governed decision, not inward from
whatever repository text happens to resemble the current wording.
