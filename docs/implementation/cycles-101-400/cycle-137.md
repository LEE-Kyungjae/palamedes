# Improvement Cycle 137

## Topic

Represent mission sequences and mutual enablement.

## Deficiency

Cycle 136 allocates finite capacity, but treating every candidate as an isolated
competitor ignores cases where one mission creates trust, access, knowledge, or
capability needed by another.

## Improvement

Added `validate_mission_enablement_sequence` and an experimental schema.

A portfolio may now encode directed, sourced enablement edges between known
missions. Every edge states the capability or option created and the
counterfactual without the predecessor. Edges must be unique, reference the
portfolio, and form an acyclic sequence.

## Scope boundary

Cycle 137 represents sequence value. Cycle 138 must stop shared-capability
claims from rationalizing empire building by requiring independent demand from
at least two credible missions.

## Verification

- retrospective focused mission suite: 1,205 passed
- Python compilation: passed
- experimental JSON schema parse: 297 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes can value a mission for the options it opens for another without
turning circular dependency claims into justification.
