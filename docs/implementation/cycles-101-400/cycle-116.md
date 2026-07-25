# Improvement Cycle 116

## Topic

Detect manufactured emotional intensity.

## Deficiency

Cycle 115 includes emotional consequence as one desire signal, but intensity can
be deliberately amplified through novelty, urgency, variable rewards, or other
engagement mechanisms. A system could therefore manufacture the evidence used
to justify its own mission.

## Improvement

Added `validate_emotional_intensity_outcome` and an experimental schema.

The contract separates short-term emotion from long-term relief or capability,
requires an autonomy and compulsion check over an explicit window, and records
the mechanisms that might manufacture intensity plus how each will be
detected. Neither emotional intensity nor engagement may equal benefit.

## Scope boundary

Cycle 116 protects desire inference from manufactured intensity. Cycle 117 must
represent valuable missions that enable desires people could not express before
encountering the possibility.

## Verification

- focused mission tests: 69 passed cumulatively
- `git diff --check`: passed

## Resulting invariant

An emotionally powerful experience counts as beneficial only when independent
evidence shows durable relief, capability, or agency rather than compulsion.
