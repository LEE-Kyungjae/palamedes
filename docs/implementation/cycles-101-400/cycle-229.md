# Improvement Cycle 229

## Topic

Compress world models after decisions without losing correction state.

## Deficiency

A rich model is useful during comparison but becomes operational debt after a
decision. Keeping every relation active consumes attention; deleting the model
destroys monitoring, falsification, and the ability to reconstruct the choice.

## Improvement

Added `validate_post_decision_model_compression` and an experimental schema.

Pre-decision components must be partitioned exactly into retained relations and
archived removals. The active model must shrink and retain at least one
relation for monitoring, disconfirmation, and reconstruction. Every removal
has a rationale, complete lineage stays archived, and a rehydration trigger
states when removed context returns.

## Scope boundary

Cycle 229 governs post-decision compression. Cycle 230 will integrate the
interpretation thesis around competing falsifiable sketches that alter mission
options rather than constructing a complete worldview.

## Verification

- focused mission tests: 521 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes sheds exploratory model complexity after deciding while preserving
the minimal state needed to monitor, disconfirm, and reconstruct the decision.
