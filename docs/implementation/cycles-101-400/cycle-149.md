# Improvement Cycle 149

## Topic

Attach constitutional and accountable lineage to consequential actions.

## Deficiency

Cycle 148 makes stop decisions diagnostically precise, but action logs could
still state only what happened. Without the governing clause, evidence state,
reversibility, and responsible identity, authority cannot be audited or
corrected.

## Improvement

Added `validate_consequential_action_lineage` and an experimental schema.

Every consequential action now binds mission, accountable agent and delegation,
authority decision, constitution clauses, evidence states and confidence,
consequence classes, timestamp, reversibility, and rollback or recovery.
Irreversible actions require a specific authorization.

## Scope boundary

Cycle 149 establishes action accountability. Cycle 150 must integrate
consequence-bounded delegation, safe probes, and escalation of only genuinely
ungranted power into one authority-thesis gate.

## Verification

- focused mission tests: 201 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Every consequential Palamedes action can be traced to who acted, what granted
the power, which evidence supported it, and how its effects can be reversed.
