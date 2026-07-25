# Improvement Cycle 214

## Topic

Evidence and predict every defeasible-principle override.

## Deficiency

A defeasible principle becomes meaningless when any favored mission can call
itself an exception. A reason without evidence or a predicted consequence
cannot later be distinguished from motivated rationalization.

## Improvement

Added `validate_defeasible_principle_override` and an experimental schema.

An override records the default action, proposed exception, reason, evidence,
affected beneficiaries, predicted consequences with and without the exception,
prediction window, and falsification signal. A bounded approval additionally
requires explicit scope, expiry, review ownership, and a declaration that it is
not permanent. Mission preference alone is never sufficient.

## Scope boundary

Cycle 214 governs defeasible-principle exceptions. Cycle 215 will decay learned
preference weight after environment or owner-identity changes without deleting
its lineage.

## Verification

- focused mission tests: 461 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can make a bounded exception to a principle only through accountable
evidence and a consequence prediction that can later be falsified.
