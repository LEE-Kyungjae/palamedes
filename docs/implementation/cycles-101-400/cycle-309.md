# Improvement Cycle 309

## Topic

Make mission contracts immutable and notify dependent planners.

## Deficiency

Editing an active mission contract in place destroys the exact purpose under
which downstream work began. Silent revision also lets planners continue work
whose assumptions, non-goals, or desired outcome are no longer valid.

## Improvement

Added `validate_immutable_mission_contract_successor` and an experimental
schema.

A revision creates a new contract ID, fingerprint, and consecutive version
linked to the immutable predecessor and its fingerprint. Changed fields,
authority, evidence, and reason are explicit. Every planner work item depending
on the predecessor receives exactly one `review_required` or `invalidated`
notification referencing the successor before it becomes active.

## Scope boundary

Cycle 309 protects contract and planner lineage. Cycle 310 will integrate the
typed linked-object state thesis while preserving observation, interpretation,
selection, and downstream-plan boundaries.

## Verification

- focused mission tests: 841 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Past planner work always retains the mission version that authorized it, and no
new mission version can silently inherit execution built for a different
purpose.
