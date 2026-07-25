# Improvement Cycle 346

## Topic

Probe selection-controlling assumptions with precommitted branches.

## Deficiency

When one uncertain assumption flips the preferred mission, further debate adds
little information. Running a probe without precommitted consequences still
permits hindsight to reinterpret the result.

## Improvement

Added `validate_precommitted_assumption_probe_branches` and an experimental
schema.

The probe names the controlling assumption, selection threshold, affected
candidates, measurement, population, cost, harm, stop condition, expiry, and
observation method. It must be safe within authority and reversible. Before any
observation, at least two contiguous, mutually exclusive, exhaustive result
branches are frozen. Every branch maps its interval to known candidates,
selection mode, action, and rationale. Selection remains
`discriminating_probe` until a branch resolves, and post-hoc rewriting is
forbidden.

## Scope boundary

Cycle 346 handles a safe discriminating probe. Cycle 347 will choose the most
reversible authority-bounded mission—or defer—when no safe probe exists.

## Verification

- focused mission tests: 989 passed
- schema JSON parse: 243 schemas parsed
- `git diff --check`: passed

## Resulting invariant

An uncertain assumption that controls mission choice is resolved by reality
under consequences committed before the result is known.
