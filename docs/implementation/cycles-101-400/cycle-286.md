# Improvement Cycle 286

## Topic

Require every condition to output a mission contract before planning.

## Deficiency

Comparing downstream plans confounds purpose quality with planning skill when a
condition can plan before committing its mission. Planner knowledge of whether
a contract came from a human, one-shot agent, or Palamedes can also bias effort
and judgment.

## Improvement

Added `validate_preplanning_blinded_mission_contract_comparison` and an
experimental schema.

All three conditions must complete a compact causal and normative mission
contract before planner handoff. Each blinded handoff removes origin metadata,
uses a unique blinded identifier, and carries the same fingerprinted capability
constraint. No downstream plan may predate its mission contract.

## Scope boundary

Cycle 286 isolates purpose formation from planning and origin bias. Cycle 287
will order evaluation so novelty is considered only after consequence and
causal coherence.

## Verification

- focused mission tests: 749 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every comparison condition is judged first on an origin-blinded mission
commitment under identical planning capabilities, not on a plan that rewrites
its purpose after implementation begins.
