# Improvement Cycle 227

## Topic

Separate normative disagreement from empirical uncertainty.

## Deficiency

Competing frames can disagree about values even after all relevant consequences
are known. Treating that conflict as missing evidence postpones an accountable
commitment and lets Palamedes smuggle a value choice in as analysis.

## Improvement

Added `validate_normative_empirical_separation` and an experimental schema.

The record represents at least two frames with their value priority,
unacceptable tradeoff, and represented constituency. Empirical questions name
discriminating evidence and updates. Normative disagreements reference the
frames, state the remaining value choice, deny that more data can resolve it,
and identify the authority and protocol required for commitment.

## Scope boundary

Cycle 227 separates kinds of disagreement. Cycle 228 will require an
interpretation to change either the mission option set or the next probe before
it gains operational relevance.

## Verification

- focused mission tests: 513 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes uses evidence to resolve empirical uncertainty and openly exposes the
value commitments that evidence cannot choose.
