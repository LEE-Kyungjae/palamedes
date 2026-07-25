# Improvement Cycle 372

## Topic

Score six non-substitutable mission-quality dimensions.

## Deficiency

A single mission-quality score allows relevance or originality to hide weak
causal reasoning, constitutional conflict, infeasibility, or absence of a
failure test. That produces attractive missions that cannot be responsibly
selected or learned from.

## Improvement

Added `validate_six_dimension_mission_quality_report` and an experimental
schema.

The report evaluates beneficiary relevance, causal defensibility,
constitutional fit, useful-frame originality, feasibility, and
disconfirmation exactly once. Each dimension has a precommitted zero-to-four
rubric, evidence and fingerprint, uncertainty, required improvement, and
dimension-specific semantic details. Results remain separate; aggregate quality
is empty and a high dimension cannot compensate for a missing one.

## Scope boundary

Cycle 372 defines mission quality. Cycle 373 will measure the upstream human
framing, clarification, approval, correction, and intervention labor retired
before a planner can act.

## Verification

- focused mission tests: 1093 passed
- schema JSON parse: 269 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Mission quality remains a six-dimensional evidence profile whose weaknesses
cannot be averaged away.
