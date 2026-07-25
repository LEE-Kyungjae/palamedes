# Improvement Cycle 386

## Topic

Reject stale mission writes with newer-wake evidence.

## Deficiency

A writer can overwrite a mission after a newer wake has changed the feasible
frontier. Returning only a generic conflict forces blind retries and hides the
evidence that made the writer's prior view obsolete.

## Improvement

Added `resolve_mission_write_fingerprint`,
`validate_stale_mission_write_conflict`, and an experimental schema.

Mission writes declare the frontier fingerprint they read. A matching current
fingerprint permits the proposed mission fingerprint to become canonical. A
mismatch returns `stale_write_conflict`, preserves the current canonical
fingerprint, rejects the write, requires rebase, and exposes the newer wake,
trigger, evidence artifact, time, and frontier-change summary.

## Scope boundary

Cycle 386 defines mission-write concurrency. Cycle 387 will ensure restore can
roll back selection state without erasing later outcome observations.

## Verification

- focused mission tests: 1,149 passed
- schema JSON parse: 283 schemas parsed
- `git diff --check`: passed

## Resulting invariant

No mission can overwrite a frontier it did not read, and every stale conflict
explains which newer evidence must be incorporated before retry.
