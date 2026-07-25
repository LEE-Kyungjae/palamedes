# Improvement Cycle 206

## Topic

Treat expected missing observations as ambiguous signals.

## Deficiency

Cycle 205 exposes what the observation system cannot see, but Palamedes could
still mishandle a report that should have arrived. Ignoring the absence loses a
useful signal; declaring it proof of harm turns missing data into an overclaim.

## Improvement

Added `validate_expected_missing_observation` and an experimental schema.

The contract admits an expected absence only when the expectation has explicit
provenance, channel, deadline, check time, and evidence that the artifact is
missing. It keeps the signal unresolved and requires at least three distinct
explanations, including harm or exclusion and at least one non-harm account.
Every explanation carries evidence for, evidence against, and a discriminator,
followed by a next probe and wake trigger.

## Scope boundary

Cycle 206 governs one expected absence. Cycle 207 will model the distinct error
structures of different evidence-source classes rather than treating source
variety as independence.

## Verification

- focused mission tests: 429 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes neither discards expected silence nor converts it directly into a
harm claim; it preserves competing explanations until a discriminating probe
changes the evidence.
