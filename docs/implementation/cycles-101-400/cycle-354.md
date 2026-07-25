# Improvement Cycle 354

## Topic

Require explicit planner acknowledgment of mission interpretation.

## Deficiency

A generic “understood” acknowledgment does not reveal what a planner thinks the
mission means. Beneficiary substitution, changed invariants, assumed authority,
or ambiguous clauses can remain hidden until tasks and implementation make the
misunderstanding expensive.

## Improvement

Added `validate_explicit_planner_mission_acknowledgment` and an experimental
schema.

Before strategy, the planner restates the beneficiary and desired external
condition with source-clause provenance, names the invariant mission meaning,
and states the exact authority it assumes. Allowed and forbidden actions are
bounded and disjoint. Unclear clauses carry their ambiguity, clarifying
question, and strategy effect. If none are found, the planner must explicitly
justify that result rather than omit the field.

## Scope boundary

Cycle 354 materializes the planner's reconstruction. Cycle 355 will compare it
with the source contract to measure semantic loss and reconstruction burden
before implementation.

## Verification

- focused mission tests: 1021 passed
- schema JSON parse: 251 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Planner acknowledgment is an inspectable reconstruction of beneficiary,
meaning, authority, and ambiguity, not a ceremonial receipt.
