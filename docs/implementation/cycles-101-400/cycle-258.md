# Improvement Cycle 258

## Topic

Grant planner freedom with evidence- and scope-based return triggers.

## Deficiency

Vague delegation either forces the planner to seek approval for every choice or
lets it revise mission meaning when reality changes. Neither tells the runtime
who currently controls the affected decision.

## Improvement

Added `validate_planner_authority_return_contract` and an experimental schema.

The clause lists at least two delegated planner freedoms and distinct forbidden
actions. It requires exactly one evidence-change trigger and one scope-change
trigger, each with condition, threshold, and return action. When a trigger
fires, an observed change, evidence, and time are required; control
automatically changes from `planner` to `palamedes_review`, and unilateral
continuation is forbidden.

## Scope boundary

Cycle 258 governs live control transfer at the mission boundary. Cycle 259 will
keep full lineage addressable through links rather than embedding it in the
concise contract.

## Verification

- focused mission tests: 637 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes grants real downstream freedom while retaining an executable,
evidence-based return path when the mission's assumptions or authorized scope
change.
