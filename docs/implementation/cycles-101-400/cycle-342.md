# Improvement Cycle 342

## Topic

Enforce hard constitutional disqualification and explicit exceptions.

## Deficiency

A model can rationalize a compelling candidate past a hard constitutional
constraint. Conversely, an authorized emergency exception can be lost if every
violation is treated as absolute without checking the frozen constitution.

## Improvement

Added `validate_hard_constitutional_disqualification` and an experimental
schema.

The constitution is frozen before candidate review. Every hard violation names
its clause, scope, evidence, and rationale. Without an exception the candidate
is removed. An exception is valid only when a distinct frozen authorizing
clause explicitly names the violated clause, matches the violation scope,
carries an authorization record, and passes authority verification. Models
cannot invent permission or override the gate. Eligible and removed outputs
must exactly preserve assessment order.

## Scope boundary

Cycle 342 governs constitutional invalidity. Cycle 343 will distinguish
structurally incomplete candidates from merely low-scoring complete candidates.

## Verification

- focused mission tests: 973 passed
- schema JSON parse: 239 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Hard constitutional limits bind candidate selection unless the frozen
constitution itself contains a verified, scope-matching exception.
