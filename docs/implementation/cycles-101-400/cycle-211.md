# Improvement Cycle 211

## Topic

Preserve context around formal governance rules.

## Deficiency

Natural-language principles permit convenient reinterpretation, while a formal
condition can discard relevant context and invite literal loopholes. Choosing
only one representation either weakens consistency or produces brittle
governance.

## Improvement

Added `validate_contextual_governance_rule` and an experimental schema.

Each record binds a natural-language principle and rationale to a formal
condition and action, while declaring that neither representation is complete
authority by itself. It includes intended scope, known loopholes, a context
review question, exception test, revision trigger, and concrete applications
whose contextual factors and principle alignment justify apply, decline, or
escalate decisions.

## Scope boundary

Cycle 211 balances rule and context within one governance record. Cycle 212
will introduce distinct constitutional layers and their precedence.

## Verification

- focused mission tests: 449 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes gains formal consistency without pretending that syntax exhausts the
meaning or context of a governance principle.
