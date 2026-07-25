# Improvement Cycle 306

## Topic

Structure causal sketches while separating normative assumptions.

## Deficiency

A prose causal story can hide unsupported links, ignore opposing evidence, and
present a value judgment as an empirical fact. It cannot clearly state what
future observation would surprise or revise it.

## Improvement

Added `validate_separated_causal_sketch` and an experimental schema.

The sketch contains empirical claim nodes, directed mechanism edges, bounded
confidence, supporting and opposing signals, preregistered predictions, and
surprise conditions. Every empirical claim references separately governed
normative assumptions, each linked to a constitutional clause and the effect of
changing that assumption.

## Scope boundary

Cycle 306 structures the causal interpretation. Cycle 307 will require every
mission candidate to reference beneficiary condition, causal sketch,
constitutional interpretation, resource thesis, harm model, and
disconfirmation.

## Verification

- focused mission tests: 829 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can revise an empirical causal belief without silently changing its
values, and can challenge a value assumption without presenting that challenge
as causal evidence.
