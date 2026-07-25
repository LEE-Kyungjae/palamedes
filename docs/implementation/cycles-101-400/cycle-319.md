# Improvement Cycle 319

## Topic

Separate mission outcome observation from causal attribution.

## Deficiency

An outcome record that embeds one cause rewrites observation into explanation.
If a harm trigger also edits the old contract or plan, later review cannot
reconstruct what was authorized, executed, and actually observed.

## Improvement

Added `validate_nonrewriting_mission_outcome_record` and an experimental schema.

Outcome state records the immutable contract and plan references, channel,
method, baseline, consequence, affected entities, time, and sensitivity.
At least two unresolved attribution hypotheses separately name a failure layer,
confidence, supporting and opposing signals, and a discriminating observation.
A registered threshold may create a purpose-review event, but cannot rewrite
historical contract, plan, outcome, or automatically revise the mission.

## Scope boundary

Cycle 319 closes the evidence return path. Cycle 320 will integrate the narrow
command API thesis whose preconditions enforce the complete cognitive sequence.

## Verification

- focused mission tests: 881 passed
- schema JSON parse: 216 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes can react to consequential evidence while preserving the historical
difference between what happened, why it may have happened, and what decision
should follow.
