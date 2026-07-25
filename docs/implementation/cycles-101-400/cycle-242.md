# Improvement Cycle 242

## Topic

Separate criticism across seven mission axes.

## Deficiency

A general “strong” or “weak” critique lets one persuasive concern hide failures
elsewhere. Mission weaknesses in causality, representation, governance, or
sustainability require different evidence and corrective responses.

## Improvement

Added `validate_seven_axis_mission_criticism` and an experimental schema.

Each candidate receives exactly one independently owned criticism for causal
thesis, beneficiary representation, constitutional fit, authority, resource
renewal, externalities, and replaceability. Every axis targets a claim, cites
evidence, records a pass, concern, or disqualify verdict, and demands a specific
response. A single aggregated criticism is forbidden.

## Scope boundary

Cycle 242 separates criticism. Cycle 243 will prevent one judge from collapsing
the axes back into a scalar reward and instead use boundaries, dominance, and
explicit unresolved tradeoffs.

## Verification

- focused mission tests: 573 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Palamedes exposes each mission's distinct failure modes without allowing a
single rhetorical judgment to stand in for seven forms of scrutiny.
