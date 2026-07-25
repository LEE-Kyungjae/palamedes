# Improvement Cycle 113

## Topic

Do not infer absence of cost from absence of complaint.

## Deficiency

Cycle 112 contextualizes behavior, but complaints remained an apparently direct
pain signal. Complaint collections systematically overweight people who are
articulate, recently affected, and publicly visible. People who exit, lack
access, or cannot formulate a complaint disappear from the sample.

## Improvement

Added `validate_complaint_silence_evidence` and an experimental schema.

Complaint evidence now records articulation, recency, and visibility biases.
It must name at least one silent or missing group, explain why it is absent, and
define an independent check for its possible cost. Silence can never be encoded
as evidence of no cost.

## Scope boundary

Cycle 113 corrects complaint sampling. Cycle 114 must prevent purchasing power
and revenue from becoming measures of beneficiary or social worth.

## Verification

- focused mission tests: 57 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Complaint volume can reveal pain among observed speakers, but cannot erase the
costs borne by groups who never enter the complaint channel.
