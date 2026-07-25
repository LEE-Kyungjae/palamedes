# Improvement Cycle 334

## Topic

Preserve empty retrieval slots as evidence.

## Deficiency

A required retrieval category can incentivize weak references merely to make
every slot appear complete. Dropping an empty slot hides the search boundary
and falsely suggests the evidence landscape was fully populated.

## Improvement

Added `validate_explicit_empty_retrieval_evidence` and an experimental schema.

Every one of the four retrieval slots records query, searched scope, sources,
completion time, and result status. A filled slot requires real result
artifacts. An empty slot requires no results plus a missing-evidence statement,
uncertainty impact, next acquisition trigger, and a context-visible empty
marker. Weak-reference padding, dropped emptiness, and forced completion are
forbidden.

## Scope boundary

Cycle 334 makes absence inspectable. Cycle 335 will govern when personal
preference history may enter context and require disconfirming owner precedents.

## Verification

- focused mission tests: 941 passed
- schema JSON parse: 231 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Palamedes distinguishes “we found supporting context” from “we searched this
bounded space and still lack evidence.”
