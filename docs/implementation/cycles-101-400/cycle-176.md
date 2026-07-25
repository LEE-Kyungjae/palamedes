# Improvement Cycle 176

## Topic

Report retired uncertainty and observed consequence beside delivery.

## Deficiency

Downstream status could report only tasks or delivery completion, allowing
execution progress to crowd out whether the work learned anything or changed
the beneficiary's condition.

## Improvement

Added `validate_downstream_mission_status` and an experimental schema.

Every status includes delivery evidence, at least one explicitly retired
uncertainty, and at least one sourced observed consequence with affected party
and time. Delivery completion is prohibited from substituting for an outcome,
and the next observation remains explicit.

## Scope boundary

Cycle 176 broadens downstream status beyond delivery. Cycle 177 will decide
which conflicts between multiple planners belong to purpose arbitration and
which remain technical strategy choices.

## Verification

- focused mission tests: 309 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Downstream progress is incomplete without evidence of learning and external
consequence, regardless of how many tasks were delivered.
