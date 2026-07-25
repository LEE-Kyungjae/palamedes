# Improvement Cycle 171

## Topic

Keep mission contracts about meaning and boundaries, not execution shape.

## Deficiency

A mission contract could contain detailed tasks, prescribed tools, or an
implementation sequence. That would let Palamedes invade strategy formation and
prevent planners from adapting execution to newly discovered constraints.

## Improvement

Added `validate_mission_meaning_boundary_contract` and an experimental schema.

The contract now states situation, mission meaning, beneficiary condition,
desired condition, explicit scope boundaries, and planner freedoms. It declares
planner ownership of strategy and leaves execution shape unlocked. Detailed
tasks, prescribed tools, and implementation sequences must remain empty.

## Scope boundary

Cycle 171 removes execution shape from the mission contract. Cycle 172 will add
enough causal thesis and success/harm signals to prevent the remaining contract
from becoming too abstract.

## Verification

- focused mission tests: 289 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes specifies why a mission matters and where its authority ends while the
planner retains freedom to decide how the mission should be pursued.
