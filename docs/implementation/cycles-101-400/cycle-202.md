# Improvement Cycle 202

## Topic

Define signal importance as a value-capability-time relation.

## Deficiency

Events could be labeled important because they were large, recent, or
interesting without showing how the change affected a condition, implicated the
constitution, connected to available capability, or mattered within time.

## Improvement

Added `validate_relational_signal_importance` and an experimental schema.

Importance now traverses four explicit relations: change to affected condition,
condition to value, value to available capability, and capability to time. Each
relation carries a claim, evidence, status, and uncertainty. Events have no
intrinsic importance, and high importance requires the complete chain.

## Scope boundary

Cycle 202 defines known relational importance. Cycle 203 will reserve bounded
attention for anomalies that fit no current value or world model.

## Verification

- focused mission tests: 413 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Importance belongs to a situated relation among change, affected condition,
values, capability, and time—not to an event in isolation.
