# Improvement Cycle 264

## Topic

Change pressure after repeated null updates.

## Deficiency

Repeatedly applying the same cognitive operation with the same evidence,
causal model, and represented stakeholders can produce no update either
because the belief is stable or because the pressure is too weak. Treating the
null sequence as proof of stability makes that ambiguity invisible.

## Improvement

Added `validate_null_update_pressure_change` and an experimental schema.

The record counts consecutive null updates and links evidence for every one.
Below a precommitted threshold, pressure remains unchanged. At or above the
threshold, exactly one of evidence source, causal model, or stakeholder
representation must change, with matching previous and current identifiers and
a declared change type. The null diagnosis may remain underdetermined while
the new pressure discriminates stability from weak challenge.

## Scope boundary

Cycle 264 changes one reasoning pressure after stagnation. Cycle 265 will
protect mission lineage from concurrent wake races using state fingerprints.

## Verification

- focused mission tests: 661 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot interpret endless agreement with one unchanged perspective as
robust stability; repeated null updates force a controlled change in how the
belief is challenged.
