# Improvement Cycle 185

## Topic

Charge new missions an explicit exploration and displacement cost.

## Deficiency

Agents can generate initiatives cheaply, making every new idea appear additive
while attention, observation capacity, and strategic coherence become
overcommitted.

## Improvement

Added `validate_new_mission_exploration_charge` and an experimental schema.

A new mission consumes positive exploration and attention capacity, names the
current option it displaces, states released capacity and displacement
consequence, and preserves the displaced option's lineage and wake trigger.
Admission is rejected if projected commitment exceeds finite capacity.

## Scope boundary

Cycle 185 governs mission admission cost. Cycle 186 will expose coordination
overhead through decision latency and contradiction resolution rather than
message counts.

## Verification

- focused mission tests: 345 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

No new mission is free: it consumes finite exploration and attention and makes
the sacrificed portfolio option explicit.
