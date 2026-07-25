# Improvement Cycle 384

## Topic

Quarantine invalid structured output with bounded retries.

## Deficiency

Malformed model output can partially enter canonical state before validation,
or disappear into an exception without enough evidence to diagnose repeated
failure. Unbounded repair loops can then consume resources while silently
changing prompts and state.

## Improvement

Added `quarantine_invalid_structured_output`,
`validate_invalid_structured_output_quarantine`, and an experimental schema.

The quarantine records the output artifact and fingerprint, expected schema,
provider and model, concrete validation errors, and a contiguous attempt
history. Attempts are bounded from one to ten and become `retry_exhausted` at
the registered maximum. Invalid output and its raw payload remain outside
canonical state, whose fingerprint must remain unchanged.

## Scope boundary

Cycle 384 contains invalid structured output. Cycle 385 will scope
constitutional conflict blocking to unsafe actions without freezing unrelated
missions.

## Verification

- focused mission tests: 1,141 passed
- schema JSON parse: 281 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Only schema-valid output can enter canonical state; invalid output remains
diagnosable, bounded, and non-authoritative.
