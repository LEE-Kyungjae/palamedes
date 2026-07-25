# Improvement Cycle 136

## Topic

Allocate finite capacity across a mission portfolio.

## Deficiency

Cycle 135 preserves multiple uncertain missions, but portfolio language can
hide the fact that every “exploration” consumes finite people, time, and
attention. Unbudgeted parallel work becomes implicit commitment to everything.

## Improvement

Added `validate_portfolio_capacity_allocation` and an experimental schema.

A portfolio now states its capacity unit, total, reserve, and allocation window.
Every mission is explicitly committed, explored, or held with a capacity,
scope, and stop condition. Allocations cannot exceed capacity after reserve;
held missions consume none. Hidden parallel commitments are forbidden.

## Scope boundary

Cycle 136 makes capacity scarcity explicit. Cycle 137 must represent sequences
and mutually enabling missions rather than treating all candidates as isolated
competitors.

## Verification

- focused mission tests: 149 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes may preserve many mission options, but only explicitly budgeted work
can execute or explore during a finite allocation window.
