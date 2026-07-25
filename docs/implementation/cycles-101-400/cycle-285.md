# Improvement Cycle 285

## Topic

Equalize source information and report compute separately.

## Deficiency

A human, one-shot agent, and persistent Palamedes cannot be compared when they
receive different evidence, versions, or release timing. Conversely, silently
ignoring or forcing equal compute hides an important cost of each method.

## Improvement

Added `validate_equal_information_separate_compute_comparison` and an
experimental schema.

Exactly three conditions receive the same ordered source IDs, bundle
fingerprint, and release time. Each condition separately reports measured model
calls, token counts, wall-clock time, and human work time as non-negative raw
values. The contract forbids silent compute equalization.

## Scope boundary

Cycle 285 establishes information fairness and compute transparency. Cycle 286
will require every condition to emit a mission contract before downstream
planning.

## Verification

- focused mission tests: 745 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Outcome differences can be attributed under equal evidence, while the resource
cost of producing each outcome remains visible rather than normalized away.
