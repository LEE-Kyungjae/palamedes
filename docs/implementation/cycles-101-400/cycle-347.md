# Improvement Cycle 347

## Topic

Choose a reversible bounded mission or defer when no safe probe exists.

## Deficiency

An unsafe probe is not justified merely because uncertainty matters. Yet
uncertainty should not automatically cause paralysis when a reversible mission
fits delegated authority and bounded consequences.

## Improvement

Added `validate_no_safe_probe_reversible_decision` and an experimental schema.

Every candidate records a unique reversibility rank, rollback mechanism and
time, residual harm, authority and consequence assessments, and evidence for
the reversibility claim. If any candidate fits both mandate dimensions, the
lowest-rank candidate alone may receive a bounded commitment with rollback,
review, and authority-return triggers. If none fit, Palamedes must defer without
selection and create an authority escalation and wake trigger. Irreversible or
unescalated out-of-mandate commitment is forbidden.

## Scope boundary

Cycle 347 governs no-safe-probe decisions. Cycle 348 will bound exploration by
cost, expiry, evidence target, and a protected dominant commitment.

## Verification

- focused mission tests: 993 passed
- schema JSON parse: 244 schemas parsed
- `git diff --check`: passed

## Resulting invariant

In the absence of a safe experiment, Palamedes preserves option value inside
its mandate and returns authority rather than crossing it.
