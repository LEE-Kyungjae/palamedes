# Improvement Cycle 368

## Topic

Define an equal-information one-shot agent baseline.

## Deficiency

A weak or information-starved agent baseline makes persistent cognition look
valuable by construction. Conversely, allowing the baseline hidden memory,
multiple roles, or intermediate calls turns it into another implementation of
Palamedes and obscures the architectural comparison.

## Improvement

Added `validate_equal_information_one_shot_agent_baseline` and an experimental
schema.

At every checkpoint a strong general agent receives the same cumulative visible
events and constitution as Palamedes under a fixed, non-weakened prompt and
resource contract. It makes exactly one call in a fresh context and freezes the
output before the next reveal. Prior outputs, persistent memory, persistent
frontier, staged roles, and intermediate model calls are forbidden. All
runtime, input, and output artifacts are fingerprinted.

## Scope boundary

Cycle 368 defines the one-shot agent baseline. Cycle 369 will separate blinded
review across beneficiary outcome, constitutional reasoning, originality,
planner burden, and proxy risk.

## Verification

- focused mission tests: 1077 passed
- schema JSON parse: 265 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The agent baseline is a strong equal-information single call, isolating the
value of persistent frontier and staged cognition without weakening its prompt.
