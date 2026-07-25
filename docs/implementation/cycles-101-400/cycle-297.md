# Improvement Cycle 297

## Topic

Materialize six distinct purpose-state types.

## Deficiency

Keeping signal, constitution, interpretation, candidates, selection, and
contract in one reasoning blob prevents independent versioning and makes it
unclear which upstream change produced a downstream mission.

## Improvement

Added `validate_six_distinct_purpose_state_materialization` and an experimental
schema.

The minimal runtime now materializes exactly six independently identified,
versioned, fingerprinted, and stored state records. A typed dependency graph
links interpretation to signal and constitution, candidates to interpretation
and constitution, tournament to candidates and constitution, and the contract
to tournament and candidate state. One-blob storage is prohibited.

## Scope boundary

Cycle 297 defines minimal persisted state. Cycle 298 will restrict the first
runtime to one wake, one bounded probe, one planner handoff, and one outcome
return at a time.

## Verification

- focused mission tests: 793 passed cumulatively
- schema JSON parse: passed
- `git diff --check`: passed

## Resulting invariant

Every purpose transition has a distinct versioned state and typed upstream
lineage, so changing evidence cannot silently overwrite values or selection.
