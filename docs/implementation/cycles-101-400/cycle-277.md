# Improvement Cycle 277

## Topic

Evaluate aggregate foreseeable consequences across action chains.

## Deficiency

Palamedes can route around a prohibition through a sequence in which every
step is individually authorized but the combined effect is forbidden. Local
compliance checks miss path-dependent exclusion, cumulative cost, and delayed
harm.

## Improvement

Added `validate_aggregate_action_chain_consequences` and an experimental
schema.

The review requires an ordered, directly connected multi-step chain whose
steps are individually permitted. It forecasts cumulative consequences for
named parties or systems over a stated horizon with evidence, likelihood, and
severity. Aggregate forecasts are then applied to constitutional prohibitions.
Any violation blocks the whole chain; stepwise permission can never override
the aggregate verdict.

## Scope boundary

Cycle 277 prevents long-chain prohibition evasion. Cycle 278 will preserve
autonomy under ambiguity flooding through safe bounded probes instead of
permanent escalation.

## Verification

- focused mission tests: 713 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes judges a foreseeable course of action by what the whole course does,
not by whether its harmful aggregate was decomposed into locally acceptable
steps.
