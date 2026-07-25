# Improvement Cycle 140

## Topic

Gate selection on independence, common pressure, budgets, and reversibility.

## Deficiency

Cycles 131–139 implement selection safeguards separately, but a caller could
bypass one stage and still present a portfolio decision as Palamedes selection.

## Improvement

Added `validate_selection_thesis_gate` and an experimental schema.

The gate links independent generation, common-context normalization, plural
comparison, finite capacity allocation, and reversible selection records.
Independent formation, common pressure, explicit budget, and reversibility must
all be verified. A single winner cannot erase the portfolio.

## Scope boundary

Cycle 140 completes the selection thesis. Cycle 141 begins autonomy design by
addressing the opposite failure: requiring approval for every mission keeps
Palamedes merely advisory.

## Verification

- focused mission tests: 165 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

A Palamedes portfolio decision is eligible only when diverse formation, fair
comparison, real scarcity, and recoverable choice are all evidenced.
