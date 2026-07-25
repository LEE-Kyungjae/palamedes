# Improvement Cycle 173

## Topic

Add typed planner return paths across the mission boundary.

## Deficiency

Planners could discover infeasibility or causal contradictions but return them
as unstructured discussion, or silently rewrite the mission while adapting
strategy.

## Improvement

Added `validate_planner_boundary_return` and an experimental schema.

Each return identifies the contract version, planner, evidence, affected field,
and requested response. It is typed as a constraint update, thesis challenge, or
execution alternative, with kind-specific details. Planners are explicitly
forbidden from unilaterally revising the mission.

## Scope boundary

Cycle 173 types discoveries crossing the boundary. Cycle 174 will distinguish
ordinary constraints from discoveries that imply a better beneficiary or
mechanism and therefore a different mission.

## Verification

- focused mission tests: 297 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Planner discoveries cross the purpose boundary as inspectable typed evidence,
not silent mission drift or an unstructured objection.
