# Improvement Cycle 327

## Topic

Split deterministic controls from model semantic judgment.

## Deficiency

Letting a model both judge meaning and govern its own context, budget,
provenance, routing, and state transitions makes safeguards advisory. Replacing
semantic judgment with deterministic scoring would erase the capability
Palamedes is intended to provide.

## Improvement

Added `validate_deterministic_semantic_ownership_boundary` and an experimental
schema.

Deterministic code exclusively owns schema validation, artifact freezing,
context separation, budget enforcement, provenance recording, and call routing.
Models exclusively own causal interpretation, mission invention, adversarial
critique, selection judgment, and outcome-attribution hypotheses. Every
responsibility has input/output contracts and a failure mode. Model outputs are
structured and validated before state change; models cannot alter control state,
while code cannot invent or score semantic purpose.

## Scope boundary

Cycle 327 defines ownership. Cycle 328 will ensure model failure does not cause
deterministic code to substitute rule-based purpose scoring.

## Verification

- focused mission tests: 913 passed
- schema JSON parse: 224 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The component that proposes meaning cannot relax the controls governing its
proposal, and the component enforcing controls cannot silently replace semantic
judgment.
