# Improvement Cycle 262

## Topic

Wake on six purpose-relevant trigger classes.

## Deficiency

A frontier without a complete trigger vocabulary can sleep through a decisive
change or wake on every irrelevant event. Either failure defeats selective
purpose cognition.

## Improvement

Added `validate_purpose_wake_trigger_registry` and an experimental schema.

The registry covers signal deviation, forecast miss, authority conflict,
mission review, expiring opportunity, and downstream boundary return exactly
once. Each definition states its condition, threshold, and required evidence
kind. A wake event must match a registered definition, use the same type,
reference an active frontier entry, and carry the observed change, evidence,
and time. Unmatched events explicitly do not wake the engine.

## Scope boundary

Cycle 262 defines why purpose cognition wakes. Cycle 263 will select one
cognitive operation from the observed insufficiency rather than rerun a fixed
pipeline.

## Verification

- focused mission tests: 653 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes wakes for each known class of purpose-relevant change and stays
asleep for events that cannot be connected to an active uncertainty or
assumption.
