# Improvement Cycle 121

## Topic

Search capability–institution mismatches before trends.

## Deficiency

Cycle 120 defines what a desire-centered mission looks like, but Palamedes
still lacked an upstream opportunity-search primitive. Following popular trends
finds opportunities only after others have named and crowded them.

## Improvement

Added `validate_capability_institution_mismatch` and an experimental schema.

An opportunity now begins from sourced evidence of a new capability and an old
institutional rule or assumption, explains why that rule persists, names the
blocked beneficiary condition change and mismatch mechanism, and includes a
disconfirming condition. Trend consensus is recorded but cannot define the
opportunity.

## Scope boundary

Cycle 121 establishes mismatch search. Cycle 122 must prevent capability
novelty itself from creating solutionism.

## Verification

- focused mission tests: 89 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes can discover opportunities before consensus by explaining a concrete,
falsifiable collision between new capability and institutional inertia.
