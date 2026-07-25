# Improvement Cycle 139

## Topic

Preserve runner-up missions and reversal triggers.

## Deficiency

Cycle 138 prevents speculative shared infrastructure, but selecting one primary
mission can still delete the evidence, context, and readiness of serious
alternatives. A winner then becomes path-dependent even after its thesis fails.

## Improvement

Added `validate_reversible_portfolio_selection` and an experimental schema.

Selection now preserves each runner-up's evidence hash, reason, wake trigger,
and preservation action. At least one precommitted reversal trigger names a
signal, threshold, target runner-up, and action. The selected scope and review
window remain bounded; erasing the option landscape is forbidden.

## Scope boundary

Cycle 139 makes selection reversible. Cycle 140 must integrate independent
formation, common-pressure comparison, explicit budgets, and reversibility into
one selection-thesis gate.

## Verification

- focused mission tests: 161 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Choosing a primary mission does not erase credible alternatives, and failure
signals can trigger a defined switch without regenerating the portfolio.
