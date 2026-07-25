# Improvement Cycle 391

## Topic

Implement the bounded signal-to-mission vertical slice.

## Deficiency

Separate semantic validators do not prove that Palamedes can carry one linked
case from evidence to a usable mission contract. Extending the slice into
tasks, tools, or external action would also collapse its purpose boundary into
another execution platform.

## Improvement

Added `run_bounded_signal_to_mission_vertical_slice`,
`validate_bounded_signal_to_mission_vertical_slice`, and an experimental
schema.

The function links a fingerprinted signal to an interpretation, a frozen set
of mission candidates, an explicit selection, and a versioned mission
contract. It enforces reference and temporal order and accepts later outcome
observations only when they reference that contract. Execution tasks, tool
calls, implementation steps, and external actions are rejected; the authority
endpoint is the mission contract and outcome intake.

## Scope boundary

Cycle 391 implements the vertical slice. Cycle 392 will map existing Palamedes
revision, fingerprint, restore, provider, reference, and benchmark surfaces
onto it, reserving new code for semantic state and cognition order.

## Verification

- focused mission tests: 1,169 passed
- schema JSON parse: 288 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes can produce and learn against a mission contract without acquiring
the downstream authority to execute it.
