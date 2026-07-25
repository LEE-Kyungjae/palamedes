# Improvement Cycle 172

## Topic

Give planners causal and consequence signals sufficient for tradeoffs.

## Deficiency

Removing execution detail could leave a mission contract so abstract that a
planner had to reconstruct the upstream causal reasoning and decide which
success or harm tradeoffs changed the mission.

## Improvement

Added `validate_mission_tradeoff_interface` and an experimental schema.

The handoff now includes a sourced causal thesis, essential mechanisms, causal
assumptions, and separately typed success and harm signals. Each signal has a
threshold, observation window, evidence source, and planner response. An
explicit tradeoff rule and return condition let planners adapt strategy without
silently redefining the mission.

## Scope boundary

Cycle 172 supplies enough meaning for strategy tradeoffs. Cycle 173 will add
typed planner return paths for constraint updates, thesis challenges, and
execution alternatives.

## Verification

- focused mission tests: 293 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Planner freedom does not require reconstructing why the mission should work or
which observed benefits and harms require a return to Palamedes.
