# Improvement Cycle 141

## Topic

Define bounded autonomous mission authority.

## Deficiency

Cycle 140 chooses a defensible portfolio, but requiring approval for every next
action leaves Palamedes advisory. Conversely, an unbounded mandate would let it
expand from mission choice into resource, party, or irreversible commitments.

## Improvement

Added `validate_autonomous_authority_delegation` and an experimental schema.

The constitution can now delegate named domains and action kinds for a fixed
period, under explicit resource envelopes, affected-party scope, forbidden
domains, and a reversible or partially reversible ceiling. Overlap and
boundary-crossing conditions require escalation.

## Scope boundary

Cycle 141 defines the four primary authority bounds. Cycle 142 must add
non-numeric consequence classes for reputation, privacy, relationships, and
strategy.

## Verification

- focused mission tests: 169 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

Palamedes may act without case-by-case approval only inside a time-bounded,
resource-bounded, party-bounded, and reversible constitutional delegation.
