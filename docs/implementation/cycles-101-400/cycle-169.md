# Improvement Cycle 169

## Topic

Scale model updates by relevance and causal identification.

## Deficiency

Large financial outcomes or emotionally powerful events could create strong
belief updates even when the evidence was only indirectly relevant or weakly
identified the proposed cause.

## Improvement

Added `validate_evidence_weighted_model_update` and an experimental schema.

Each update targets one world, value, or mechanism claim and records relevance,
causal identification, their rationales, and the prior and proposed belief.
Update strength cannot exceed either relevance or identification strength.
Emotional salience and financial magnitude remain visible but are explicitly
forbidden from driving the update.

## Scope boundary

Cycle 169 governs update strength for one target claim. Cycle 170 will integrate
the learning thesis by requiring separate world, value, and mechanism revisions,
counterfactual uncertainty, and completed-purpose retirement.

## Verification

- focused mission tests: 281 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

The force of an outcome cannot outweigh what its evidence actually identifies
about the particular belief being revised.
