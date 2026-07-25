# Improvement Cycle 205

## Topic

Map systematically unobserved beneficiaries and consequences.

## Deficiency

Telemetry, payment, support, and institutional data encode who is visible to the
organization. Palamedes could mistake the resulting dataset for the world and
systematically ignore people who never enter those channels.

## Improvement

Added `validate_observation_coverage_map` and an experimental schema.

The coverage map records beneficiary-consequence pairs as observed, partial, or
unobserved, with sources, visibility reason, collection incentive, and
mitigation. It must expose at least one blind pair and cannot cite an observing
source for an unobserved cell. Silence never counts as coverage, and missing
reports have a wake trigger.

## Scope boundary

Cycle 205 represents observation blind spots. Cycle 206 will treat expected but
missing observations as signals while preserving alternative explanations and
refusing to call absence harm by itself.

## Verification

- focused mission tests: 425 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes knows which beneficiaries and consequences its evidence channels
systematically cannot see instead of treating institutional visibility as
reality.
