# Improvement Cycle 178

## Topic

Accumulate plan failures before challenging mission feasibility.

## Deficiency

One failed plan could be mistaken for an infeasible mission, while repeated
failures could remain trapped in endless replanning even when they consistently
challenged the same feasibility assumption.

## Improvement

Added `validate_cumulative_plan_failure_boundary` and an experimental schema.

The boundary counts only attempts with adequate execution that implicate the
same pre-registered feasibility assumption. A mission challenge requires a
configured number of qualifying failures across multiple strategy families.
Before that boundary, the correct response is replanning; one failure never
disconfirms the mission.

## Scope boundary

Cycle 178 defines the cumulative return boundary. Cycle 179 will version mission
revisions, preserve their reasons, and invalidate dependent downstream work.

## Verification

- focused mission tests: 317 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Plan failure changes purpose only after independent, adequately executed
attempts accumulate against the same feasibility assumption.
