# Improvement Cycle 223

## Topic

Earn causal complexity through decision relevance.

## Deficiency

Actors, incentives, constraints, mechanisms, and feedback loops can make a
causal sketch sound sophisticated without improving a decision. Unbounded
detail increases confidence and cost while concealing which assumptions matter.

## Improvement

Added `validate_decision_relevant_causal_complexity` and an experimental schema.

The review requires all five causal component types but gives the sketch a
component budget. Every component must identify evidence, its decision
relevance, the branch it changes, and what is lost if removed. A component
whose removal leaves the decision unchanged is rejected, as is decorative
complexity.

## Scope boundary

Cycle 223 governs the complexity admitted into a causal sketch. Cycle 224 will
lower mission authority and prefer a probe when evidence is merely
correlational.

## Verification

- focused mission tests: 497 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes spends causal complexity only on elements that can change a concrete
decision branch and prunes explanatory decoration.
