# Improvement Cycle 226

## Topic

Make every world model vulnerable to surprise.

## Deficiency

A model that explains every possible observation cannot lose to an alternative.
It becomes a narrative lens rather than a corrigible account of the world.

## Improvement

Added `validate_world_model_surprise_registry` and an experimental schema.

Every registered model declares an expected observation, a distinct surprising
observation, why it is surprising, how it will be measured, the update applied
if observed, and which other registered model gains support. Each model must
explicitly be able to lose.

## Scope boundary

Cycle 226 makes empirical models defeasible. Cycle 227 will distinguish
empirical disagreement from normative frames that additional data cannot
resolve.

## Verification

- focused mission tests: 509 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes retains only world models that predeclare observations capable of
weakening them relative to a live alternative.
