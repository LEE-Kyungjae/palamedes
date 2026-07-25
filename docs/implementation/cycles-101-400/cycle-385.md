# Improvement Cycle 385

## Topic

Scope constitutional conflict blocking to affected actions.

## Deficiency

Treating any constitutional conflict as a global stop lets one disputed action
freeze safe probes and unrelated missions. Treating safe exploration like
irreversible action also removes the evidence-generating path needed to resolve
the conflict.

## Improvement

Added `scope_constitution_conflict_actions`,
`validate_scoped_constitution_conflict_blocking`, and an experimental schema.

Conflicts now reference exact action identifiers. Each affected action is
crossed with its registered safe-exploration authority: unsafe affected
actions are blocked, affected safe probes continue within their authority, and
unaffected actions continue unchanged. Every mission remains accounted for and
global freeze is forbidden.

## Scope boundary

Cycle 385 scopes constitutional conflict effects. Cycle 386 will apply
fingerprint conflict semantics to stale mission writes and expose the newer
wake that changed the frontier.

## Verification

- focused mission tests: 1,145 passed
- schema JSON parse: 282 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Constitutional conflict removes authority only from the actions it reaches
beyond safe exploration; it does not suspend the rest of the company.
