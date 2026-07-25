# Improvement Cycle 323

## Topic

Enforce inventor independence beyond role prompts.

## Deficiency

Two agents with different role prompts can still converge when they receive the
same evidence in the same order or see an existing candidate before generating
their own. The appearance of plurality then hides shared anchoring.

## Improvement

Added `validate_partitioned_inventor_independence` and an experimental schema.

Each inventor receives frozen shared evidence plus a nonempty, pairwise
disjoint exclusive partition with an explicit pressure intent. Assignment,
partition, candidate, and fingerprint provenance are retained. Inventors cannot
see rival IDs or content before freezing, frozen candidates cannot be mutated,
and the reveal event must cover every candidate only after all are frozen.

## Scope boundary

Cycle 323 establishes independent invention. Cycle 324 will determine when one
interpreter may produce several separable causal sketches and when independent
interpretation calls are required.

## Verification

- focused mission tests: 897 passed
- schema JSON parse: 220 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Candidate diversity must arise under documented differences in evidence
pressure, not merely different prompt labels applied after a shared anchor.
