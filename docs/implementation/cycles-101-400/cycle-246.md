# Improvement Cycle 246

## Topic

Select an information-producing probe over premature mission commitment.

## Deficiency

A tournament that must always crown a mission converts unresolved assumptions
into premature commitment. Sometimes the most valuable result is evidence that
preserves options and changes which mission should win.

## Improvement

Added `validate_probe_over_mission_selection` and an experimental schema.

The record compares bounded probe option value with immediate commitment value.
The probe must separate every leading mission and specify the observation and
selection update rule. When probe option value is higher, the computed result
is `select_probe` and premature mission commitment is forbidden; otherwise
commitment may proceed.

## Scope boundary

Cycle 246 admits probes as tournament winners. Cycle 247 will compare probes by
harm, speed, separation, and whether existing evidence already answers them.

## Verification

- focused mission tests: 589 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can end a mission tournament by buying the evidence that changes
selection rather than manufacturing certainty and choosing too early.
