# Improvement Cycle 335

## Topic

Govern personal preference history with disconfirming precedents.

## Deficiency

Repeated owner taste can look like a value mandate even when no constitution
grants it authority. Retrieving only preference-confirming history turns
personalization into bias amplification.

## Improvement

Added `validate_constitution_authorized_preference_history` and an experimental
schema.

Preference history may enter context only under a fingerprinted constitution
clause whose authorized domain matches the decision. The clause limits its use
to advisory evidence and cannot override beneficiary or observed-outcome
evidence. Authorized history must include both confirming and disconfirming
owner precedents with decision context, observed outcomes, provenance, and
fingerprints. The summary preserves exact precedent links and both tendencies.

## Scope boundary

Cycle 335 governs owner history. Cycle 336 will minimize exposure of sensitive
signals through summaries, redaction, local embeddings, and controlled original
provenance.

## Verification

- focused mission tests: 945 passed
- schema JSON parse: 232 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The owner's repeated taste is neither hidden nor sovereign: it is scoped,
counter-evidenced, and subordinate to governed beneficiary and outcome evidence.
