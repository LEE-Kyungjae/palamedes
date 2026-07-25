# Improvement Cycle 231

## Topic

Generate missions from both conditions and capabilities.

## Deficiency

Problem-first search overproduces repair missions and can miss newly reachable
beneficiary states. Capability-first search overproduces uses for available
technology and can mistake technical possibility for a worthwhile mission.

## Improvement

Added `validate_bidirectional_mission_generation` and an experimental schema.

Every generation round must include condition-first and capability-first
candidates. Both origins name evidence, beneficiary, mission hypothesis,
desired state change, and failure signal, then enter the same comparison using
beneficiary consequence, constitutional fit, evidence strength, and option
value. Neither generation direction receives default authority.

## Scope boundary

Cycle 231 establishes both search directions. Cycle 232 will specify the
different questions condition-first and capability-first generation must ask.

## Verification

- focused mission tests: 529 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes searches for missions from both unmet beneficiary conditions and
newly reachable states without confusing either starting point with selection.
