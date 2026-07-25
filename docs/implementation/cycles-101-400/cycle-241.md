# Improvement Cycle 241

## Topic

Commit candidate forecasts before tournament reveal.

## Deficiency

A mission tournament can become debate theater when candidates adapt their
claims after seeing rivals. Persuasive flexibility then replaces prediction,
falsifiability, and genuine comparison.

## Improvement

Added `validate_pre_reveal_candidate_commitments` and an experimental schema.

At least two candidates must seal unique commitment records before rival
reveal. Each record includes a measurable forecast, target, window, failure
condition, withdrawal condition, and assumption set while the rival list is
empty. Post-reveal mutation is forbidden; any amendment creates a new version
while preserving the sealed original.

## Scope boundary

Cycle 241 governs pre-competition commitments. Cycle 242 will separate
criticism across seven distinct mission axes.

## Verification

- focused mission tests: 569 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes compares missions against claims they made before strategic knowledge
of their rivals, not arguments optimized during debate.
