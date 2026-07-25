# Improvement Cycle 312

## Topic

Keep `record_signal` free of implicit interpretation and wake side effects.

## Deficiency

If recording an observation also infers meaning or wakes the agent, signal
admission silently becomes a cognitive decision. Callers cannot distinguish
durable evidence capture from attention allocation or purpose change.

## Improvement

Added `validate_record_signal_command` and an experimental schema.

The command calls the observational signal validator and requires an expected
revision fingerprint, authority, revision reason, new revision and object
fingerprints, and provenance preserving source, method, and received time. Its
result must explicitly show that no meaning, wake evaluation, wake event,
mission, constitution change, or other implicit side effect occurred.

## Scope boundary

Cycle 312 records evidence only. Cycle 313 will make `evaluate_wake` a separate
read-and-decide command over the frontier and constitution.

## Verification

- focused mission tests: 853 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

An admitted observation can be persisted and audited without secretly deciding
that it matters, what it means, or which cognitive operation should run.
