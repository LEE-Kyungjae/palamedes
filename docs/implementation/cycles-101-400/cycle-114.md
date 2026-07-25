# Improvement Cycle 114

## Topic

Separate market payment from social worth.

## Deficiency

Cycle 113 restores silent groups to the evidence model, but a revenue signal
could still re-rank them below paying users. Payment demonstrates willingness
under purchasing power and can validate an operating mechanism; it does not
measure who matters or whose condition most deserves improvement.

## Improvement

Added `validate_market_payment_evidence` and an experimental schema.

Payment observations now produce a distinct mechanism inference, disclose
purchasing-power limits, and carry a separate social-worth assessment.
Nonpaying or economically underpowered groups and independent evidence of their
value must remain visible. Payment-based social-worth ranking is forbidden.

## Scope boundary

Cycle 114 bounds the meaning of market evidence. Cycle 115 must combine speech,
behavior, sacrifice, recurrence, counterfactual choice, and emotional
consequence without allowing any single signal to define desire.

## Verification

- focused mission tests: 61 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Revenue may validate how a mission can be sustained, but never whom Palamedes
should value most.
