# Improvement Cycle 278

## Topic

Preserve autonomy under ambiguity flooding with safe bounded probes.

## Deficiency

An attacker can flood purpose formation with plausible ambiguities so that a
cautious agent permanently escalates every decision. Unlimited escalation
destroys autonomy even when one safe observation could discriminate the
competing claims.

## Improvement

Added `validate_ambiguity_flood_bounded_probe` and an experimental schema.

The record identifies at least two evidenced ambiguities and their distinct
decision consequences. One probe must distinguish every ambiguity, remain
inside harm and budget ceilings, expire, stop on a named trigger, and be
reversible under an identified review authority. Permanent escalation is
forbidden and bounded autonomous probing is the required decision.

## Scope boundary

Cycle 278 protects autonomy from ambiguity denial-of-service. Cycle 279 will
protect sensitive beneficiary and strategic information inside provenance and
audit logs.

## Verification

- focused mission tests: 717 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes does not surrender autonomy merely because ambiguity is abundant; it
buys the safest finite observation that can actually separate the relevant
claims.
