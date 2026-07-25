# Improvement Cycle 269

## Topic

Treat waiting for reality as a cognitive sleep operation.

## Deficiency

Continuous autonomy can be mistaken for continuous internal thought or busy
polling. When only a future external observation can resolve a missing
condition, more inference wastes budget and may hallucinate progress; passive
waiting without monitoring, however, becomes abandonment.

## Improvement

Added `validate_cognitive_sleep_operation` and an experimental schema.

Sleep requires that reality is the only useful information source and that
additional internal reasoning has zero expected information gain. It records
an observation source and channel, wake condition and evidence, latest review
time, safe interim state, and responsible monitor. Harm and authority conflict
can interrupt sleep early. Busy polling and mission abandonment are forbidden,
and waking requires evidence and time.

## Scope boundary

Cycle 269 makes waiting an explicit runtime operation. Cycle 270 will integrate
the runtime thesis: an event-driven uncertainty frontier selecting the least
sufficient operation under bounded cognition.

## Verification

- focused mission tests: 681 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes can deliberately stop thinking until reality can teach it something,
without losing monitoring, safety, ownership, or the exact condition for
resumption.
