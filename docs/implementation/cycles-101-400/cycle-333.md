# Improvement Cycle 333

## Topic

Counter vocabulary lock-in in retrieval.

## Deficiency

Similarity retrieval preferentially returns documents using the current
language. That reinforces the active frame even when contradictory evidence,
past failure, a distant mechanism, or an excluded beneficiary would be more
decision-relevant.

## Improvement

Added `validate_anti_vocabulary_lockin_retrieval_slots` and an experimental
schema.

Every context plan now includes exactly four independently budgeted slots:
counter-view contradiction search, failure-archive search, cross-domain
mechanism search, and beneficiary-gap search. Each records its own question,
scope, query fingerprint, inclusion criterion, attempt, and results. No slot may
be reduced to lexical similarity or require the current vocabulary, and one
global similarity ranking cannot control them all.

## Scope boundary

Cycle 333 requires all four searches to be attempted. Cycle 334 will preserve an
empty result as meaningful evidence rather than silently dropping the slot.

## Verification

- focused mission tests: 937 passed
- schema JSON parse: 230 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Retrieval must deliberately seek evidence that the current vocabulary is least
likely to retrieve by similarity alone.
