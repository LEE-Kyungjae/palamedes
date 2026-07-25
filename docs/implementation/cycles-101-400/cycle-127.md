# Improvement Cycle 127

## Topic

Name the changed constraint that creates a timing window.

## Deficiency

Cycle 126 identifies conditions missing from failed predecessors. Palamedes
could still assert that those conditions are different “now” without specifying
what changed, when, how strongly, or whether the change will persist.

## Improvement

Added `validate_changed_constraint_window` and an experimental schema.

A timing claim now names the constraint and missing-condition kind, distinct
before and after states, date, evidence and source, why the opportunity was
formerly unviable and is now viable, confidence, durability, and a reversal
signal. Generic “now” claims are forbidden.

## Scope boundary

Cycle 127 proves a changed constraint. Cycle 128 must compare acting during the
window with waiting, including uncertainty that may resolve naturally and
options that delay may close.

## Verification

- focused mission tests: 113 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can claim timing only through a traceable constraint transition whose
durability and reversal can be monitored.
