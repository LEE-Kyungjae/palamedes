# Improvement Cycle 210

## Topic

Integrate the value-relevant signal wake thesis.

## Deficiency

Cycles 201–209 establish separate attention, anomaly, coverage, source, claim,
and wake controls. Without an integration gate, an implementation could satisfy
some controls while silently adding arbitrary wake classes or dropping
observation blind spots from the final policy.

## Improvement

Added `validate_signal_thesis_integration` and an experimental schema.

The integration admits exactly three wake classes: value-relevant deviation,
consequential anomaly, and model failure. Each class must have a concrete case
linking its basis and evidence to a candidate mission change. Unsupported
events cannot wake the system. Observation blind spots remain explicitly
represented but are not treated as self-interpreting evidence.

## Scope boundary

Cycle 210 completes the signal thesis. Cycle 211 will confront the tradeoff
between flexible natural-language principles and brittle formal rules.

## Verification

- focused mission tests: 445 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes wakes through a bounded, mission-relevant signal policy while
retaining explicit knowledge of what its observation system cannot establish.
