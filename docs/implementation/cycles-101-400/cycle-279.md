# Improvement Cycle 279

## Topic

Minimize and access-control provenance with hash-only commitments when needed.

## Deficiency

Complete audit logs can become a second leak path for sensitive beneficiary
evidence or strategic reasoning. Storing everything in plaintext trades
auditability for exposure even when later verification only needs proof that a
specific content bundle existed.

## Improvement

Added `validate_minimized_access_controlled_provenance` and an experimental
schema.

Every record states collection necessity, minimization rationale, omitted
fields, sensitivity, allowed roles, retention deadline, and expiry action. The
policy demonstrates both minimized content and hash-only commitments.
Restricted records must be hash-only with no stored content. Every access event
is allowed or denied from the record's role list, and raw sensitive beneficiary
identifiers are forbidden from the shared log.

## Scope boundary

Cycle 279 protects provenance confidentiality without losing verifiability.
Cycle 280 will integrate the adversarial thesis across source incentives,
authority separation, aggregate consequences, and protected lineage.

## Verification

- focused mission tests: 721 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes retains enough provenance to verify decisions without making its
audit trail an unrestricted copy of sensitive beneficiary and strategic data.
