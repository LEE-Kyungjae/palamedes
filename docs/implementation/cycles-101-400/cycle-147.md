# Improvement Cycle 147

## Topic

Let pre-registered disconfirmation outrank sunk cost.

## Deficiency

Cycle 146 prevents implementation agents from expanding scope, but Palamedes
itself could keep a failing mission alive because substantial code, time, or
identity had accumulated around it.

## Improvement

Added `validate_disconfirmation_stop_authority` and an experimental schema.

When a pre-registered condition and threshold are met by sourced evidence, the
decision must be `stop`. Sunk cost cannot override it. Stop actions must freeze
resources and revoke downstream delegations while preserving evidence and the
option landscape.

## Scope boundary

Cycle 147 establishes stopping authority. Cycle 148 must distinguish genuine
thesis failure from execution failure, delayed signal, or measurement failure
before triggering it.

## Verification

- focused mission tests: 193 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can terminate its own mission when its causal thesis fails, regardless
of prior investment.
