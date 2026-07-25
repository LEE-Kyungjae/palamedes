# Improvement Cycle 340

## Topic

Integrate the role-specific hash-addressed context thesis.

## Deficiency

Individual context safeguards can coexist with a runtime that still sends one
maximal packet to every role. That erases independence, spreads sensitive
material, and hides whether opposition or evidence absence reached a decision.

## Improvement

Added `validate_role_specific_context_thesis` and an experimental schema.

Integration requires verified evidence for all nine context controls from
bounded assembly through summary provenance. Interpreter, inventor, adversary,
selector, and outcome analyst each receive distinct packet and manifest hashes
with a minimized evidence scope. Every packet has a mandatory opposition slot:
it contains qualifying evidence or an explicit missing-evidence marker. Shared
maximal context and one manifest reused by all roles are forbidden.

## Scope boundary

Cycle 340 closes the context-architecture block. Cycle 341 will address the
scaling and false-transitivity problems of pairwise ranking across plural
values.

## Verification

- focused mission tests: 965 passed
- schema JSON parse: 237 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes gives each cognitive role a reproducible evidence packet that includes
opposition or visible absence, rather than maximizing shared context volume.
