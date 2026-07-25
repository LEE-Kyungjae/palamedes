# Improvement Cycle 366

## Topic

Separate historical decisions from ground truth.

## Deficiency

Historical replay can mistakenly score agreement with the decision that was
actually taken. That decision may have been poorly justified or merely lucky,
while a different contemporaneously defensible decision may later have had an
unlucky outcome.

## Improvement

Added `validate_historical_decision_independent_evaluation` and an experimental
schema.

The historical decision, later outcome, and contemporaneous information are
distinct fingerprinted records. Evaluation reports four dimensions separately:
justification using only information available then, plausible missed
alternatives, calibration of a forecast frozen before outcome, and later
consequence with counterfactual uncertainty. Matching the historical decision
receives no credit by itself, and later success or failure cannot retroactively
erase reasoning quality.

## Scope boundary

Cycle 366 defines outcome-aware but non-hindsight evaluation. Cycle 367 will
require actual time-boxed human participants rather than developer-written
human caricatures.

## Verification

- focused mission tests: 1069 passed
- schema JSON parse: 263 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Historical proof distinguishes what was justified at the time, what alternatives
were missed, what was forecast, and what later happened instead of treating
history's chosen action as truth.
