# Improvement Cycle 289

## Topic

Define explicit purpose-comparison failure criteria.

## Deficiency

A flexible success narrative can excuse a generic mission, concealed human goal
injection, proxy harm, constitution theater, planner reconstruction, or no
outcome advantage. Aggregate scoring is especially dangerous when strengths on
other dimensions can offset one of these validity failures.

## Improvement

Added `validate_purpose_comparison_failure_criteria` and an experimental schema.

The protocol freezes exactly six failure types before evaluation. Every type
has an observable test, failure threshold, evidence, independent evaluator, and
finding. Any triggered criterion forces the overall verdict to `fail`; no other
score can compensate for it.

## Scope boundary

Cycle 289 makes disproof binding. Cycle 290 will integrate the minimal
end-to-end proof from signal through mission and outcome, including retired
upstream labor.

## Verification

- focused mission tests: 761 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot claim success by narrating around any of the six precommitted
conditions that invalidate autonomous, beneficial purpose formation.
