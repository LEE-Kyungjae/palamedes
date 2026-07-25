# Improvement Cycle 352

## Topic

Map mission semantics into explicit planner fields.

## Deficiency

A planner adapter can preserve a source link while still putting arbitrary
content into familiar fields. A delivery proxy can become the goal, activity
can masquerade as success, harms can disappear, causal claims can become
untraceable prescriptions, and non-goals can be dropped.

## Improvement

Added `validate_mission_semantic_planner_field_mapping` and an experimental
schema.

The mission outcome maps exactly to the planner goal. Every success signal maps
once to a success metric, every harm signal to a harm metric, the causal thesis
to a causal constraint, and every non-goal to an explicit exclusion. Text,
source pointers, and value fingerprints must match their source semantics.
Coverage must be complete and exact. Task and implementation-sequence fields
remain empty.

## Scope boundary

Cycle 352 defines semantic compilation. Cycle 353 will prevent the adapter from
automatically generating tasks and crossing into planner-owned execution form.

## Verification

- focused mission tests: 1013 passed
- schema JSON parse: 249 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Planner-compatible fields are traceable projections of distinct mission
semantics, not convenient places to invent delivery goals or hide harms and
exclusions.
