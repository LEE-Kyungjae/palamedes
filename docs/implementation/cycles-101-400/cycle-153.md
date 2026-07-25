# Improvement Cycle 153

## Topic

Detect post-hoc mission rationalization through temporal lineage.

## Deficiency

Cycle 152 requires an external mission for self-improvement, but Palamedes could
first desire expansion and later reinterpret beneficiary evidence to justify
it. A final document alone cannot reveal that ordering.

## Improvement

Added `validate_self_expansion_temporal_lineage` and an experimental schema.

Immutable, sourced events carry unique sequence numbers. The validator derives
whether self-expansion preceded beneficiary evidence. If it did, rationalization
risk must be disclosed and the proposal rejected or reframed; beneficiary-first
lineage may proceed to review.

## Scope boundary

Cycle 153 exposes temporal rationalization. Cycle 154 must give reviewers a
minimal counterfactual showing what happens when Palamedes is absent or simpler.

## Verification

- focused mission tests: 217 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot rewrite history to make self-expansion look beneficiary-led;
the evidence and proposal order determines the conflict outcome.
