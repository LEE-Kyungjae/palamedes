# Palamedes Product Overview

<p align="center">
  <strong>English</strong> · <a href="product-overview.ko.md">한국어</a>
</p>

Palamedes is a local-first mission-intelligence layer that works before
`planner -> task -> implementation`. It helps a person or agent decide what is
worth pursuing, why, what evidence could overturn the decision, and when the
decision must be revisited.

## Why it exists

Execution agents can produce code quickly while still optimizing the wrong
goal. Palamedes treats direction as revisionable state rather than disposable
prompt text. It preserves competing interpretations, evidence, hypotheses,
view changes, rejected alternatives, falsifiers, and restore points.

## Planning flow

```text
world signals and references
  -> observations separated from inference
  -> competing interpretations
  -> candidate missions and opportunities
  -> adversarial pressure and falsifiers
  -> bounded mission contract
  -> planner -> tasks -> implementation
  -> attributable outcome signals
```

## Core concepts

- **Mission before task:** establish the worthwhile outcome before expanding work.
- **Competing interpretations:** preserve rival frames until evidence discriminates.
- **Evidence and hypothesis separation:** confidence never turns inference into fact.
- **View transitions:** record what changed, what became visible, and what may now be hidden.
- **Reversible probes:** prefer actions that create learning without silently expanding authority.
- **Outcome lineage:** connect approved missions to later observations without rewriting history.
- **Bounded authority:** Palamedes recommends; hosts and people retain execution and approval authority.

## Product boundary

Palamedes is not a general execution runtime, autonomous deployer, project
manager, or guarantee of originality and commercial success. It can propose
missions, probes, product opportunities, and review gates. It cannot claim that
implementation occurred or grant itself delivery authority.

## State model

The repository-local state includes the current plan, evidence, hypotheses,
development probes, view transitions, decisions, revision history, outcomes,
and restore information. Fingerprints prevent stale writes from silently
overwriting newer state.

Stable and experimental surfaces are identified in [STABILITY.md](../STABILITY.md).
Versioning policy is documented in
[CONTRACT_VERSIONING.md](../CONTRACT_VERSIONING.md).

## Intended users

Palamedes is useful for founders, product teams, researchers, and agent hosts
that need inspectable reasoning before expensive implementation. It is most
valuable when a project has multiple plausible directions, fast execution, or
weak feedback between upstream decisions and downstream outcomes.

## Design principles

1. A worthwhile mission before a larger task list.
2. Observation before interpretation and alternatives before convergence.
3. References with recorded influence, not retrieval theater.
4. Explicit uncertainty, falsifiers, non-goals, and reversal triggers.
5. The smallest mechanism that survives evidence pressure.
6. Recommendation strength never exceeds evidence strength.
7. Better external decisions matter more than more generated text.

See [cognition workflows](cognition-workflows.md) for the available reasoning
paths and [evidence and demos](evidence-and-demos.md) for current proof limits.
