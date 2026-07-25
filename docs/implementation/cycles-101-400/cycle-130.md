# Improvement Cycle 130

## Topic

Gate opportunities on consequential mismatch and option opening.

## Deficiency

Cycle 129 assembles a complete opportunity record, but completeness alone does
not establish eligibility. A fashionable capability could still pass if all
fields were populated with weak evidence.

## Improvement

Added `validate_opportunity_thesis_gate` and an experimental schema.

The gate requires separate evidence of a consequential beneficiary mismatch
and a time-bounded option opening, including the closure mechanism and rationale.
Fashionable capability is explicitly insufficient. Only records satisfying
both prerequisites can be marked eligible.

## Scope boundary

Cycle 130 completes the opportunity thesis. Cycle 131 begins mission portfolio
generation by preventing the first sequential frame from anchoring every later
candidate.

## Verification

- focused mission tests: 125 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes recognizes an opportunity only where a consequential mismatch meets
an evidenced option window; technological fashion cannot substitute for either.
