# Improvement Cycle 216

## Topic

Bound precedent with analogy, dissent, and invalidation.

## Deficiency

Precedent improves consistency but can turn a historically contingent choice
and its embedded bias into a universal rule. Outcome success alone does not
show that a new case shares the conditions that made the old decision valid.

## Improvement

Added `validate_bounded_precedent_record` and an experimental schema.

A precedent now declares its scope, analogical features, material differences,
recorded dissent, and environmental changes that invalidate it. It is never
universally binding. Applying it requires an analogy rationale, and detection
of a declared invalidating change forces the record out of applicable status.

## Scope boundary

Cycle 216 governs precedent validity. Cycle 217 will define authority grants by
consequences, resources, duration, and representation rights rather than tools.

## Verification

- focused mission tests: 469 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes uses precedent as a contestable analogy whose validity can expire,
not as accumulated authority that silently fossilizes earlier bias.
