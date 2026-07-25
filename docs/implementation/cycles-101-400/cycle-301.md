# Improvement Cycle 301

## Topic

Keep purpose states distinct from the existing plan object.

## Deficiency

Reusing `plan.json` for observations, interpretations, and missions would save
types but collapse evidence, meaning, purpose, and execution into one revision
surface. A plan edit could then silently rewrite what was observed or why the
mission exists.

## Improvement

Added `validate_purpose_plan_semantic_separation` and an experimental schema.

Observation, interpretation, mission, and execution plan have unique
namespaces, schemas, semantic roles, and transition authorities. Only the
execution-plan domain may use the existing plan object. Cross-domain movement
uses identifier-only links in both forward lineage and outcome return; embedded
purpose payloads are prohibited.

## Scope boundary

Cycle 301 separates semantic state without discarding the existing plan
implementation. Cycle 302 will reuse the kernel's revision, fingerprint,
restore, and provenance mechanics through shared infrastructure rather than
duplicating them.

## Verification

- focused mission tests: 809 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Execution planning can reuse the mature plan object, but observations,
interpretations, and missions retain independent meaning, storage, and revision
boundaries.
