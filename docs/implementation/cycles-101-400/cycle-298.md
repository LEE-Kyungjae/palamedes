# Improvement Cycle 298

## Topic

Limit the first runtime to one serial purpose cycle.

## Deficiency

Concurrency and company-wide orchestration obscure whether one purpose loop
works. A minimal runtime should first prove that a wake can lead through a safe
probe and planner handoff to an outcome that updates purpose state.

## Improvement

Added `validate_single_serial_purpose_runtime_cycle` and an experimental schema.

Exactly four non-overlapping stages execute in order: wake, bounded probe,
planner handoff, and outcome return. Each depends only on the prior stage. The
probe has budget, harm, expiry, and stop controls, and the outcome must return
evidence to the mission frontier. Concurrent-cycle and scaled-orchestration
claims are forbidden.

## Scope boundary

Cycle 298 defines the first executable serial loop. Cycle 299 will require the
next code change to implement this vertical slice instead of adding conceptual
surface area.

## Verification

- focused mission tests: 797 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes must close one bounded, observable purpose-to-outcome loop before
complexity from concurrent agents or orchestration is admitted.
