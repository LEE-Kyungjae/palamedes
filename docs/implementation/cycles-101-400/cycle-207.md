# Improvement Cycle 207

## Topic

Model source-specific error structures without assuming independence.

## Deficiency

Palamedes could treat a human report, telemetry stream, and study as three
independent confirmations merely because their labels differ. They may still
share the same accessible population, upstream records, incentives, or
collection failure.

## Improvement

Added `validate_source_error_structure` and an experimental schema.

Each source declares its class, observation method, error mechanisms,
collection incentive, and known blind spot. Every pair of declared sources
must then receive an explicit independent, correlated, or unknown assessment
covering shared upstream inputs, shared incentives, and rationale. An
independence classification additionally requires evidence.

## Scope boundary

Cycle 207 represents source error and dependence. Cycle 208 will define the
atomic stored signal claim, including affected entity, time, uncertainty,
baseline, and collection incentives.

## Verification

- focused mission tests: 433 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes counts corroboration only after inspecting how sources can fail
together; source-class diversity alone never proves independent evidence.
