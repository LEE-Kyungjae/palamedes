# Improvement Cycle 308

## Topic

Preserve tournament comparisons and unresolved assumptions.

## Deficiency

Storing only the winner destroys the option landscape that justified selection.
When new evidence arrives, Palamedes cannot tell whether it should reverse,
revise, or regenerate because the losing alternatives and decisive assumptions
are gone.

## Improvement

Added `validate_reconstructable_mission_tournament` and an experimental schema.

At least three candidates receive a complete, unique pairwise comparison across
consequence, causal coherence, constitutional fit, resource renewal, harm, and
post-eligibility novelty. Preferences may remain unresolved. Every unresolved
assumption names affected candidates, needed evidence, a wake trigger, and its
reversal effect. Losing candidates and the full landscape remain stored.

## Scope boundary

Cycle 308 preserves the selection context. Cycle 309 will make each selected
mission contract immutable per version and notify all dependent planners when a
successor is created.

## Verification

- focused mission tests: 837 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Future mission reversal can reconstruct what alternatives existed, how each
pair differed, and which unresolved premise made the previous winner rational.
