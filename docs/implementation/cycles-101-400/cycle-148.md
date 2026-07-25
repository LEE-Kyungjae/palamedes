# Improvement Cycle 148

## Topic

Diagnose thesis, execution, delay, and measurement failures before stopping.

## Deficiency

Cycle 147 enforces stopping after disconfirmation, but a missing signal may
reflect bad execution, a genuinely delayed effect, or a broken measurement
rather than a false mission thesis. Blind automatic stopping can destroy
fragile long-horizon work.

## Improvement

Added `validate_stop_failure_diagnosis` and an experimental schema.

Every deviation is assessed under exactly four hypotheses: thesis failure,
execution failure, delayed signal, and measurement failure. Each carries
plausibility, evidence, and a discriminator. The selected diagnosis determines
the only valid decision: stop, remediate execution, wait, or repair measurement.

## Scope boundary

Cycle 148 makes stopping diagnostically precise. Cycle 149 must make every
consequential action traceable to constitution clause, evidence state,
reversibility, and accountable agent identity.

## Verification

- focused mission tests: 197 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes stops a mission only for diagnosed thesis failure, not merely because
an expected signal was absent.
