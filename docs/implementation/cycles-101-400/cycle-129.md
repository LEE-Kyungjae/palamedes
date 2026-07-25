# Improvement Cycle 129

## Topic

Assemble a complete opportunity record.

## Deficiency

Cycles 121–128 create anomaly, beneficiary, failure, timing, and act-versus-wait
evidence, but those pieces remained independently validatable. A mission could
be proposed without a single record proving that all required lineage exists.

## Improvement

Added `validate_opportunity_record` and an experimental schema.

The record links anomaly, affected and possible conditions, enabling change,
failed predecessors, timing window, and act-wait comparison. It also requires a
reversible cheapest discriminating exposure with at least two outcomes,
rollback, explicit cost and risk, and costlier rejected alternatives.
Fashionable capability cannot define the opportunity.

## Scope boundary

Cycle 129 assembles opportunity evidence. Cycle 130 must integrate the
opportunity thesis as a gate: consequential mismatch plus time-bounded option
opening, never fashionable capability alone.

## Verification

- focused mission tests: 121 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Every Palamedes opportunity is one inspectable evidence chain ending in the
cheapest reversible observation that could distinguish its central hypothesis.
