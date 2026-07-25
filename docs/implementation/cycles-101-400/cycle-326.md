# Improvement Cycle 326

## Topic

Restrict selectors to structured candidates and critiques.

## Deficiency

A selector exposed to raw reasoning or persuasive discussion can choose the
best narrative instead of the best governed mission. A bare decision label also
hides which evidence mattered and which conflict remains unresolved.

## Improvement

Added `validate_structured_selector_decision_packet` and an experimental schema.

The selector receives only constitution, structured candidate fields, and
structured critiques. Every candidate must have critique coverage. The decision
must cite exact candidate or critique fields with value fingerprints and state
their decision effects. At least one unresolved conflict must retain opposing
claims, affected candidates, decision impact, and a resolution trigger.
Raw chain-of-thought, persuasive history, and uncited decisive reasons are
excluded.

## Scope boundary

Cycle 326 makes semantic selection reconstructable. Cycle 327 will assign
mechanical validation, freezing, separation, budgets, provenance, and routing
to deterministic code while retaining semantic judgment in models.

## Verification

- focused mission tests: 909 passed
- schema JSON parse: 223 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A selection can be reconstructed from stable fields and named conflicts without
access to private reasoning traces or persuasive process history.
