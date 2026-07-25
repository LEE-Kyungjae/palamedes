# Improvement Cycle 276

## Topic

Protect the constitution from malicious amendment.

## Deficiency

A constitution that constrains ordinary actions can still be neutralized by an
amendment that grants itself authority, hides the clause diff, invents a
rationale, activates immediately, or cannot be reversed after harmful effects.

## Improvement

Added `validate_constitution_amendment_security` and an experimental schema.

Every amendment links a verified authority grant, independent ratifier,
evidenced rationale, published clause-level before/after diff, and actual text
change. Self-granted authority is forbidden. High-impact amendments cannot
activate immediately, must meet a minimum delay, and require a predecessor
snapshot, rollback trigger, action, authority, and verification test.

## Scope boundary

Cycle 276 secures constitutional change. Cycle 277 will detect attempts to
route around valid prohibitions through individually acceptable steps whose
aggregate consequence is forbidden.

## Verification

- focused mission tests: 709 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes cannot weaken its governing constitution through an invisible,
self-authorized, immediate, or irreversible high-impact amendment.
