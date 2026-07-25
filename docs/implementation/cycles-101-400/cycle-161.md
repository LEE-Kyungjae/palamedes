# Improvement Cycle 161

## Topic

Separate mission-thesis truth from luck and execution quality.

## Deficiency

An observed success could be treated as direct proof that the selected mission's
causal thesis was true. That collapses mechanism, execution quality, and
exogenous luck into one favorable outcome and makes later learning unreliable.

## Improvement

Added `validate_causal_outcome_attribution` and an experimental schema.

The attribution record binds an observed outcome to a pre-registered,
multi-link causal forecast. Every predicted link needs sourced observation.
Mission thesis, execution quality, and luck remain competing explanations with
evidence for and against each. The outcome and thesis receive separate statuses,
and outcome success is explicitly prohibited from counting as thesis proof.

## Scope boundary

Cycle 161 separates outcome from attribution. Cycle 162 will separately classify
where failure occurred across mission selection, planning, execution,
environment, and measurement.

## Verification

- focused mission tests: 249 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

A successful outcome can support learning only through its pre-registered causal
chain; it cannot by itself prove that the mission thesis was true.
