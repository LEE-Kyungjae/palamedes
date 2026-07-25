# Improvement Cycle 382

## Topic

Resume partial tournaments from frozen candidates.

## Deficiency

Restarting candidate generation after an interruption changes the comparison
frontier. Recomputing completed judgments also destroys auditability and lets
resume timing influence which mission wins.

## Improvement

Added `resume_frozen_candidate_tournament`,
`validate_idempotent_frozen_tournament_resume`, and an experimental schema.

The resume function deep-copies the partial state, preserves the ordered frozen
candidate set and comparison protocol, retains completed judgment evidence,
and adds pending records only for unjudged candidates. It rejects unknown or
duplicate candidates, incomplete completed judgments, and unsupported
versions. Reapplying resume produces the identical state.

## Scope boundary

Cycle 382 defines deterministic partial resume. Cycle 383 will represent a
provider timeout as an unavailable operation while preserving this frontier.

## Verification

- focused mission tests: 1,133 passed
- schema JSON parse: 279 schemas parsed
- `git diff --check`: passed

## Resulting invariant

An interrupted tournament resumes the same comparison; it never creates a new
candidate frontier under the identity of the old one.
