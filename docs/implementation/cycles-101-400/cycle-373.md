# Improvement Cycle 373

## Topic

Measure upstream human cognition retired.

## Deficiency

“Less human involvement” can hide shifted work, unlogged corrections, or the
unsafe removal of value-bearing approval. It does not show which cognition
Palamedes actually retired before a planner could act.

## Improvement

Added `validate_upstream_human_cognition_retirement_ledger` and an experimental
schema.

The ledger compares baseline and Palamedes minutes and events for framing,
clarification, approval, correction, and intervention within the exact
pre-planner window. Retired and added minutes are calculated independently, and
all declared totals must match the categories. Approval records carry their
authority boundary and nondelegable minutes; nondelegable authority cannot be
claimed as retired. Post-planner work is excluded rather than mixed into the
upstream claim.

## Scope boundary

Cycle 373 measures upstream cognition retired. Cycle 374 will measure the
planner's reconstruction and clarification burden after handoff.

## Verification

- focused mission tests: 1097 passed
- schema JSON parse: 270 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Upstream labor retirement is a measured five-category pre-planner ledger that
does not pretend nondelegable human value authority disappeared.
