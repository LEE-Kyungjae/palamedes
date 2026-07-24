# Palamedes Integration Guide

This guide is for a separate integration repo that wants to use Palamedes as its planning state layer.

Use Palamedes when your runtime needs one place to keep:

- the current plan
- evidence and hypotheses behind that plan
- revision history
- restore points when direction changes

Palamedes should sit under your multi-agent runtime, not replace it.

Recommended role split:

- Palamedes: planning state, QA, revisions, restore, planning context
- host runtime: orchestration, agent routing, execution, scheduling, channels
- research/execution agents: produce updates, evidence, and candidate replans

## System Boundary

Use Palamedes when you need:

- one authoritative planning state
- evidence-backed planning updates
- revision-aware restore
- stale-write protection for agent writes
- planning QA and health gating

Do not use Palamedes for:

- task execution runtime
- queueing or distributed workers
- agent memory unrelated to planning state
- chat/session transport

## Canonical Read Loop

For orchestrators, `get_cycle()` is the default read API.

It returns:

- current plan
- current QA
- current health
- current fingerprint
- recent revision history

Use it as the main control surface before and after mutations.

## Canonical Write Loop

Use this sequence for most agent-driven planning updates:

1. Read `cycle`
2. Apply one mutation
3. Inspect `post_cycle`
4. Decide whether to continue, replan, restore, or stop

Default client helper:

```python
result = client.apply_and_get_cycle(
    "update_plan",
    {
        "goal": "Narrow to creator workflow automation",
        "success_metric": "Reach 5 retained pilots",
        "deadline": "2026-04-30",
    },
    history_limit=5,
    require_healthy=True,
)
```

Inspect:

- `result["changed_fields"]`
- `result["post_cycle"]["qa"]`
- `result["post_cycle"]["health"]`
- `result["post_cycle"]["history"]`

## Conflict Model

Palamedes uses fingerprint-based stale-write protection:

- current plan state is identified by `fingerprint`
- stale writes fail with `412`
- Python client surfaces that as `PalamedesConflictError`

This is a coordination signal, not a transport failure.

Useful fields on `PalamedesConflictError`:

- `expected_fingerprint`
- `current_fingerprint`
- `operation`
- `step`
- `can_refresh`

## Retry Model

Use `apply_and_get_cycle_with_retry()` when one refresh-and-retry is acceptable:

```python
result = client.apply_and_get_cycle_with_retry(
    "update_plan",
    {"goal": "Focus on paid pilot conversion"},
    expected_fingerprint=stale_fingerprint,
)
```

Default retry policy is conservative:

- retries are enabled by default for `update_plan`
- retries are also enabled for `restore_revision`
- append-like operations such as `add_evidence` and `replan` require `allow_non_idempotent_retry=True`

This avoids duplicate append-style writes unless your integration explicitly opts in.

## Health-Gated Writes

If your host runtime should stop writes during degraded storage conditions, use `require_healthy=True`:

```python
result = client.apply_and_get_cycle(
    "update_plan",
    {"goal": "Ship planning API alpha"},
    require_healthy=True,
)
```

If storage health is not `ok`, the client raises `PalamedesHealthGateError`.

Recommended host behavior:

- block autonomous writes
- surface health state to operator
- allow only read/diagnostic flows until health recovers

## Restore Flow

Recommended rollback sequence:

1. preview target
2. inspect diff and metadata
3. restore through the generalized write flow

```python
preview = client.preview_restore(previous=True)
restored = client.apply_and_get_cycle(
    "restore_revision",
    {"previous": True},
    require_healthy=True,
)
```

Use restore as a normal planning write, not as an out-of-band emergency tool.

## Minimal Adapter Pattern

The host repo should wrap `PalamedesClient`, not call the HTTP API directly.

Suggested responsibilities for a host-side adapter:

- fetch planning snapshots
- apply one planning mutation
- attach host metadata around the call
- branch on conflict vs health-gate vs operation failure
- convert Palamedes results into the host runtime's event model

This repo includes a minimal adapter skeleton in:

- `examples/palamedes_kernel_adapter.py`

## Example Host Loop

Typical host-side decision flow:

1. Planner agent proposes a plan change
2. Host adapter applies `update_plan`
3. Host inspects `qa.score`, `health.status`, and `changed_fields`
4. If quality improves, continue
5. If quality degrades or risk grows, add evidence or trigger restore preview

## Recommended First Integration

For a separate AgentScope-style repo:

1. run Palamedes HTTP locally
2. wrap `PalamedesClient` in a thin adapter
3. give the planner agent only the adapter surface
4. use `get_cycle()` as the pre/post step context
5. keep execution/runtime memory outside Palamedes

The goal is simple:

- Palamedes decides what the current plan is
- your runtime decides what to execute next

## Relevant Client Methods

- `get_cycle`
- `get_plan`
- `update_plan`
- `replan`
- `add_evidence`
- `apply_and_get_cycle`
- `apply_and_get_cycle_with_retry`
- `preview_restore`
- `restore_revision`
- `capture_evidence_cycle`

For multi-step append flows such as `capture_evidence_cycle()`, pass one host-level
`idempotency_key` and let the client derive stable step keys for `add_evidence`
and `replan`.

Preferred import surface for host repos:

```python
from palamedes_sdk import PalamedesClient
```

For local development against this repo:

```bash
python3 -m pip install -e /path/to/palamedes
```

## Non-Goals

This guide does not cover:

- direct CLI-only workflows
- full slash-command usage
- execution agent design
- deployment/runtime operations for the host repo
