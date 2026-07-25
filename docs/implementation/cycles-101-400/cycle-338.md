# Improvement Cycle 338

## Topic

Prioritize decision-bearing evidence in context token budgets.

## Deficiency

An undifferentiated token budget can spend most capacity explaining background
while truncating the observation, constitutional conflict, or rival mechanism
that could change the decision.

## Improvement

Added `validate_decision_evidence_token_priority` and an experimental schema.

Context allocation now has four ordered categories: primary observation,
constitutional conflict, rival mechanism, and narrative background. The first
three must receive at least 75% of total capacity; background receives at most
15%. Each allocation records requested and granted tokens, artifacts, basis,
and truncation effect. If pressure requires truncation, background is removed
first and primary observation last. Equal category allocation is not required.

## Scope boundary

Cycle 338 controls token priority. Cycle 339 will treat summaries as
interpretations with provenance and prevent them from silently replacing raw
evidence in high-consequence selection.

## Verification

- focused mission tests: 957 passed
- schema JSON parse: 235 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Narrative completeness cannot consume the capacity required for evidence that
can alter a mission judgment.
