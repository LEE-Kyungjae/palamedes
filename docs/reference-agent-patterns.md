# Reference-Derived Agent Architecture

Palamedes's agent runtime should be assembled from locally available, inspectable
reference implementations rather than from a single generic agent framework.

## Adopted patterns

| Concern | Primary reference | Pattern to adopt | Palamedes boundary |
| --- | --- | --- | --- |
| Durable direction memory | Palamedes | Plan, evidence, hypotheses, revisions, restore | Owned by the kernel |
| Wake and work ownership | Paperclip | Heartbeat/wake context, explicit ownership, budgets, idempotent approval | Owned by the host |
| Tool safety | AgentScope | Per-tool permission decisions, sandbox/workspace isolation, event stream | Owned by the host |
| Within-cycle memory | Dexter | Scratchpad, bounded tool loop, context compaction, separate final synthesis | Owned by the cycle runner |
| Specialist behavior | gstack | Role-specific skills, real-environment QA, context save/restore, eval persistence | Skills and evaluation layer |
| Extensibility | OpenClaw | Lean core, plugins for optional capability, explicit channels and safe defaults | Plugins around the host |

Canonical source locations are recorded in
`/Users/ze/work/ref/manifests/status-current.json`; automated keyword-level
coverage is stored in `/Users/ze/work/ref/catalog/agent-patterns.json`.

## Minimum vertical loop

```text
wake
  -> read Palamedes snapshot
  -> AI strategist report
  -> persist grounded reference insights
  -> validate next_actions against capabilities
  -> execute bounded host actions
  -> stop on failure, limit, or human review
  -> return the post-cycle snapshot
```

The implementation is `runtime/agent_cycle.py` in the agent scaffold. It is
deliberately bounded and does not add a queue, scheduler, shell executor, or
manager-of-managers hierarchy to the Palamedes kernel.

## Rejected defaults

- Unbounded autonomous loops
- Silent permission bypass outside a sandbox
- Multiple manager layers before a single-agent loop is proven
- Persisting model prose without source IDs, URLs, or evidence quotes
- Treating structural schema validity as evidence of decision quality
- Copying optional integrations into the core instead of exposing plugin hooks

## Evaluation contract

The initial comparison dataset is
`scaffolds/palamedes_agents/evals/agent-cycle-cases.json`. A valid release claim
requires three real project cases, at least two blinded preferences over a
generic baseline, and at least one attributable stop, pivot, or positioning
decision. Unit tests and schema checks are necessary but do not satisfy this
product-quality gate.
