# Improvement Cycle 160

## Topic

Gate persistence on adversarial expansion review and replaceability.

## Deficiency

Cycles 151–159 constrain self-benefit and prefer simpler systems separately,
but Palamedes persistence or expansion still lacked a single decision gate.

## Improvement

Added `validate_anti_preservation_gate` and an experimental schema.

The gate links self-conflict, temporal lineage, minimal counterfactual,
verification status, and anti-entrenchment clause. Expansion must be tested as
an adversarial hypothesis with evidence for and against it. Simpler replacement
must be tested and retirement executable. If a simpler system is adequate,
replacement is mandatory; continued existence is never the default.

## Scope boundary

Cycle 160 completes the anti-preservation thesis. Cycle 161 begins causal
outcome evaluation by separating mission-thesis truth from luck and execution
quality.

## Verification

- focused mission tests: 245 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes survives or expands only after adversarial review, and must yield to a
successful simpler mechanism.
