# Improvement Cycle 208

## Topic

Store signals as contextualized claims rather than raw events.

## Deficiency

An event record does not state what is being claimed, whom it affects, which
baseline makes it unusual, or how collection incentives and uncertainty shape
its meaning. Treating the event and claim as equivalent erases those
epistemically important boundaries.

## Improvement

Added `validate_contextualized_signal_claim` and an experimental schema.

A stored signal now names its source structure, observation method, affected
entity, observation and recording times, expected baseline, observed deviation,
bounded uncertainty and rationale, possible collection incentive, evidence,
claim status, and next update trigger. Inferred claims require explicit
inference bases, while observed claims cannot silently carry them.

## Scope boundary

Cycle 208 defines the atomic signal claim. Cycle 209 will decide whether new
cognition could change a mission before waking the inquiry process.

## Verification

- focused mission tests: 437 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes stores an accountable interpretation of an observation, never an
unqualified raw event presented as self-explanatory evidence.
