# Improvement Cycle 357

## Topic

Answer only purpose-affecting planner challenges.

## Deficiency

Challenge type alone does not determine jurisdiction. An alternative mechanism
may revise the causal thesis or merely choose an implementation form. If
Palamedes answers both, it becomes a micromanaging planner; if it answers
neither, planners can silently rewrite purpose.

## Improvement

Added `validate_purpose_effect_challenge_jurisdiction` and an experimental
schema.

Every challenge is assessed against beneficiary, invariant meaning,
constitution, authority, causal thesis, and execution form with evidence. Any
effect on the five purpose dimensions routes the decision to a Palamedes
mission response. An execution-form-only effect returns the choice to the
planner. Palamedes cannot prescribe the implementation choice, its
implementation opinion remains advisory, and the planner cannot rewrite
purpose.

## Scope boundary

Cycle 357 fixes challenge jurisdiction. Cycle 358 will invalidate dependent
strategy versions when a mission revision occurs and require explicit planner
acceptance.

## Verification

- focused mission tests: 1033 passed
- schema JSON parse: 254 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes governs purpose effects while planners retain implementation
judgment, even when Palamedes would personally prefer another implementation.
