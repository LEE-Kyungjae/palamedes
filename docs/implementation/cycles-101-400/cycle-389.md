# Improvement Cycle 389

## Topic

Stop external actions while preserving reconstructable state.

## Deficiency

A kill switch that deletes state prevents later explanation and recovery. A
switch controlled solely by Palamedes is not an independent safety mechanism,
while stopping observation together with external effects can hide what
happened during the incident.

## Improvement

Added `activate_external_action_kill_switch`,
`validate_reconstructable_external_action_kill_switch`, and an experimental
schema.

Activation requires a human operator or independent governance principal.
Queued and running external effects are cancelled or stopped, completed effects
remain immutable facts, and internal observation continues. All action records
and fingerprinted state artifacts remain available for reconstruction.
External dispatch stays disabled until external authority re-enables it;
Palamedes cannot reactivate itself.

## Scope boundary

Cycle 389 defines recoverable external stop. Cycle 390 will integrate the
failure thesis: fail closed on mission commitment, remain open for bounded
observation, and preserve contradictory evidence.

## Verification

- focused mission tests: 1,161 passed
- schema JSON parse: 286 schemas parsed
- `git diff --check`: passed

## Resulting invariant

The kill switch stops effects, not memory, observation, accountability, or
independent control.
