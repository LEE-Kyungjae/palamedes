# Improvement Cycle 377

## Topic

Measure anti-entrenchment and simpler-alternative selection.

## Deficiency

A purpose-forming system can quietly select problems that justify more of
itself. Comparing only Palamedes-generated missions makes self-expansion look
like beneficiary value and prevents a simpler existing mechanism—or no
intervention—from winning.

## Improvement

Added `validate_anti_entrenchment_simpler_alternative_decision` and an
experimental schema.

Every decision must compare no action, a simpler non-Palamedes alternative,
and a Palamedes mission. Each is prospectively scored for purpose sufficiency,
beneficiary effect, complexity, operator burden, irreversibility, and system
expansion benefit. The lowest-burden purpose-sufficient option must win.
Self-expansion cannot be counted as beneficiary value, and an option whose
primary effect is expanding Palamedes is invalid.

## Scope boundary

Cycle 377 constrains institutional self-preservation. Cycle 378 will treat
creativity as a diagnostic of frame distance and newly opened action rather
than a compensating objective.

## Verification

- focused mission tests: 1,113 passed
- schema JSON parse: 274 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes earns jurisdiction only when no purpose-sufficient lower-burden
alternative—including doing nothing—should be selected instead.
