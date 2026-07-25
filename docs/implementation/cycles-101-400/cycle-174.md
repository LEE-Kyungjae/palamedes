# Improvement Cycle 174

## Topic

Let constraints reopen beneficiary or mechanism selection.

## Deficiency

Palamedes could treat planner-reported constraints as mere resistance to be
overcome, even when they revealed that a different beneficiary or causal
mechanism would form a more worthwhile mission.

## Improvement

Added `validate_constraint_reframing_review` and an experimental schema.

A constraint is compared against an explicit alternative beneficiary and
mechanism across beneficiary change, causal defensibility, and constitutional
fit. Constraint evidence cannot be dismissed by default. When the alternative
mission is better, planning pauses and mission selection reopens.

## Scope boundary

Cycle 174 lets planning discoveries improve purpose formation. Cycle 175 will
protect beneficiary condition and non-goals from feasibility optimization unless
Palamedes explicitly versions a mission revision.

## Verification

- focused mission tests: 301 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

A real constraint may invalidate the current framing and reopen mission
selection instead of being treated as planner resistance.
