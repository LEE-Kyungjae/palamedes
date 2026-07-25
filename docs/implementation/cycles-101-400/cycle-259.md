# Improvement Cycle 259

## Topic

Link concise claims to addressable full lineage.

## Deficiency

Embedding every source record defeats contract compression, while removing
lineage makes concise claims unauditable. A planner or reviewer then must choose
between overload and unsupported assertions.

## Improvement

Added `validate_addressable_contract_lineage` and an experimental schema.

The contract sets a maximum claim length and forbids embedding full lineage.
Full records live behind immutable addresses and content hashes. The index must
contain signals, interpretations, alternatives, and constitution traces, and
every concise claim links to a known record of each kind. Missing or mutable
lineage therefore invalidates the claim without enlarging the planner-facing
contract.

## Scope boundary

Cycle 259 governs compact auditability. Cycle 260 will integrate the complete
mission contract as a compressed causal and normative interface that preserves
meaning while maximizing planner freedom.

## Verification

- focused mission tests: 641 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes contracts remain concise, but every important claim can be expanded
into its full evidential, interpretive, alternative, and constitutional
lineage by address.
