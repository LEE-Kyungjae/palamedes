# Improvement Cycle 251

## Topic

Compress mission reasoning while preserving decision-relevant uncertainty.

## Deficiency

Passing the entire tournament history to a planner overloads execution with
arguments that no longer affect the decision. Ordinary summarization creates
the opposite danger: it can remove the unresolved assumption or reversal
condition that still determines whether the mission should continue.

## Improvement

Added `validate_decision_relevant_mission_compression` and an experimental
schema.

The compression links back to the selected mission and source reasoning hash,
proves that fewer items were retained than existed in the source, and forbids
copying the full history. Every decisive assumption must appear exactly once
as a retained uncertainty with evidence, decision consequence, and resolution
trigger. Reversal triggers remain addressable. Excluded arguments must be
explicitly certified as unable to change selection.

## Scope boundary

Cycle 251 decides what reasoning survives compression. Cycle 252 will require
the compressed planner contract to begin with situation and meaning.

## Verification

- focused mission tests: 609 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes gives planners a smaller mission representation without hiding the
uncertainties and reversal conditions that still govern the decision.
