# Improvement Cycle 158

## Topic

Mark claims unverified when independent certification is unavailable.

## Deficiency

Cycle 157 requires independent custody, but such processes may be costly or
temporarily unavailable. Palamedes could respond by relabeling internally
coherent evidence as validation.

## Improvement

Added `validate_independent_verification_status` and an experimental schema.

Without an independent process, a claim must remain `unverified` and state the
verification limit, required process, and wake trigger. It cannot cite completed
custody. `independently_verified` status requires actual custody. Internal
coherence can never count as validation.

## Scope boundary

Cycle 158 preserves epistemic honesty. Cycle 159 must encode an
anti-entrenchment constitutional preference for the smallest system capable of
retiring the targeted cognitive labor.

## Verification

- focused mission tests: 237 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes reports the absence of independent verification as a live limitation,
never as internally certified success.
