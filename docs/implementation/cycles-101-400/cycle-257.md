# Improvement Cycle 257

## Topic

Attribute disconfirmation to mission, planner, implementation, measurement, or
timing.

## Deficiency

An outcome shortfall can falsely invalidate the mission when the planner chose
the wrong strategy, implementation omitted an essential mechanism,
measurement missed the change, or the observation occurred outside the
expected time range.

## Improvement

Added `validate_disconfirmation_layer_attribution` and an experimental schema.

The record tests exactly five distinct hypotheses: mission, planner,
implementation, measurement, and timing. Each has a discriminating test,
evidence, status, and next action. One supported layer becomes the primary
attribution; multiple supported or unresolved possibilities remain
underdetermined. The mission is disconfirmed only when its own failure is
supported and all four downstream explanations are ruled out.

## Scope boundary

Cycle 257 adapts the earlier general failure-layer diagnosis to the compressed
planner contract and its explicit timing range. Cycle 258 will define planner
freedom and the evidence or scope changes that return authority to Palamedes.

## Verification

- focused mission tests: 633 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes does not confuse a failed observation with failed purpose until
planning, implementation, measurement, and timing have each been tested.
