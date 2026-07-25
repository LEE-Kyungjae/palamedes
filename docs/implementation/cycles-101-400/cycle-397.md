# Improvement Cycle 397

## Topic

Compile into the planner envelope and measure acknowledgment loss.

## Deficiency

A syntactically valid handoff can still change beneficiary, desired outcome,
success or harm signals, causal thesis, exclusions, or authority. If the
planner begins strategy before exposing that reconstruction, semantic loss
becomes implementation drift.

## Improvement

Added `compile_planner_envelope_and_measure_acknowledgment_loss`,
`validate_planner_envelope_acknowledgment_loss`, and an experimental schema.

Seven source dimensions compile into the existing planner goal, beneficiary
context, success and harm metrics, causal constraints, explicit exclusions,
and authority boundary. Tasks and implementation remain empty. The planner's
acknowledged fingerprint for every dimension is compared with its source;
loss count and rate are recomputed, and any mismatch blocks acknowledgment and
requires correction before strategy.

## Scope boundary

Cycle 397 measures planner semantic transport. Cycle 398 will permit live
OpenRouter or other providers only after deterministic replay, treating
provider plurality as an experiment rather than architecture.

## Verification

- focused mission tests: 1,193 passed
- schema JSON parse: 294 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Planner strategy cannot begin until the compiled mission has been acknowledged
without hidden semantic loss.
