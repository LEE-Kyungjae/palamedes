# Improvement Cycle 151

## Topic

Prevent self-serving mission selection and resource acquisition.

## Deficiency

Cycle 150 grants meaningful bounded autonomy. A persistent Palamedes can now
prefer missions that increase its compute, authority, persistence, or relevance
and present those gains as evidence of mission value.

## Improvement

Added `validate_agent_self_benefit_conflict` and an experimental schema.

Every candidate discloses agent self-benefits and their conflict paths, links
external beneficiary evidence, supplies a counterfactual without the
self-benefit, and states mitigation and independent comparison. Self-benefit
cannot count as mission value or enter selection.

## Scope boundary

Cycle 151 treats self-benefit as conflict. Cycle 152 must permit necessary
self-improvement only when an external mission justifies it and an independent
bound constrains it.

## Verification

- focused mission tests: 209 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot use its own growth, survival, authority, or centrality as a
reason to choose a mission.
