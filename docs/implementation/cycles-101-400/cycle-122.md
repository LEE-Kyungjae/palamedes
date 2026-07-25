# Improvement Cycle 122

## Topic

Prevent capability novelty from becoming solutionism.

## Deficiency

Cycle 121 finds collisions between new capabilities and old institutions, but
novel technology can make any collision appear important. Without evidence of
someone's burden, Palamedes could originate missions merely to deploy a new
capability.

## Improvement

Added `validate_mismatch_beneficiary_burden` and an experimental schema.

Every mismatch assessment now links the capability to sourced, contextual, and
recurring beneficiary friction, exclusion, delay, or unrealized possibility.
It explains why the capability is relevant, includes a disconfirming condition,
and explicitly rejects capability novelty as a definition of value.

## Scope boundary

Cycle 122 grounds mismatches in burden. Cycle 123 must look beyond incremental
friction lists to anomalies, workarounds, and intended-workflow violations that
may reveal a different problem frame.

## Verification

- focused mission tests: 93 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

A new capability earns mission relevance only by connecting to an observed
beneficiary burden or blocked possibility, never through novelty alone.
