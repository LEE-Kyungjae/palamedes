# Improvement Cycle 311

## Topic

Replace generic object creation with type-specific commands.

## Deficiency

A flexible `create_object(type, payload)` endpoint lets callers bypass the
semantic transition they are performing. Authority, validation, revision
reason, and side effects become conventions rather than enforceable contracts.

## Improvement

Added `validate_intent_specific_command_registry` and an experimental schema.

Eight commands separately record signals, amend constitutions, record causal
sketches, propose candidates, conduct tournaments, issue and revise contracts,
and return outcomes. Each fixes its intent, input and output type, unique
semantic validator, authority, revision-reason field, and the only permitted
lifecycle side effects. Generic and unknown creation is rejected, and
validation precedes revision.

## Scope boundary

Cycle 311 defines the command surface. Cycle 312 will constrain `record_signal`
so recording provenance cannot infer meaning or wake the agent as an implicit
write side effect.

## Verification

- focused mission tests: 849 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every purpose-state mutation declares what epistemic transition it intends and
passes the validator and authority specific to that transition.
