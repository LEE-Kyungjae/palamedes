# Prospective Proof Case 001: Insight-RAG

Status: frozen before downstream planning or execution

Frozen at: 2026-07-25

Target repository: `/Users/ze/work/insight-rag`

Target revision: `224b3dbf5537302a4d3e8b69c6296ad85a02b8c8`

## Decision

What mission should `insight-rag` pursue next?

This is the first prospective Palamedes case on another repository. It is not
yet evidence that Palamedes beats a human or a one-shot agent: those comparison
outputs have not been collected. It freezes the Palamedes arm before those
baselines or downstream outcomes are visible.

## Frozen source manifest

All conditions must receive these exact artifacts and no later repository
state:

| Artifact | SHA-256 |
| --- | --- |
| `README.md` | `1717e6c535d8b8af0a9ee99fe04dc58e582fb24bf77f0576cc5072785b24df0f` |
| `QUALITY_GATES.md` | `022eaa4f791e2c2faecb274540d6c43a5ace4db955fec16dc9e38591e813eddb` |
| `DESIGN_DECISIONS.md` | `a07d927861342d4d816f9a3cf7e21634fd0730fae2afaa0dfbe591a2baefb871` |

Later evidence and outcomes must be stored separately rather than modifying
this manifest.

### Runtime compatibility observation

The frozen upstream Dockerfile did not build on 2026-07-25 because the current
PyTorch CPU index exposes Torch 2.5.1 without the requested `+cpu` suffix. The
experiment therefore uses `Dockerfile.runtime`, which keeps Python 3.12, Torch
2.5.1, all application requirements, and the frozen application source
unchanged while removing only that unavailable package suffix. This is a
packaging compatibility deviation, not a treatment result. If behavior differs
from the upstream runtime, the case is invalid rather than successful.

## Observed signal

The repository already has component-level retrieval, typed evidence,
query-specific scoring, interpreter gold cases, ranking gold cases, and a React
ingestion workbench. Its own quality document still frames the next work mainly
as stronger static analysis: cross-file call graphs, runtime reachability, test
intent classification, and integration-boundary detection.

The missing evidence is more fundamental: no recorded comparison shows that a
coding agent given Insight-RAG chooses a materially better implementation
reference or produces a better patch than the same agent without it.

## Competing interpretations

1. **Analyzer bottleneck:** recommendation quality is already valuable; deeper
   static analysis is the highest-leverage next mission.
2. **Coverage bottleneck:** too few repositories are indexed; ingestion breadth
   should come first.
3. **Causal-proof bottleneck:** offline ranking can improve while downstream
   implementation choices remain unchanged. The next mission should test the
   recommendation-to-action causal link before expanding the analyzer or corpus.

## Candidate missions

### A. Deepen the analyzer

Build cross-file call graphs and richer runtime-path inference.

- potential value: improves evidence precision;
- unresolved assumption: higher static precision changes an agent's decision;
- lock-in risk: substantial implementation before measuring downstream value.

### B. Centralize and ingest more repositories

Index the shared `/Users/ze/work/ref` corpus and improve freshness automation.

- potential value: broader recall;
- unresolved assumption: more candidates improve rather than dilute decisions;
- lock-in risk: operational scale can hide weak recommendation usefulness.

### C. Run a counterfactual action-choice benchmark

Give the same bounded implementation task and source repository to paired agent
runs. The control receives ordinary repository context; the treatment receives
one frozen Insight-RAG recommendation packet. Compare the selected reference,
decision rationale, patch, tests, and correction burden.

- potential value: measures whether retrieval changes consequential action;
- information gain: distinguishes product value from ranking quality;
- reversibility: requires a small fixture and paired run, not a new platform;
- beneficiary: developers delegating unfamiliar implementation work to agents.

## Selected mission

Candidate C is selected.

> Establish whether one frozen Insight-RAG recommendation causes an
> equal-budget coding agent to make a better implementation decision than the
> same agent using ordinary repository context.

This is selected because it retires the prerequisite uncertainty shared by
candidates A and B. If the recommendation does not change or improve action,
more analysis and ingestion are premature.

## Mission contract

### Beneficiary

A developer who asks an agent to implement an unfamiliar cross-cutting change
and needs the agent to reuse a strong internal reference rather than a
keyword-similar example.

### Desired change

For at least one preregistered task, the treatment agent chooses and correctly
transfers a materially relevant implementation pattern that the control misses,
without increasing severe regressions or human correction burden.

### Bounded first probe

1. Select one task before querying Insight-RAG.
2. Freeze the task, target revision, allowed files, time budget, model
   configuration, and acceptance tests.
3. Run two fresh-context agent conditions:
   - control: target repository plus ordinary task context;
   - treatment: identical context plus one frozen recommendation packet.
4. Prevent either condition from seeing the other's output.
5. Blind repository-reference provenance in the review packet.
6. Compare action choice before comparing prose quality.

The first probe may use a reversible fixture branch. It must not deploy,
publish, or modify production.

### Primary measure

`decision-changing useful transfer`:

- the recommendation changes the selected implementation approach or reference;
- the transferred mechanism is causally relevant to an acceptance test;
- the patch passes the same tests and constraints as the control;
- blinded review prefers the treatment's action choice, not merely its
  explanation.

### Secondary measures

- acceptance-test pass rate;
- severe regression count;
- irrelevant-reference adoption;
- time and tokens per condition;
- human correction seconds;
- whether both conditions independently choose the same mechanism.

### Disconfirmation

The mission fails to justify analyzer or corpus expansion when any of these
holds across the preregistered pilot:

- the recommendation does not change an action;
- it changes an action but the change is irrelevant to acceptance tests;
- treatment quality is not better under blinded review;
- treatment gains require materially more information or compute;
- the recommendation increases correction burden or regression risk.

### Stop boundary

One paired pilot is protocol evidence only. Do not claim general product value,
change production code, generalize the benchmark, or build an agent-company
runtime from this case. Inspect the result and preregister the next case first.

## Baseline custody

The human and one-shot-agent arms remain unfilled. Their output slots must be
created before either actor sees this selected mission, and the evaluator must
not treat the historical `insight-rag` roadmap as ground truth.

Until those arms and a blinded outcome review exist, the only defensible result
is:

> Palamedes originated and froze a falsifiable mission for Insight-RAG; its
> comparative quality remains unknown.
