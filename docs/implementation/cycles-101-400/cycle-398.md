# Improvement Cycle 398

## Topic

Gate live provider experiments on deterministic replay.

## Deficiency

Calling live providers before deterministic replay makes model variance hide
state-machine defects. Requiring multiple providers in the architecture also
turns an empirical comparison question into permanent complexity.

## Improvement

Added `authorize_live_provider_experiment`,
`validate_live_provider_experiment_gate`, and an experimental schema.

Authorization requires identical fixture replay fingerprints, passing
freeze-lineage checks, and zero prior live calls. Every provider arm uses the
same fixture set, context manifest, semantic roles, and evaluation rubric with
a bounded call budget. One provider is valid; multiple providers set an
experimental plurality flag only. Provider outputs retain no selection
authority and cannot bypass validators.

## Scope boundary

Cycle 398 gates live experiments. Cycle 399 will stop implementation after one
end-to-end case and inspect newly visible evidence before generalizing schemas
or building an agent-company runtime.

## Verification

- focused mission tests: 1,197 passed
- schema JSON parse: 295 schemas parsed
- `git diff --check`: passed

## Resulting invariant

Provider plurality is an optional controlled experiment downstream of proven
semantic machinery, never a prerequisite for that machinery.
