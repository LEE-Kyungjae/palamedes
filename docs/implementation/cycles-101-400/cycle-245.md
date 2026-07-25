# Improvement Cycle 245

## Topic

Normalize assumptions or isolate the selection-changing assumption.

## Deficiency

Most mission comparisons use different estimates, baselines, or causal
assumptions. Applying dominance before aligning them produces a precise-looking
but invalid winner.

## Improvement

Added `validate_assumption_normalization_or_pivot` and an experimental schema.

Every assumption records both candidate values and whether a normalized value
exists. Fully normalized sets proceed to comparison. Otherwise the review must
identify exactly one unresolved assumption capable of reversing selection,
name it as the pivot, and run a discriminating probe. Multiple pivotal
assumptions or an already normalized pivot are rejected.

## Scope boundary

Cycle 245 governs assumption alignment. Cycle 246 will allow a tournament to
choose an information-producing probe instead of prematurely committing to a
mission.

## Verification

- focused mission tests: 585 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes compares missions only after normalizing their assumptions or
concentrating inquiry on the one unresolved assumption that changes selection.
