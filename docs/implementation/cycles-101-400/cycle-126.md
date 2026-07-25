# Improvement Cycle 126

## Topic

Learn missing conditions from failure archives.

## Deficiency

Cycle 125 connects repository patterns to beneficiary change, but success-only
reference learning encourages surface imitation. Failed predecessors reveal
which plausible combinations lacked timing, trust, distribution, economics,
capability, or institutional fit.

## Improvement

Added `validate_failure_archive_learning` and an experimental schema.

Every failed predecessor preserves its plausible thesis, observed failure,
evidence for a typed missing condition, archive limitations, and source. The
analysis must synthesize across failures, retain a surviving assumption and a
disconfirming condition, and reject the sufficiency of success cases.

## Scope boundary

Cycle 126 identifies missing conditions. Cycle 127 must show which specific
constraint has changed now, rather than using generic timing language.

## Verification

- focused mission tests: 109 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes learns from why plausible predecessors failed and carries those
missing conditions forward instead of copying only successful surfaces.
