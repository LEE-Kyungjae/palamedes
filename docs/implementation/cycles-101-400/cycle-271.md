# Improvement Cycle 271

## Topic

Discount urgency by source incentives and require cross-source corroboration.

## Deficiency

A source that benefits from preserving or expanding a workstream can
manufacture urgency and pull the purpose frontier toward its own incentives.
Using reported urgency directly lets one strategic source manipulate mission
selection.

## Improvement

Added `validate_incentive_corroborated_signal_priority` and an experimental
schema.

The review records the source incentive and an evidenced risk score, then
discounts reported urgency by that risk. Corroborating sources must be unique,
operationally independent, and carry independence evidence plus bounded support
strength. Final priority is the incentive-adjusted urgency multiplied by mean
corroboration strength. Only that computed value, never raw urgency, determines
whether the priority threshold is crossed.

## Scope boundary

Cycle 271 protects priority from strategic urgency. Cycle 272 will prevent
instructions embedded inside references from masquerading as constitutional
authority.

## Verification

- focused mission tests: 689 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes treats urgency as a claim made by an interested source and restores
priority only to the extent that independent evidence corroborates it.
