# Improvement Cycle 350

## Topic

Integrate deterministic tournament boundaries around model judgment.

## Deficiency

Eligibility, criticism, selection, and issuance can each be valid in isolation
while their composition still lets a model revive an incomplete or
constitutionally disqualified candidate. A scalar score can also erase the
unresolved value tradeoffs that the tournament was designed to preserve.

## Improvement

Added `validate_deterministic_model_tournament_implementation` and an
experimental schema.

The integration requires verified evidence for all nine tournament controls.
Structural completeness, constitutional eligibility, and shared-assumption
dominance deterministically construct the frontier. Model-owned adversarial
criticism and semantic selection operate only inside it. A deterministic
post-check then constrains the selected candidate before winner, authority, and
reversal triggers are issued atomically. Every unresolved tradeoff remains an
evidence-linked, revisitable object; scalar aggregation and model-authored
eligibility are forbidden.

## Scope boundary

Cycle 350 closes the tournament implementation block. Cycle 351 will adapt the
existing goal-and-success-metric planner interface without collapsing the
upstream mission contract into a conventional goal.

## Verification

- focused mission tests: 1005 passed
- schema JSON parse: 247 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Models criticize and choose only within a reproducibly eligible,
non-dominated frontier, while code enforces the boundary without pretending to
make the semantic value judgment or averaging away unresolved tradeoffs.
