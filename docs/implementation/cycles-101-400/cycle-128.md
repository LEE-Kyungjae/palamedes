# Improvement Cycle 128

## Topic

Compare acting now with waiting and natural uncertainty reduction.

## Deficiency

Cycle 127 proves that a constraint changed, but changed conditions do not imply
immediate action. Some uncertainty disappears naturally, and acting early is
valuable only when delay closes an option or a cheap probe preserves one.

## Improvement

Added `validate_act_wait_comparison` and an experimental schema.

The contract compares consequences and costs of acting and waiting, records
uncertainty expected to reduce naturally and options delay would close, and
supports `act_now`, `wait`, or `probe`. Acting now requires an option at risk;
waiting requires natural learning and a wake trigger; probing requires an
explicit probe. Aggregate urgency scores are forbidden.

## Scope boundary

Cycle 128 governs timing choice. Cycle 129 must assemble anomaly, affected
condition, enabling change, failed predecessors, window, and cheapest
discriminating exposure into one opportunity record.

## Verification

- focused mission tests: 117 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes treats waiting as a real alternative and acts early only to preserve
an option, not merely because a constraint changed.
