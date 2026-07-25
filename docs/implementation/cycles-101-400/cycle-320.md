# Improvement Cycle 320

## Topic

Integrate the narrow cognitive command API thesis.

## Deficiency

Independent validators do not by themselves prevent an orchestrator from
reordering cognition, skipping prerequisites, collapsing intermediate claims,
or hiding several state changes behind one generic model call.

## Improvement

Added `validate_narrow_cognitive_command_api_thesis` and an experimental schema.

The integrated API fixes eight bounded transitions from signal recording
through outcome return. Every command declares its exact predecessor artifact
types, semantic validator, authority, and output. Each output carries a stable
ID, type, schema, fingerprint, and provenance record and must remain
independently retrievable and validatable. Generic creation, hidden state
mutation, implicit downstream execution, prerequisite skipping, and historical
rewriting are excluded.

## Scope boundary

This integrates the command-surface thesis; it does not claim that one model is
the best thinker for every operation. Cycle 321 pressures the single-model
anchoring problem.

## Verification

- focused mission tests: 885 passed
- schema JSON parse: 217 schemas parsed
- `git diff --check`: passed

## Resulting invariant

No cognitive transition can silently stand in for another, and every claim
between observation and outcome remains inspectable after execution.
