# Improvement Cycle 237

## Topic

Subordinate internal capability work to cheaper external-mission delivery.

## Deficiency

Internal tooling can acquire mission status merely because it is interesting or
reusable. This lets Palamedes optimize itself while an existing service,
manual process, or other alternative could deliver the external change more
cheaply.

## Improvement

Added `validate_subordinate_internal_capability_work` and an experimental
schema.

Internal work must name the external mission dependency and cannot be an
independent mission. It is compared with at least one evidence-backed adequate
alternative in common cost units. The computed cheaper adequate path determines
the decision. Approved internal work has an expiry and stops when its mission
dependency disappears or a cheaper adequate alternative emerges.

## Scope boundary

Cycle 237 governs internal support work. Cycle 238 will make external missions
falsifiable without prematurely locking planners into one implementation.

## Verification

- focused mission tests: 553 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes develops itself only as temporary, cost-justified support for a
specific external mission.
