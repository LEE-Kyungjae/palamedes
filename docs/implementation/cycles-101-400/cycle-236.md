# Improvement Cycle 236

## Topic

Require missions to describe changed external conditions.

## Deficiency

“Build,” “research,” or “improve Palamedes” describes internal activity, not
why the activity matters. Activity-shaped missions can succeed operationally
while no beneficiary condition changes.

## Improvement

Added `validate_external_condition_mission` and an experimental schema.

A mission must identify an external beneficiary, distinct current and target
conditions, an observable measure, baseline, target, evaluation horizon, and
failure condition. Internal systems cannot be the beneficiary, and supporting
activities remain subordinate identifiers rather than the mission object.

## Scope boundary

Cycle 236 defines external mission shape. Cycle 237 will permit internal
capability work only when it is subordinate to such a mission and cheaper than
available alternatives.

## Verification

- focused mission tests: 549 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes proposes missions in terms of observable changes in the external
world, never completion of its own activity.
