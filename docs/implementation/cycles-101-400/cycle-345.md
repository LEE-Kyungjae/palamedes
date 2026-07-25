# Improvement Cycle 345

## Topic

Review non-dominated candidates by adversarial axes and sensitivity.

## Deficiency

An aggregate numerical score hides which value tradeoff, failure mode, or
uncertain assumption controls a choice. Non-dominated candidates are precisely
the cases where such plural differences matter.

## Improvement

Added `validate_adversarial_axis_sensitivity_review` and an experimental schema.

Every non-dominated candidate receives every registered adversarial axis.
Each review records the adversarial question, finding, supporting and opposing
evidence, worst credible condition, and observable failure signal. A sensitivity
range names the controlling assumption, low/high bounds, outcomes at both,
selection-flip threshold, and fragility. Ranges remain visible to the selector.
Aggregate scores and collapsed tradeoffs are forbidden.

## Scope boundary

Cycle 345 exposes plural tradeoffs and fragility. Cycle 346 will turn a single
selection-controlling uncertain assumption into a probe with precommitted result
branches.

## Verification

- focused mission tests: 985 passed
- schema JSON parse: 242 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes selects among non-dominated missions from explicit axes and
sensitivity, never from an opaque scalar total.
