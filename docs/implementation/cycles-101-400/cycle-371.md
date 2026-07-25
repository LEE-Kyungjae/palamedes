# Improvement Cycle 371

## Topic

Normalize proof results by compute and human correction.

## Deficiency

Win rate can make a system look better because it saw more information, used
many more calls, waited longer, or received hidden human correction. Without
resource reporting, architectural quality and purchased effort are
indistinguishable.

## Improvement

Added `validate_quality_resource_budget_report` and an experimental schema.

Human, one-shot-agent, and Palamedes conditions each link a blinded quality
artifact to four measured budgets: visible information, compute, latency, and
human labor. Every numeric component has units, a measurement record, and a
method. Shared visible-information fingerprints are explicit. Compute-token and
human-minute totals must equal their components, including operator
intervention, developer correction, and evaluation time. Missing resources
cannot be treated as zero, and win rate cannot be reported alone.

## Scope boundary

Cycle 371 makes resource use visible beside quality. Cycle 372 will define the
six distinct mission-quality dimensions that the quality artifact must report.

## Verification

- focused mission tests: 1089 passed
- schema JSON parse: 268 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Every quality comparison exposes the information, compute, latency, and human
labor that produced it, including hidden correction work.
