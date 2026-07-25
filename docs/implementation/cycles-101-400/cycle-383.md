# Improvement Cycle 383

## Topic

Preserve the tournament frontier across provider timeouts.

## Deficiency

A timed-out judgment is missing evidence, not evidence against its candidate.
Treating it as a loss or selecting the remaining available candidate turns
provider reliability and response timing into hidden selection criteria.

## Improvement

Added `record_tournament_provider_timeout`,
`validate_provider_timeout_frontier_preservation`, and an experimental schema.

The timeout record identifies the provider, model, attempt, duration, failure
class, diagnostic artifact, and retry eligibility. It copies the frozen
candidate frontier and both fingerprints unchanged, marks only the operation
as unavailable, and blocks selection. The timed-out candidate is not
disqualified and no remaining candidate can be selected automatically.

## Scope boundary

Cycle 383 handles timeouts. Cycle 384 will quarantine invalid structured model
output outside canonical state with bounded diagnostic retry history.

## Verification

- focused mission tests: 1,137 passed
- schema JSON parse: 280 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Provider availability affects evidence availability, never the semantic merit
or automatic selection status of a frozen candidate.
