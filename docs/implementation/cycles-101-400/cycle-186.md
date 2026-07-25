# Improvement Cycle 186

## Topic

Measure decision latency and contradiction resolution, not message volume.

## Deficiency

Automatic agents can exchange enormous numbers of messages while delaying
decisions and leaving contradictions unresolved. Message volume made
coordination overhead appear productive.

## Improvement

Added `validate_coordination_outcome_metrics` and an experimental schema.

Message count remains observable but cannot represent coordination quality.
The record instead requires sourced decision-latency samples and contradiction
records with resolution status and latency. At least one actual contradiction
resolution must be measurable.

## Scope boundary

Cycle 186 exposes coordination outcomes. Cycle 187 will add expiry and evidence
thresholds to protected minority exploration so it cannot become permanent.

## Verification

- focused mission tests: 349 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Agent coordination is valuable when decisions become timely and contradictions
are resolved—not when agents merely generate more communication.
