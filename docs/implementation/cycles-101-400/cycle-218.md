# Improvement Cycle 218

## Topic

Trace mission interpretation through constitutional state.

## Deficiency

An alignment verdict without an interpretation path hides which mission
features activated which clauses and where conflict, exception, or uncertainty
entered the decision. It cannot be reconstructed or challenged later.

## Improvement

Added `validate_constitution_interpretation_trace` and an experimental schema.

The trace versions both mission and constitution, identifies mission features,
and requires every feature to reach at least one applied clause. It then records
clause conflicts and their resolution records, principle overrides and their
evidence and predictions, and uncertainties with their decision effects.
Every reference must point back to an actually applied clause.

## Scope boundary

Cycle 218 makes interpretation traceable. Cycle 219 will prevent the trace from
being mistaken for proof of alignment and use it to detect convenient
interpretation and recurring blind spots.

## Verification

- focused mission tests: 477 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can reconstruct how concrete mission features traveled through
constitutional clauses, conflicts, exceptions, and unresolved uncertainty.
