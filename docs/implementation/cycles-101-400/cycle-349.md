# Improvement Cycle 349

## Topic

Issue downstream authority and reversal triggers with selection.

## Deficiency

A selected winner without bounded execution authority is inert. A winner with
authority but no reversal contract can persist after its evidence fails.
Writing these separately also permits partial, unsafe state.

## Improvement

Added `validate_atomic_selection_authority_reversal_issue` and an experimental
schema.

One atomic issue transaction writes the winner, a downstream authority grant,
and at least one reversal trigger. The grant names grantee, mission contract,
scope, budget, expiry, allowed and forbidden actions, and authority-return
trigger; it cannot redefine the mission or expand itself. Every reversal
trigger names evidence, threshold, measurement, action, rollback authority,
wake event, and review owner without automatic mission rewrite. Partial commit
and execution before the atomic commit are forbidden.

## Scope boundary

Cycle 349 completes an individual selection. Cycle 350 will integrate the
tournament implementation around deterministic eligibility and dominance,
model criticism and selection, and preserved unresolved tradeoffs.

## Verification

- focused mission tests: 1001 passed
- schema JSON parse: 246 schemas parsed
- `git diff --check`: passed

## Resulting invariant

A mission winner becomes executable only together with the exact authority to
act and the evidence conditions that can reverse it.
