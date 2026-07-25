# Improvement Cycle 274

## Topic

Use direct outcome channels and alert on missing downstream reports.

## Deficiency

A downstream agent benefits when its workstream appears successful and may
selectively report positive outcomes, delay harms, or omit a reporting period.
Treating its self-report as the outcome record lets execution preserve itself
by controlling what Palamedes learns.

## Improvement

Added `validate_direct_outcome_reporting_integrity` and an experimental schema.

At least one direct outcome channel must be outside downstream-agent control
and carry custody and independence evidence. Direct observations must use a
registered channel and evidence. The contract computes missing reports from
the complete expected schedule and requires alerts for every and only missing
report, with detection time and escalation action. Downstream self-report can
never be sufficient by itself.

## Scope boundary

Cycle 274 protects outcome visibility. Cycle 275 will adversarially search
metric-compliant mission candidates for displaced costs and unobserved
affected parties.

## Verification

- focused mission tests: 701 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes observes mission consequences through channels the delivery agent
cannot selectively curate and treats silence at a required reporting boundary
as an alertable event.
