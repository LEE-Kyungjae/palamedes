# Improvement Cycle 305

## Topic

Represent constitution state as structured governed records.

## Deficiency

One editable constitution prompt hides clause identity, precedence, scope,
authority, conflict, and learned precedent. Any prompt edit can silently
reorder values or erase why a boundary was adopted.

## Improvement

Added `validate_structured_constitution_state` and an experimental schema.

Constitution state and every clause are versioned. Clauses have a recognized
kind, numeric precedence, scope, authority source, reciprocal conflict links,
and outcome-precedent references. Precedents link a known clause to outcome
evidence, a finding, and an interpretation boundary. Amendments require named
authority; the constitution cannot be treated as one freely editable prompt.

## Scope boundary

Cycle 305 structures normative state. Cycle 306 will structure causal sketches
while keeping empirical claims and normative assumptions separate.

## Verification

- focused mission tests: 825 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every constitutional judgment can identify the exact governed clause,
precedence, conflict, authority source, and outcome evidence that shaped it.
