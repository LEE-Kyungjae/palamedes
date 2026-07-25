# Improvement Cycle 253

## Topic

Anchor the planner contract in beneficiary and desired external condition.

## Deficiency

Situation and meaning can still be converted into internal delivery success if
the contract leaves “who changes” and “what externally becomes true”
implicit. A deployed service or completed artifact can then replace the
consequence that justified the mission.

## Improvement

Added `validate_beneficiary_external_condition_contract` and an experimental
schema.

The beneficiary must be a represented, directly affected external population
with a stated current condition and recourse channel, not the internal delivery
team. The desired condition names an observable external difference, window,
beneficiary verification method, and evidence source while keeping
implementation form open. Technical outputs may be recorded, but they cannot
count as success without observed beneficiary change.

## Scope boundary

Cycle 253 fixes who must experience what external change. Cycle 254 will
separate the causal mechanism that planners must preserve from implementation
forms they remain free to choose.

## Verification

- focused mission tests: 617 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes planners cannot satisfy a mission by shipping technology alone; the
represented beneficiary must experience the specified observable condition.
