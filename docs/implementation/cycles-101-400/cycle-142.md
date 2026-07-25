# Improvement Cycle 142

## Topic

Bound authority by non-numeric consequence classes.

## Deficiency

Cycle 141 defines numeric resource and scope boundaries, but low-cost actions
can still create large reputational, privacy, relational, or strategic
commitments. Spending limits do not describe those consequences.

## Improvement

Added `validate_consequence_class_authority` and an experimental schema.

Every delegation now has exactly four consequence classes—reputational,
privacy, relational, and strategic—with autonomous, escalation, or prohibition
authority, plus boundaries, examples, and detection rules. Unclassified
consequences default to escalation. Numeric limits are explicitly insufficient.

## Scope boundary

Cycle 142 defines known consequence classes. Cycle 143 must classify novel
actions through analogical precedent while exposing weak analogy.

## Verification

- focused mission tests: 173 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot treat an action as harmless merely because it is cheap; its
non-financial commitments are explicit authority constraints.
