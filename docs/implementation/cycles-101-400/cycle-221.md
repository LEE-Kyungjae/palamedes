# Improvement Cycle 221

## Topic

Replace monolithic world narratives with explicit model plurality.

## Deficiency

A signal has no mission implication without assumptions about how the world
works. A single coherent narrative can hide causal uncertainty and make its
preferred mission implication look inevitable.

## Improvement

Added `validate_plural_world_model_set` and an experimental schema.

The model set keeps at least two distinct causal claims around one affected
condition. Every model has supporting and opposing evidence, a distinguishable
prediction, mission implication, bounded uncertainty, and rationale.
Unresolved disagreement and the next discriminating observation remain
explicit; no monolithic model is authoritative.

## Scope boundary

Cycle 221 establishes model plurality. Cycle 222 will keep the competing
representations as bounded causal sketches rather than exhaustive simulations.

## Verification

- focused mission tests: 489 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot turn one plausible explanation into an invisible world model;
competing causal accounts and their divergent mission implications remain live.
