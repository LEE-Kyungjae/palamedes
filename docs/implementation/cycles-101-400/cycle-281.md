# Improvement Cycle 281

## Topic

Build the smallest comparison around one evolving signal case.

## Deficiency

Implementing the complete production runtime before testing its central
hypothesis makes failure ambiguous: infrastructure defects, operational scope,
and purpose reasoning become inseparable. A static one-shot example, however,
cannot test whether persistence changes a mission.

## Improvement

Added `validate_single_evolving_signal_comparison_case` and an experimental
schema.

The first comparison contains exactly one signal case with at least two unique,
evidenced, chronological state-changing events. It implements only an event
sequence, condition runner, and output store, while explicitly listing deferred
production infrastructure. The hypothesis, success criterion, and
falsification criterion are frozen, and neither a full nor production runtime
is claimed.

## Scope boundary

Cycle 281 fixes the minimal experiment boundary. Cycle 282 will require the one
case to support at least two plausible beneficiary interpretations and three
competing missions.

## Verification

- focused mission tests: 729 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes tests persistent purpose reasoning on the smallest evolving case that
can reveal revision, before runtime infrastructure obscures the hypothesis.
