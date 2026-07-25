# Improvement Cycle 222

## Topic

Maintain bounded competing causal sketches.

## Deficiency

Model plurality can become an excuse to simulate the whole world. Exhaustive
narratives add unverifiable detail, obscure the affected condition, and make
the comparison too expensive to guide a decision.

## Improvement

Added `validate_competing_causal_sketch_set` and an experimental schema.

Each competing model becomes a bounded sketch around a shared affected
condition and decision window. The sketch declares its local boundary,
included factors, deliberately excluded factors, causal path, prediction, and
discriminating observation. At least two distinct paths remain, and exhaustive
world simulation is explicitly forbidden.

## Scope boundary

Cycle 222 establishes bounded sketches. Cycle 223 will require actors,
incentives, constraints, mechanisms, and feedback only when their complexity is
earned by decision relevance.

## Verification

- focused mission tests: 493 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes compares local causal explanations that can change the next decision
instead of hiding uncertainty inside multiple oversized world stories.
