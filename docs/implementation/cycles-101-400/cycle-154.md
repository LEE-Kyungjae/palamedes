# Improvement Cycle 154

## Topic

Compare Palamedes with absent and simpler counterfactuals.

## Deficiency

Cycle 153 exposes self-expansion timing, but reviewers may still accept
complexity because understanding or removing the system feels costly. They need
a minimal observable comparison, not an architectural argument.

## Improvement

Added `validate_minimal_system_counterfactual` and an experimental schema.

The same frozen input signals are given to absent, simpler, and full-Palamedes
conditions. Each preserves system description, output and reasoning hashes,
owner labor, and quality observation under blind evaluation. An adequacy
threshold identifies the minimal sufficient condition and requires a complexity
justification.

## Scope boundary

Cycle 154 tests whether complexity is necessary. Cycle 155 must isolate upstream
cognition from ceremony by asking whether a simple planner can infer the same
mission from already supplied signals.

## Verification

- focused mission tests: 221 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes complexity remains justified only when a simpler or absent system
fails the same beneficiary-oriented test under fixed inputs.
