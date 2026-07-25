# Improvement Cycle 304

## Topic

Keep signal state strictly observational.

## Deficiency

A signal that embeds interpretation, recommendation, mission, or authority can
smuggle a source's incentives directly into purpose. Downstream reasoning then
appears autonomous while merely obeying a semantically overloaded event.

## Improvement

Added `validate_observational_signal_state` and an experimental schema.

A signal records source identity, observation method, observation, baseline,
deviation, affected entities, bounded uncertainty and its note, source
incentives, sensitivity, and received time. Its epistemic kind is strictly
`observation`. It cannot interpret meaning, recommend action, assign a mission,
authorize action, or change the constitution.

## Scope boundary

Cycle 304 defines only what was observed. Cycle 305 will represent constitution
state as structured governed records rather than one editable prompt.

## Verification

- focused mission tests: 821 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every purpose-forming process starts from evidence whose descriptive content is
separable from the values, meaning, mission, and authority later applied to it.
