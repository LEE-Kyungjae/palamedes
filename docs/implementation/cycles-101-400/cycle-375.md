# Improvement Cycle 375

## Topic

Measure outcome quality across defined horizons.

## Deficiency

An early improvement can hide later side effects, dependence on exceptional
resources, or destroyed options. A single outcome timestamp also encourages
extrapolating short-term delivery into durable beneficiary change.

## Improvement

Added `validate_multi_horizon_outcome_quality_report` and an experimental
schema.

Short, medium, and long horizons have strictly increasing registered days.
Each horizon independently measures intended beneficiary change, side effects,
sustainability, and option preservation against a baseline and boundary.
Reached horizons require observed values and evidence. Unreached horizons remain
pending with a reason and next observation time; early results cannot be
extrapolated. Side effects, sustainability, and options remain separate from
beneficiary change.

## Scope boundary

Cycle 375 defines outcome horizons. Cycle 376 will compare frozen forecast
ranges and failure signals with observations and penalize uncalibrated
confidence.

## Verification

- focused mission tests: 1,105 passed
- schema JSON parse: 272 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Outcome quality is a four-dimensional time series across registered horizons,
not a short-term success label projected into the future.
