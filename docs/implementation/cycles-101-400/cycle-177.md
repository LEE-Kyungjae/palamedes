# Improvement Cycle 177

## Topic

Arbitrate only conflicts that change mission meaning.

## Deficiency

When multiple planners proposed incompatible strategies, Palamedes could expand
its authority by arbitrating tool, architecture, sequencing, or other technical
tradeoffs that belonged downstream.

## Improvement

Added `validate_strategy_conflict_jurisdiction` and an experimental schema.

Each disagreement is typed as purpose or technical, with evidence and a boundary
test. Any purpose conflict returns to Palamedes. A technical-only conflict
remains with downstream strategy resolution, and Palamedes is explicitly denied
default technical arbitration power.

## Scope boundary

Cycle 177 assigns conflict jurisdiction. Cycle 178 will accumulate repeated plan
failures before allowing them to challenge the mission's feasibility assumption.

## Verification

- focused mission tests: 313 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes arbitrates purpose coherence, not implementation preference; technical
strategy conflicts remain downstream while mission meaning is unchanged.
