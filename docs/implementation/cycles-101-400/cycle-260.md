# Improvement Cycle 260

## Topic

Integrate the compressed causal and normative mission contract thesis.

## Deficiency

The contracts from Cycles 251–259 can exist independently while a handoff omits
one of them. Compression might lose meaning, causal guidance might prescribe a
form, normative boundaries might become advisory, or planner freedom might
erase the return path.

## Improvement

Added `validate_mission_contract_thesis_integration` and an experimental schema.

The gate links the reasoning compression, situation and meaning, beneficiary
condition, causal mechanisms, reopenable non-goals, timed signals,
disconfirmation protocol, authority clause, and lineage index. It separately
enumerates the causal and normative interface components and verifies nine
preservation guarantees. Full reasoning may remain addressable but not
embedded; implementation form belongs to the planner, while mission meaning
and authority return remain outside unilateral planner revision.

## Scope boundary

Cycle 260 closes the planner-contract section. Cycle 261 will make runtime
reasoning selective by maintaining a frontier of unresolved value-relevant
uncertainties and active mission assumptions.

## Verification

- focused mission tests: 645 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

A Palamedes handoff is eligible only as a compact causal and normative
interface that preserves why and what must change while maximizing freedom over
how to achieve it.
