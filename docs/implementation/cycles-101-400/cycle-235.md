# Improvement Cycle 235

## Topic

Isolate generator contexts before candidate comparison.

## Deficiency

Different generation methods can reproduce one hidden taste when they share
the same prompt context, reference slice, or previously generated candidates.
Apparent diversity then reflects labels rather than independent search.

## Improvement

Added `validate_isolated_generator_contexts` and an experimental schema.

Condition-first, capability-first, lineage-transfer, opposition, temporal, and
no-mission-counterfactual generators each receive a unique sealed context and
non-overlapping reference slice. No generator can see another candidate during
generation. Candidates are revealed simultaneously only after all six contexts
close and then enter a separate comparison context.

## Scope boundary

Cycle 235 governs generation isolation. Cycle 236 will reject activity-shaped
missions and require a changed external condition.

## Verification

- focused mission tests: 545 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes creates genuine search diversity before comparison instead of letting
all generators imitate the same visible preference.
