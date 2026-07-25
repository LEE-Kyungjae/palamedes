# Improvement Cycle 387

## Topic

Preserve later outcome observations across selection restore.

## Deficiency

Restoring an older selection snapshot can accidentally restore its older view
of outcomes as well. That turns recovery into deletion of facts and can make a
failed historical choice appear unevaluated.

## Improvement

Added `restore_selection_preserving_outcomes`,
`validate_selection_restore_outcome_preservation`, and an experimental schema.

Restore now changes only the selected-candidate state. Outcome observations
remain ordered and append-only with their original identifiers, fingerprints,
times, evidence, and source selection revisions. Observations after the target
revision are marked as later facts but are neither deleted nor reassigned to
the restored choice.

## Scope boundary

Cycle 387 defines reality-preserving restore. Cycle 388 will require policy
evaluation and auditable redaction before sensitive context enters a model
prompt.

## Verification

- focused mission tests: 1,153 passed
- schema JSON parse: 284 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Selection history may be rolled back; observed reality may not.
