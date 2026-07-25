# Improvement Cycle 138

## Topic

Require independent mission demand for shared assets.

## Deficiency

Cycle 137 recognizes mutually enabling missions, but “shared infrastructure”
can justify building a broad platform before any mission needs it. Related
candidates may merely repeat one assumption and create fake demand.

## Improvement

Added `validate_shared_asset_demand` and an experimental schema.

A shared asset now requires at least two credible missions with distinct sealed
assumption hashes, separate credibility evidence, a concrete asset need, and a
counterfactual without it. The asset has bounded scope, explicit capacity cost,
and a stop condition. The shared-asset label is never sufficient.

## Scope boundary

Cycle 138 constrains shared assets. Cycle 139 must preserve runner-up missions
and reversal triggers so current selection cannot erase the option landscape.

## Verification

- retrospective focused mission suite: 1,205 passed
- Python compilation: passed
- experimental JSON schema parse: 297 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes funds shared capability only when two independently credible missions
need it for different, inspectable reasons.
