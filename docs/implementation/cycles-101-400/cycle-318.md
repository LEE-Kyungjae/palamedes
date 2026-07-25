# Improvement Cycle 318

## Topic

Require selection and constitutional trace before contract issue.

## Deficiency

A free-form contract endpoint can bypass independent generation, criticism,
tournament selection, or constitutional judgment. A polished contract then
looks governed despite having no auditable authorization path.

## Improvement

Added `validate_governed_mission_contract_issue` and an experimental schema.

Only a `commit` selection may issue a planner contract. Selection, tournament,
and candidate IDs and fingerprints are mandatory. A verified constitutional
trace records each unique clause's interpretation, selection effect, authority,
and precedents. The version-one compact contract must link the committed
candidate, selection, and interpretation and contain the full why/what
interface. Free-form and tournament-bypassing paths are prohibited.

## Scope boundary

Cycle 318 governs contract creation. Cycle 319 will separate observed mission
outcomes from causal attribution while allowing evidence to trigger purpose
review without rewriting history.

## Verification

- focused mission tests: 877 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

No planner receives a mission contract that cannot reconstruct the frozen
candidate, tournament decision, constitutional reading, and authority that
produced it.
