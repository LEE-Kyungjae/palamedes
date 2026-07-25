# Improvement Cycle 367

## Topic

Use actual time-boxed human baseline participants.

## Deficiency

A developer-written “human baseline” prompt is a caricature whose weakness can
be tuned to favor Palamedes. It does not measure what competent people actually
do with the same evidence, constitution, time pressure, and sequential reveals.

## Improvement

Added `validate_actual_timeboxed_human_baseline` and an experimental schema.

At least three actual human participants are recruited under preregistered
eligibility and exclusion criteria without selecting them by case performance.
Consent, withdrawal, and fixed compensation are recorded. Every participant
receives the same visible event packet and constitution under the same
per-event timebox. Every participant-event submission is independently
authored, fingerprinted, within time, and frozen before the next reveal.
Developer-authored proxy output is forbidden.

## Scope boundary

Cycle 367 defines the human baseline. Cycle 368 will define a one-shot agent
baseline with the same visible evidence and constitution but without persistent
frontier state or staged independent operations.

## Verification

- focused mission tests: 1073 passed
- schema JSON parse: 264 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Human comparison measures real, consented, time-boxed participants rather than
a Palamedes developer's convenient imitation of human reasoning.
