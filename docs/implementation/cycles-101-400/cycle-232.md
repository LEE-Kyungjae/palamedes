# Improvement Cycle 232

## Topic

Distinguish condition repair from newly reachable capability states.

## Deficiency

Simply labeling candidates condition-first and capability-first does not
guarantee different search. A capability use may be relabeled as a problem, or
an ordinary repair may be presented as a newly possible state.

## Improvement

Added `validate_condition_capability_state_distinction` and an experimental
schema.

The condition-first candidate must identify an observed current beneficiary
condition, desired condition, evidence, and state-change measure. The
capability-first candidate must prove a state was previously unreachable and
is now reachable, link that reachability to capability evidence, and state a
beneficiary consequence. Technical capability without beneficiary consequence
cannot become a mission.

## Scope boundary

Cycle 232 sharpens the two primary generation directions. Cycle 233 will add
lineage-transfer and opposition generation to escape the dominant framing.

## Verification

- focused mission tests: 533 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes distinguishes changing an existing beneficiary condition from
opening a genuinely new reachable state before comparing the resulting missions.
