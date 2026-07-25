# Improvement Cycle 124

## Topic

Test workaround mechanisms across contexts and boundaries.

## Deficiency

Cycle 123 can derive a new problem frame from one workaround, but a single
anomaly may be a local convention or personality. Palamedes needed to separate
the recurring mechanism from context-specific form.

## Improvement

Added `validate_cross_context_workaround` and an experimental schema.

The analysis now requires at least two distinct sourced contexts, their shared
mechanism evidence and differences, an explicit strength assessment, boundary
conditions, and the next discriminating context. Universal generalization is
forbidden.

## Scope boundary

Cycle 124 tests the breadth of an anomaly mechanism. Cycle 125 must connect
technical possibility patterns found in repository collections to changing
beneficiary conditions rather than treating repository popularity as an
opportunity.

## Verification

- focused mission tests: 101 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Repeated workarounds strengthen a mechanism only alongside the contextual
differences and boundary conditions that limit where it applies.
