# Improvement Cycle 217

## Topic

Bind authority to consequences, resources, duration, and representation.

## Deficiency

A tool-name allowlist confuses mechanism with authority. The same tool can
produce harmless drafts or irreversible commitments, and a newly substituted
tool can produce the same forbidden consequence.

## Improvement

Added `validate_consequence_bounded_authority_grant` and an experimental schema.

An authority grant now declares allowed and prohibited consequence classes,
positive ceilings for compute, currency, and elapsed time, a validity window,
and explicit representation rights. Each represented group has a mode, consent
basis, binding-commitment flag, and challenge channel. Consequence classes
cannot overlap, and tool names cannot define scope.

## Scope boundary

Cycle 217 defines the grant boundary. Cycle 218 will trace a mission
interpretation through clauses, conflicts, overrides, and uncertainties.

## Verification

- focused mission tests: 473 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes knows authority by what consequences it may create, what resources it
may consume, for how long, and whom it may represent—not by which tool happens
to execute the action.
