# Improvement Cycle 329

## Topic

Disclose shared-model dependence across roles.

## Deficiency

Local testing may assign one model to every cognitive role. Treating five role
outputs as five independent opinions would inflate confidence while hiding
correlated model errors.

## Improvement

Added `validate_shared_model_dependence_manifest` and an experimental schema.

The runtime manifest records provider, model, context partition, and preserved
boundary for each of the five roles. Every model assigned to multiple roles
must appear in a dependence group that counts as one independent source and
discloses correlated-error risk. Evaluation separately reports role outputs,
unique models, and unique providers. Shared-model agreement is labeled
`correlated_role_agreement`, never independent consensus.

## Scope boundary

Cycle 329 permits cheap local execution without overstating independence. Cycle
330 will integrate the provider-neutral cognition thesis and its deterministic
enforcement.

## Verification

- focused mission tests: 921 passed
- schema JSON parse: 226 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Structural role separation remains useful under one model, but confidence
claims reflect the actual number of independent model sources.
