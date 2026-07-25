# Improvement Cycle 256

## Topic

Give success baselines and time ranges while reviewing harm earlier.

## Deficiency

A success threshold without a baseline cannot show improvement, and a point
deadline hides the plausible interval in which an effect should appear. Using
that same review time for harm can leave beneficiaries exposed when damage is
observable before enough time has passed to estimate benefit.

## Improvement

Added `validate_timed_success_harm_signals` and an experimental schema.

Every success signal now has a numeric baseline with evidence, an explicitly
directed target range, and observation start and end days. The target must
improve on the baseline in the stated direction. Every harm signal has a
threshold, evidence source, first review day, and response. When damage can
precede benefit, its first review must occur before the earliest success
observation window.

## Scope boundary

Cycle 256 governs signal timing and comparison. Cycle 257 will distinguish
mission disconfirmation from planner, implementation, measurement, and timing
failure.

## Verification

- focused mission tests: 629 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes judges success against an evidenced baseline over a plausible time
range and does not wait for lagging benefit before checking earlier harm.
