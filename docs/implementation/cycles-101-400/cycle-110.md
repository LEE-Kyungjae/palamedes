# Improvement Cycle 110

## Topic

Integrate a revisable, plural, provenance-bearing value constitution.

## Deficiency

Cycle 109 assembles current value inputs, while Cycle 102 validates isolated
revisions. Neither contract proved which constitution version governed a
particular value state or that the governing clauses themselves were plural,
traceable, and explicitly revisable.

## Improvement

Added `validate_value_constitution_binding` and a value constitution schema.

A constitution now has identity, version lineage, revision triggers, and
provenance-bearing clauses. It must contain at least a principle and a
prohibition, cannot contain scalar weights or rewards, and its identity and
version must exactly match the value state. The state declares
`plural_deliberation` as its decision rule.

## Scope boundary

Cycle 110 defines the value substrate for choosing missions. Cycle 111 begins a
new pressure: distinguish a user's stated request from the underlying need.

## Verification

- focused mission tests: 45 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Every mission-selection value state is governed by one identifiable,
revisable, plural constitution whose clauses and provenance can be inspected.
