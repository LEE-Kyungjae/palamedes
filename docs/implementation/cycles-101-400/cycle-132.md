# Improvement Cycle 132

## Topic

Normalize sealed candidates against common constraints.

## Deficiency

Cycle 131 protects independent formation, but candidates produced from isolated
evidence slices may omit shared constitutional prohibitions or assume different
resource availability. Direct comparison would then reward incompatible
premises.

## Improvement

Added `validate_common_candidate_normalization` and an experimental schema.

Sealed candidates are evaluated against one constitution version, resource
envelope, evaluation date, and common context hash. Each records constitutional
fit, resource demand, and constraint tensions while preserving the hash and
original thesis. Normalization cannot rewrite candidates.

## Scope boundary

Cycle 132 creates a fair common context. Cycle 133 must ensure comparison
represents option creation, learning, and beneficiary change alongside legible
near-term output.

## Verification

- focused mission tests: 133 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes preserves independently formed alternatives while making their shared
constraints and resource assumptions comparable.
