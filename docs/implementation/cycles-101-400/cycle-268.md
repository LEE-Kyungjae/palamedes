# Improvement Cycle 268

## Topic

Defer honestly on budget exhaustion with a missing condition and wake trigger.

## Deficiency

When a reasoning budget ends, an agent can manufacture confidence simply to
produce a terminal answer. That hides unresolved purpose uncertainty and makes
later evidence look like an exception rather than the condition the decision
was waiting for.

## Improvement

Added `validate_budget_exhaustion_deferral` and an experimental schema.

An exhausted record must have zero remaining budget, deny fabricated closure
and resolution, and remain `deferred`. It names exactly one decisive missing
condition, the evidence required to observe it, and a registered next wake
type and threshold. A safe interim state and explicit option-preservation
action keep deferral from becoming uncontrolled inaction.

## Scope boundary

Cycle 268 governs honest exhaustion. Cycle 269 will treat sleeping as a
cognitive operation when reality is the only useful remaining information
source.

## Verification

- focused mission tests: 677 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can run out of cognition without pretending uncertainty disappeared;
it leaves a precise condition under which thought should resume.
