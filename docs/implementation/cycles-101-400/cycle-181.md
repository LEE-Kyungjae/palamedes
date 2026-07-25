# Improvement Cycle 181

## Topic

Begin portfolio review from beneficiary and world change.

## Deficiency

An agent company could maximize task completion and throughput while producing
nothing worth doing. Portfolio review lacked an enforced order that examined
external consequence before delivery performance.

## Improvement

Added `validate_beneficiary_first_portfolio_review` and an experimental schema.

Review order is fixed to beneficiary change, world change, assumption change,
and only then delivery. Every mission includes sourced before-and-now
beneficiary conditions and a sourced environmental change. Task velocity remains
visible but cannot determine the portfolio decision.

## Scope boundary

Cycle 181 changes the starting point of portfolio review. Cycle 182 will place
revenue inside the broader value state as a sustainability constraint and market
signal rather than the sole mission selector.

## Verification

- focused mission tests: 329 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

An agent company's portfolio is judged first by changed beneficiary and world
conditions, never by how quickly its agents completed tasks.
