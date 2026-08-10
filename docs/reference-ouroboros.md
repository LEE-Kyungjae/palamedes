# Ouroboros Reference Review

Reviewed source: `/Users/ze/work/ref/ouroboros` at commit
`5ba0af5c4a1824695fb7848db01171a41624dcba` (2026-08-10).

## Decision

Ouroboros is a useful implementation reference, but not a product template for
Palamedes.

Ouroboros is an execution-oriented Agent OS. Its central loop turns an
interview into an immutable Seed, executes work, evaluates the artifacts, and
feeds the verdict into another generation. Palamedes is a plan-only kernel. It
may propose, challenge, revise, and record a plan, but the host owns delivery
authority. Copying Ouroboros's complete loop would erase that boundary and add
a second orchestrator to hosts that already have one.

The useful material is therefore below the workflow level: small contracts
that keep decisions, evidence, and state transitions honest.

## Adopt

### Separate execution outcome from evaluation verdict

Ouroboros explicitly distinguishes a worker task completing from an acceptance
criterion passing. Palamedes should apply the same distinction whenever a host
reports downstream work:

- `execution_status` says whether the host finished, failed, blocked, or skipped
  the requested work.
- `evaluation_status` says whether recorded evidence satisfies the plan's
  success condition.
- A completed execution must not imply an approved outcome.
- Missing evaluation remains `not_evaluated`, not an inferred pass.

This fits Palamedes because it strengthens evidence custody without granting
execution authority.

Reference:
`docs/guides/execution-vs-evaluation.md` in the Ouroboros checkout.

### Keep large artifacts out of the planning record

Ouroboros's disposable-memory contract returns a small result envelope and
stores the full body behind a content-addressed `artifact_ref`. Palamedes should
use the same shape when hosts return large reports, transcripts, benchmark
packets, or delegated-agent output:

```json
{
  "status": "completed",
  "artifact_ref": "sha256:<digest>",
  "summary": "bounded human-readable result",
  "evidence_ids": ["evidence-..."]
}
```

The ledger should retain the reference, digest, custody, and bounded summary;
the full artifact should remain explicitly fetchable. This reduces context
bloat and prevents model prose from silently becoming plan state.

Reference: `src/ouroboros/core/disposable_memory.py` and
`docs/rfc/disposable-memory.md`.

### Use one typed decision envelope at authority boundaries

Ouroboros validates control directives before persistence and derives terminal
state from the directive instead of trusting a caller-supplied boolean.
Palamedes should preserve this principle at the host boundary:

- decision identity and target are required;
- rationale and producer are explicit;
- idempotency identifies an effective decision, not just a stored row;
- terminality is derived from the canonical decision vocabulary;
- transport delivery is not the source of truth.

Palamedes already has host contracts and idempotent mutations, so this is a
consolidation rule rather than a new subsystem.

Reference: `src/ouroboros/core/control_contract.py` and
`docs/contributing/control-contract.md`.

## Adapt carefully

Ouroboros's immutable Seed is useful as a reminder that intent needs a stable
baseline. Palamedes should not make the whole plan immutable: revision history
and explicit replanning are core capabilities. The compatible interpretation
is to freeze the user-approved objective and constraints per revision, then
create a new linked revision when they change.

Its mechanical → semantic → consensus evaluation pipeline is also useful, but
only as an escalation policy. Cheap deterministic checks should run first;
model judging should run when semantics require it; independent consensus
should be reserved for consequential or uncertain decisions. Requiring three
stages for every planning mutation would add cost without improving custody.

## Do not adopt

- Do not add an execution engine, worker scheduler, provider mesh, or persistent
  autonomous loop to the Palamedes kernel.
- Do not copy the nine-agent persona taxonomy. Roles should exist only when an
  ablation shows that they improve a decision over a simpler prompt.
- Do not use ontology similarity as a universal convergence target. Stable
  wording is not evidence that a product decision is correct.
- Do not reproduce Ouroboros's breadth. The reviewed checkout contains hundreds
  of Python modules and tests across orchestration, providers, TUI, plugins,
  execution, and evaluation. That scale is appropriate to an Agent OS, not to a
  thin plan-state kernel.
- Do not make an immutable specification a substitute for observed outcomes.

## Recommended next slice

The first implementation should be only the execution/evaluation split on the
host outcome boundary. It is small, directly testable, and protects the central
Palamedes claim that recorded completion is not automatically evidence of
success. Artifact envelopes should follow only after real records demonstrate
context-size pressure.

Success means a regression test proves that `execution_status=completed` with
no evaluator evidence remains `evaluation_status=not_evaluated`. Failure means
the new fields merely rename existing statuses or require Palamedes to execute
the work itself.
