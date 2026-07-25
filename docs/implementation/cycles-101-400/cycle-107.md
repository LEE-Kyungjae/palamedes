# Improvement Cycle 107

## Topic

Future, diffuse, and unobserved beneficiaries cannot provide ordinary consent.
Their silence must not become permission.

## Deficiency

Cycle 106 validates consent for known affected parties, but it could not express
that a relevant group was represented only by proxy, remained unrepresented, or
did not yet exist.

## Improvement

Added `validate_representation_gaps`.

Affected groups are classified as `direct`, `proxy`, `unrepresented`, or
`future`. Every non-direct group requires a representation limit and mitigation
plan, and any gap forces `silence_is_consent=false`.

## Scope boundary

Cycle 107 exposes missing representation. Cycle 108 must stop Palamedes from
filling that gap with invented beneficiary preferences.

## Verification

- focused mission tests: 33 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

An absent voice remains an uncertainty and representation obligation, never
implicit consent.
