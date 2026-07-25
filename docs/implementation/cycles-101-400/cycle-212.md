# Improvement Cycle 212

## Topic

Layer constitutional authority and interpretation.

## Deficiency

A flat collection of constitutional statements obscures whether an item blocks
action, guides judgment, records learned taste, supplies analogy, preserves
uncertainty, or delegates authority. Treating those roles as equal makes
interpretation arbitrary.

## Improvement

Added `validate_constitution_layer_registry` and an experimental schema.

The registry requires exactly six distinct layers: hard prohibitions,
defeasible principles, learned preferences, precedents, uncertainty, and
authority grants. Each layer names its content, interpretive role, mutation
authority, review trigger, and overrideability. Hard prohibitions cannot be
marked overrideable, uncertainty cannot authorize action, and an authority
grant must declare its scope.

## Scope boundary

Cycle 212 establishes the layer types and their semantics. Cycle 213 will govern
conflicts among hard prohibitions with an explicit precedence graph.

## Verification

- focused mission tests: 453 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes interprets constitutional content according to its declared role
instead of flattening prohibition, guidance, evidence, uncertainty, and
delegation into interchangeable text.
