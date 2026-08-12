# Palamedes

<p align="center">
  <strong>English</strong> · <a href="README.ko.md">한국어</a>
</p>

<p align="center">
  <img src="assets/palamedes.png" alt="Palamedes" width="100%">
</p>

> **Palamedes decides what mission is worth planning before execution agents
> decide how to implement it.**

Palamedes is an open-source, local-first Goal Discovery and Goal Synthesis
Engine. It works before `planner -> task -> implementation`: observing what
matters, forming competing interpretations, discovering product and business
opportunities, attacking assumptions, and handing a bounded mission to
downstream agents.

It treats direction as revisionable state rather than disposable prompt text.
Evidence, hypotheses, view changes, rejected alternatives, falsifiers, outcomes,
and restore points remain inspectable in the repository.

```text
world signals and references
  -> competing interpretations
  -> product opportunities and candidate missions
  -> evidence, criticism, and falsification
  -> selected mission contract + non-goals
  -> planner -> tasks -> implementation
  -> outcome signals back to Palamedes
```

## Current Status

**Research Alpha.** The plan-state kernel is implemented and heavily tested.
The autonomous pre-planner remains an active, falsifiable product hypothesis.

| Area | Status |
| --- | --- |
| Revision, restore, fingerprint conflicts, QA | Implemented |
| Mission cognition and bounded handoff | Implemented |
| Opportunity, invention, vision, and pursuit workflows | Experimental |
| Better reviewed missions than a one-shot baseline | Initial blinded model-review evidence |
| Better external outcomes or human-level creativity | Not proven |

Palamedes reports evidence limits rather than converting generated confidence,
retrieval, debate, or novelty into authority. See
[Evidence and Demos](docs/evidence-and-demos.md) for the proof ledger, costs,
failures, and reproduction paths.

## What It Does

- Keeps one revisionable plan with evidence, hypotheses, and restore history.
- Runs independent interpretation, invention, adversarial, and selection roles.
- Finds retention, monetization, content, distribution, platform, and risk opportunities.
- Preserves useful established patterns when product-specific causal fit exists.
- Separates observation, inference, value judgment, commitment, and execution.
- Produces explicit falsifiers, non-goals, reversal triggers, and bounded probes.
- Integrates with execution agents without granting itself delivery authority.
- Records outcomes without silently laundering correlation into causation.

## Why Use It

Use Palamedes when:

- AI can build quickly but the direction keeps drifting.
- several plausible product or research paths compete for attention.
- the obvious feature request may hide a larger business opportunity.
- you need a reviewable reason to select, defer, or reject a direction.
- implementation should create evidence rather than merely complete tasks.

Palamedes is not a general execution runtime, autonomous deployer, or guarantee
of originality and commercial success. People and hosts retain approval,
credentials, side effects, and delivery authority.

## Quick Start

Requirements: Python 3.9+ and Codex CLI, OpenRouter, or an OpenAI API key.

```bash
git clone https://github.com/LEE-Kyungjae/Palamedes.git
cd Palamedes
python3 -m pip install -e .
palamedes init
codex login
palamedes chat --provider codex
```

Inside the chat terminal:

```text
/think What product assumption is most likely to be wrong?
/opportunity Find retention, revenue, distribution, and operating opportunities.
/cycle Choose the smallest reversible mission that tests user value.
/approve
```

For OpenRouter, OpenAI, workspace selection, and plan-state CLI examples, see
[Getting Started](docs/getting-started.md).

## Core Workflows

| Goal | Command |
| --- | --- |
| Explore competing interpretations | `/think <topic>` |
| Discover multi-perspective product opportunities | `/opportunity <context>` |
| Originate and select a bounded mission | `/cycle <context>` |
| Explore structural product inventions | `/invent <context>` |
| Originate a product world | `/vision <context>` |
| Run a lower-cost founder-prompt scout | `/vision-scout <context>` |
| Compose evidence-producing knowledge work | `/pursue <objective>` |
| Observe repository reality | `palamedes observe` |
| Run bounded change-triggered cognition | `palamedes watch --once` |

Each workflow preserves different authority boundaries. Read
[Cognition Workflows](docs/cognition-workflows.md) before integrating automated
approval or execution.

## Architecture

```text
Palamedes plan state
  ├─ evidence and hypotheses
  ├─ competing views and decisions
  ├─ missions, probes, outcomes, and gates
  ├─ revisions, fingerprints, and restore
  └─ CLI / HTTP / Python client / agent adapters

Execution host
  ├─ credentials and process lifecycle
  ├─ implementation and side effects
  └─ observable outcomes returned to Palamedes
```

Stable and experimental surfaces are listed in [STABILITY.md](STABILITY.md).
Contract evolution is documented in
[CONTRACT_VERSIONING.md](CONTRACT_VERSIONING.md).

## Documentation

| Document | Contents |
| --- | --- |
| [Product Overview](docs/product-overview.md) | Purpose, architecture, boundaries, state model, principles |
| [Evidence and Demos](docs/evidence-and-demos.md) | Proof ledger, costs, failures, demos, reproduction |
| [Getting Started](docs/getting-started.md) | Installation, providers, first session, workspaces |
| [Cognition Workflows](docs/cognition-workflows.md) | Cycle, Opportunity, Invention, Vision, Pursuit, Watch |
| [Integrations](docs/integrations.md) | HTTP, Python client, agent hosts, adapters |
| [Operations Reference](docs/operations-reference.md) | CLI groups, concurrency, restore, storage, verification |

Additional references:

- [Pre-planner contract](docs/palamedes-pre-planner-contract.md)
- [AgentScope integration](docs/integration-agentscope.md)
- [Reference agent patterns](docs/reference-agent-patterns.md)
- [Proof program](experiments/PROOF.md)
- [Contributing](CONTRIBUTING.md)

Every overview document has a matching `.ko.md` Korean version with the same
section structure, commands, factual claims, and safety boundaries.

## Development

```bash
make check
```

Individual targets include `make compile`, `make test`, `make scaffold-test`,
`make schema-check`, and `make package-check`.

## License

Palamedes is open-source software licensed under the
[MIT License](LICENSE). You may use, copy, modify, merge, publish, distribute,
sublicense, and sell copies of the software, subject to the license terms. The
copyright notice and permission notice must be included in copies or substantial
portions of the software.

Copyright (c) 2026 LEE Kyungjae.

## Star History

<a href="https://www.star-history.com/?repos=LEE-Kyungjae%2FPalamedes&type=date&legend=top-left">
 <picture>
   <source media="(prefers-color-scheme: dark)" srcset="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&theme=dark&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
   <source media="(prefers-color-scheme: light)" srcset="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
   <img alt="Star History Chart" src="https://api.star-history.com/chart?repos=LEE-Kyungjae/Palamedes&type=date&legend=top-left&sealed_token=U33QpKO_oklxBeuwOfEdD2Gmq-HJhb3IRggfqJjLvFbMCBcmMBC_xBJ1IbS5ewZAaCVBGrfDsfsVMvhp_-pKkFZmOIP10VTsbZZ74hIC2PQNEsZuL0Yko7Te7mGMTzosQ8TKrC0YAjqm4Qktj29JiWxxuVfFoilk-USU7M8FkvUL-3LFgWcL0BH8wTjx" />
 </picture>
</a>
