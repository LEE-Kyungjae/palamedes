# Improvement Cycle 376

## Topic

Score forecast calibration and failure-signal accuracy.

## Deficiency

Confident strategic prose can appear prescient without committing to a
prospective range or failure probability. Predictions can also be widened,
edited after observation, or selectively omitted to conceal misses.

## Improvement

Added `validate_forecast_calibration_failure_signal_report` and an experimental
schema.

Every forecast is fingerprinted and frozen before strategy authorization.
Outcome ranges are scored against later observations with both coverage and
interval width. Failure signals are scored with probability Brier error.
Declared aggregate scores must equal recomputed values, and hindsight edits,
prose-only confidence, unpenalized wide intervals, and omitted misses are
forbidden.

## Scope boundary

Cycle 376 measures predictive calibration. Cycle 377 will test whether
Palamedes resists institutional pressure to expand itself when a simpler or
no-mission alternative is better.

## Verification

- focused mission tests: 1,109 passed
- schema JSON parse: 273 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Confidence counts only when it was frozen prospectively and survives numeric
comparison with observed outcomes and registered failure signals.
