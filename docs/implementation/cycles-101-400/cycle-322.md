# Improvement Cycle 322

## Topic

Define provider-neutral cognitive roles.

## Deficiency

Binding cognition directly to providers makes architecture depend on vendors,
while allowing one unrestricted model to do everything collapses interpretation,
invention, criticism, selection, and outcome analysis into one authority.

## Improvement

Added `validate_provider_neutral_cognitive_roles` and an experimental schema.

The vertical slice now defines exactly five responsibilities: interpreter,
inventor, adversary, selector, and outcome analyst. Each has fixed input
artifact types, one output type, a completion criterion, validator, and
explicitly forbidden authorities. Role definitions contain no provider or model
binding. Runtime may use one or several providers, but must preserve an
auditable assignment manifest.

## Scope boundary

Cycle 322 separates responsibility from provider topology. It does not claim
that role prompts alone create independence; Cycle 323 pressures that problem.

## Verification

- focused mission tests: 893 passed
- schema JSON parse: 219 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Changing providers cannot silently change Palamedes' cognitive responsibilities,
and sharing a provider cannot merge the authority of distinct roles.
