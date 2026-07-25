# Improvement Cycle 170

## Topic

Integrate separate model revision, counterfactual uncertainty, and purpose
retirement.

## Deficiency

Cycles 161–169 introduced causal attribution, failure-layer separation,
alternative forecasts, signal trajectories, consequence cadence, purpose
retirement, causal uncertainty, and evidence-weighted updates separately. They
still lacked one gate proving that an outcome-learning cycle used them together.

## Improvement

Added `validate_learning_thesis_gate` and an experimental schema.

The gate links all preceding learning records, requires distinct world, value,
and mechanism update IDs, preserves counterfactual uncertainty, and prohibits
collapsing the three model classes. When the underlying purpose is complete,
both the purpose and the learning decision must retire it.

## Scope boundary

Cycle 170 completes the learning thesis. Cycle 171 begins the handoff thesis by
preventing mission contracts from prescribing detailed execution shape.

## Verification

- focused mission tests: 285 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes learns through separate world, value, and mechanism revisions while
preserving counterfactual uncertainty and retiring purposes that are complete.
