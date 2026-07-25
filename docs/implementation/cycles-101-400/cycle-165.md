# Improvement Cycle 165

## Topic

Track moved, invariant, and unexpectedly timed signals.

## Deficiency

Comparing a final outcome with a binary success threshold discarded near misses,
unchanged indicators, and signals that arrived earlier or later than forecast.
Those details carry more calibration information than a pass/fail label.

## Improvement

Added `validate_signal_trajectory_review` and an experimental schema.

Each signal now preserves its forecasted direction, window, threshold, observed
value and time, movement and timing status, threshold result, distance to the
threshold, and evidence. A valid review includes both moved and invariant
signals plus at least one unexpectedly timed signal. Binary outcome alone is
explicitly insufficient.

## Scope boundary

Cycle 165 records granular signal trajectories. Cycle 166 will assign different
review cadences to consequence types, including early harm and lagging benefit.

## Verification

- focused mission tests: 265 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes learns from how far and when each signal moved, including invariance
and near misses, rather than reducing reality to one success bit.
