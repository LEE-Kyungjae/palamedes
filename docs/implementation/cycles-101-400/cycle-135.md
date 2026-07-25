# Improvement Cycle 135

## Topic

Preserve probability ranges and downside exposure.

## Deficiency

Cycle 134 supplies early causal accountability, but a vivid high-upside mission
can still dominate attention despite weak probability and asymmetric harm.
Expected-value arithmetic would hide both uncertainty width and who bears the
downside.

## Improvement

Added `validate_probability_downside_profile` and an experimental schema.

Every candidate preserves a non-point probability range, its evidence basis,
unknowns outside the range, and explicit downside exposures with affected
groups, harm, severity, reversibility, mitigation, and source. Expected value,
risk-adjusted scores, and upside-probability products are forbidden.

## Scope boundary

Cycle 135 makes uncertainty and downside inspectable. Cycle 136 must allocate
finite execution capacity across a portfolio without pretending all preserved
missions can be pursued.

## Verification

- focused mission tests: 145 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

High upside cannot erase low confidence or transfer hidden downside to
beneficiaries; both remain visible and non-collapsed.
