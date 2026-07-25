# Improvement Cycle 307

## Topic

Link every mission candidate to its complete decision basis.

## Deficiency

A polished mission sentence can conceal an unspecified beneficiary change, weak
causal theory, convenient constitutional reading, absent resource renewal,
unmodeled harm, or no condition that would defeat it.

## Improvement

Added `validate_complete_mission_candidate_basis` and an experimental schema.

Each candidate contains a beneficiary's current and desired external condition,
causal-sketch reference, clause-addressable constitutional interpretation,
resource source and renewal failure, affected-population harm records with
detection and mitigation, and a timed evidence-based disconfirmation decision.
The candidate cannot authorize itself.

## Scope boundary

Cycle 307 makes individual candidates inspectable. Cycle 308 will preserve the
full tournament comparison and unresolved assumptions rather than storing only
the winner.

## Verification

- focused mission tests: 833 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

No mission enters selection without exposing who should experience what change,
why it may work, why it is allowed, how it persists, whom it may harm, and what
would defeat it.
