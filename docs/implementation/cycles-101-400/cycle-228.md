# Improvement Cycle 228

## Topic

Require interpretations to change options or probes.

## Deficiency

An interpretation can sound insightful while leaving both the mission option
set and next investigation unchanged. Keeping it in active decision state
confuses accumulated background knowledge with operational cognition.

## Improvement

Added `validate_interpretation_operational_relevance` and an experimental
schema.

The validator compares mission-option identifiers before and after the
interpretation and compares prior and next probes. Declared change flags must
match those states. If either changes, the interpretation is operational and
must state its decision effect. If neither changes, it is classified and
archived as background knowledge.

## Scope boundary

Cycle 228 governs interpretation relevance. Cycle 229 will shrink model
complexity after a decision while retaining only monitoring, disconfirmation,
and reconstruction relations.

## Verification

- focused mission tests: 517 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes promotes an interpretation into active decision state only when it
changes a reachable mission option or the next information-producing probe.
