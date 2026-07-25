# Improvement Cycle 363

## Topic

Replay historical events without future framing leakage.

## Deficiency

A historical replay can accidentally become a hindsight summary: later events
alter earlier wording, the known outcome leaks into packets, or the framing
that eventually succeeded is shown to one condition. Such a replay rewards
recognition of the answer rather than contemporaneous reasoning.

## Improvement

Added `validate_original_order_blinded_historical_replay` and an experimental
schema.

The original archive has a contiguous, fingerprinted event order. Every replay
reveal must cite the event ID and fingerprint at the same sequence position and
exclude future content. Every comparison condition receives the identical
ordered packet fingerprints. The eventual outcome and successful framing are
separately sealed before replay and released only after all final checkpoints.

## Scope boundary

Cycle 363 controls historical replay information. Cycle 364 will include cases
where the correct action is wait, reject, or preserve a minority option so the
benchmark does not reward manufacturing missions.

## Verification

- focused mission tests: 1057 passed
- schema JSON parse: 260 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Historical replay reconstructs what was knowable in the original order and
never exposes the future outcome or winning frame before participants commit.
