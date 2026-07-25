# Improvement Cycle 330

## Topic

Integrate the provider-neutral cognition thesis.

## Deficiency

Provider-neutral roles, context separation, blinded review, deterministic
controls, failure handling, and dependence disclosure can each exist while the
overall system still lacks evidence that they operate as one governed
cognition architecture.

## Improvement

Added `validate_provider_neutral_cognition_thesis` and an experimental schema.

Integration requires nine verified component artifacts covering model
multiplicity measurement, roles, invention independence, interpretation
routing, adversarial blinding, selector structure, ownership, failure recovery,
and dependence disclosure. Each carries its validator, schema, fingerprint, and
verification record. The integrated invariants preserve provider neutrality,
structural separation, deterministic independence and authority enforcement,
validated state transitions, honest dependence claims, and explicit failure.

## Scope boundary

Cycle 330 closes the cognition-architecture block. Cycle 331 will minimize
repository and history context so prior conclusions do not leak into
independent mission generation.

## Verification

- focused mission tests: 925 passed
- schema JSON parse: 227 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Semantic cognition remains flexible across providers while deterministic
infrastructure—not prompts or model self-report—governs independence and
authority claims.
