# Improvement Cycle 134

## Topic

Require an early signal diagnostic of the causal thesis.

## Deficiency

Cycle 133 preserves long-horizon dimensions, but an attractive narrative can
defer accountability indefinitely. Ordinary activity or output metrics may rise
even when the mission's causal mechanism is wrong.

## Improvement

Added `validate_early_causal_signal` and an experimental schema.

Every candidate now names an early signal, observation window, measurement and
baseline, distinct expectations under true and false theses, why the signal is
unlikely under the false thesis, a threshold, and an action if absent. Output
proxies and post-hoc explanation of absence are forbidden.

## Scope boundary

Cycle 134 makes causal narratives answerable early. Cycle 135 must keep
probability ranges and downside exposure visible so improbable high-upside
missions do not dominate imagination.

## Verification

- focused mission tests: 141 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

No Palamedes mission may rely solely on distant narrative value; it must expose
an early observation capable of proving its causal thesis wrong.
