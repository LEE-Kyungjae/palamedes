# Improvement Cycle 106

## Topic

Information gain is subordinate to harm constraints and consent.

## Deficiency

Cycle 105 can select a reversible, discriminating probe, but it did not inspect
who is affected or whether learning requires unauthorized exposure. A highly
informative probe could therefore cross the very value boundary it is meant to
clarify.

## Improvement

Added `validate_probe_safety`.

- refused consent always blocks the probe;
- moderate or high risk requires obtained consent;
- unavailable consent permits only minimal-risk, reversible probes without
  external action;
- every probe names affected parties, harm ceiling, mitigation, and stop
  condition.

## Scope boundary

Cycle 106 enforces probe safety. Cycle 107 must represent beneficiaries who
cannot provide consent or are missing from observation instead of treating
silence as permission.

## Verification

- focused mission tests: 29 passed cumulatively
- Python compilation: passed
- `git diff --check`: passed

## Resulting invariant

Expected information gain cannot authorize a probe that exceeds its harm or
consent boundary.
