# Improvement Cycle 125

## Topic

Connect repository patterns to beneficiary condition changes.

## Deficiency

Cycle 124 tests human workaround mechanisms across contexts. Palamedes also has
a rich centralized reference collection, but recurring technical patterns in
repositories reveal only what is becoming possible. Popularity or technical
convergence alone does not establish an opportunity.

## Improvement

Added `validate_repository_pattern_opportunity` and an experimental schema.

A repository-derived opportunity now requires at least two uniquely identified,
revision-pinned references, the pattern evidence from each, the enabled
capability, a sourced beneficiary condition, a causal bridge to a possible
condition change, adoption constraints, and a disconfirming condition.
Repository popularity cannot define the opportunity.

## Scope boundary

Cycle 125 connects technical possibility to beneficiary change. Cycle 126 must
use failure archives to reveal missing timing, trust, distribution, or other
conditions that success-only references conceal.

## Verification

- focused mission tests: 105 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Repository collection patterns become opportunity evidence only after Palamedes
connects them causally and falsifiably to a beneficiary condition change.
