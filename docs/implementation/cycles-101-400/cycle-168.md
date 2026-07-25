# Improvement Cycle 168

## Topic

Preserve uncertainty across value, mechanism, timing, and luck.

## Deficiency

A successful outcome could teach Palamedes an overly broad preference and
narrow future exploration, even when it remained unclear whether value fit,
mechanism, timing, or luck produced the result.

## Improvement

Added `validate_outcome_cause_uncertainty` and an experimental schema.

Every result retains separate assessments for value fit, mechanism, timing, and
luck, including evidence for and against, causal-identification strength,
confidence range, and residual uncertainty. At least two explanations remain
live, single-cause certainty is prohibited, and the record must preserve
exploration capacity and bound any learned preference to an explicit scope.

## Scope boundary

Cycle 168 preserves plural causal uncertainty. Cycle 169 will determine update
strength from evidence relevance and causal identification rather than outcome
size or emotional force.

## Verification

- focused mission tests: 277 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Success cannot collapse value, mechanism, timing, and luck into one learned
preference or eliminate competing exploration prematurely.
