# Improvement Cycle 313

## Topic

Evaluate wake separately from signal recording.

## Deficiency

Persisting evidence and allocating cognition are different decisions. Without a
separate wake evaluation, every signal can consume reasoning or mutate state,
and no artifact explains which frontier insufficiency justified that cost.

## Improvement

Added `validate_evaluate_wake_command` and an experimental schema.

The command reads identified, fingerprinted signal, frontier, and constitution
state. A wake result names one recognized insufficiency, maps it to exactly one
cognitive operation, and grants positive tokens and one operation within the
available budget. A no-wake result names no insufficiency or operation and
grants zero budget. Evaluation is read-only and creates no wake event itself.

## Scope boundary

Cycle 313 decides whether and how cognition is warranted. Cycle 314 will allow
multiple causal sketches to be recorded without selecting one as truth.

## Verification

- focused mission tests: 857 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every cognitive activation is an explicit, budgeted answer to a named deficit
in frozen frontier and constitutional state—not a side effect of receiving
data.
